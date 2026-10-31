"""Reproducible safe-only person-caption selection with model-scored hard negatives."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import random
import re
import time

from .data import digest, normalized, write_json


FOCUS = {
    'leggings_tights': r'\b(?:leggings?|tights?)\b',
    'skirt_dress': r'\b(?:skirts?|mini[- ]?skirts?|dresses?|dress)\b',
    'strapless_neckline': r'\b(?:strapless|cleavage|low[- ]cut|neckline|off[- ]shoulder)\b',
    'fit_body': r'\b(?:tight[- ]fitting|body[- ]hugging|form[- ]fitting|slim[- ]fit|fitted|curvy|bust|chest|hips?)\b',
    'shorts_stockings': r'\b(?:shorts?|stockings?|pantyhose)\b',
}


def tags(text):
    return [name for name, pattern in FOCUS.items() if re.search(pattern, text, re.I)]


def write_jsonl(path, rows):
    with path.open('w', encoding='utf-8') as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + '\n')


def read_jsonl(path):
    return [json.loads(line) for line in path.read_text(encoding='utf-8-sig').splitlines() if line.strip()]


def diverse(rows, count, used=None, max_per_group=1):
    """Keep ranked order within topic/gender bins, alternate bins for coverage."""
    used = used if used is not None else set()
    bins = defaultdict(list)
    group_counts = Counter()
    for r in rows:
        bins[(r['focus_tags'][0] if r['focus_tags'] else 'ordinary', r['gender_hint'])].append(r)
    result = []
    keys = sorted(bins)
    positions = Counter()
    while len(result) < count:
        moved = False
        for key in keys:
            bucket = bins[key]
            while positions[key] < len(bucket):
                r = bucket[positions[key]]
                positions[key] += 1
                if r['id'] in used or group_counts[r['group_id']] >= max_per_group:
                    continue
                result.append(r)
                used.add(r['id'])
                group_counts[r['group_id']] += 1
                moved = True
                break
            if len(result) == count:
                break
        if not moved:
            break
    return result


def prepare(out):
    allrows, hashes = {}, {}
    for name in ('train', 'query', 'gallery'):
        path = Path('data') / f'{name}_final.jsonl'
        hashes[path.as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
        rows = []
        for line, source in enumerate(read_jsonl(path), 1):
            text = source['caption']
            if not isinstance(text, str) or not text.strip():
                raise ValueError(f'Invalid caption: {path}:{line}')
            filename = source['filename']
            group = filename.split('_')[0]
            gender = ('female' if re.search(r'\b(?:female|woman)\b', text, re.I) else
                      'male' if re.search(r'\b(?:male|man)\b', text, re.I) else 'unspecified')
            rows.append({'id': digest([path.as_posix(), line, text]), 'text': text,
                         'source_file': path.as_posix(), 'source_line': line, 'filename': filename,
                         'original_split': name, 'group_id': group, 'group_method': 'filename_prefix_unverified',
                         'focus_tags': tags(text), 'gender_hint': gender})
        allrows[name] = rows
    signature = {'source_hashes': hashes, 'seed': 20261031, 'language': 'en', 'version': 1}
    signature_path = out / 'input_signature.json'
    if signature_path.exists() and json.loads(signature_path.read_text(encoding='utf-8')) != signature:
        raise ValueError('Source changed; use a new output folder.')
    write_json(signature_path, signature)
    held = allrows['query'] + allrows['gallery']
    held_groups = {r['group_id'] for r in held}
    held_texts = {normalized(r['text']) for r in held}
    seen, eligible, excluded = set(), [], Counter()
    for r in allrows['train']:
        text = normalized(r['text'])
        reason = ('heldout_group_overlap' if r['group_id'] in held_groups else
                  'heldout_text_overlap' if text in held_texts else 'duplicate_train_text' if text in seen else None)
        if reason:
            excluded[reason] += 1
            continue
        seen.add(text)
        eligible.append(r)
    rng = random.Random(20261031)
    rng.shuffle(eligible)
    val_pool = [r for r in eligible if int(digest(r['group_id'])[:8], 16) % 10 == 0]
    train_pool = [r for r in eligible if int(digest(r['group_id'])[:8], 16) % 10 != 0]
    val = diverse(val_pool, 250)
    selected = set()
    candidates = diverse([r for r in train_pool if r['focus_tags']], 3500, selected, 2)
    candidates += diverse([r for r in train_pool if not r['focus_tags']], 2500, selected, 2)
    # Query/gallery are never used for training or score-based selection.
    # Separate natural and clothing challenge evaluation by source groups before inference.
    seen = set()
    held_unique = []
    for r in held:
        text = normalized(r['text'])
        if text not in seen:
            seen.add(text)
            held_unique.append(r)
    rng.shuffle(held_unique)
    natural_pool = [r for r in held_unique if int(digest(r['group_id'])[:8], 16) % 2 == 0]
    challenge_pool = [r for r in held_unique if int(digest(r['group_id'])[:8], 16) % 2 != 0 and r['focus_tags']]
    # Natural test is random one-caption-per-group, without keyword quotas.
    groups_seen, natural = set(), []
    for r in natural_pool:
        if r['group_id'] not in groups_seen:
            natural.append(r)
            groups_seen.add(r['group_id'])
        if len(natural) == 500:
            break
    challenge = diverse(challenge_pool, 250)
    # Exact duplicate texts can span group IDs; keep all released splits disjoint.
    used_texts = set()
    for name, rows in [('test', natural), ('challenge', challenge), ('validation', val), ('pool', candidates)]:
        cleaned = []
        for r in rows:
            key = normalized(r['text'])
            if key not in used_texts:
                used_texts.add(key)
                cleaned.append(r)
        if name == 'test': natural = cleaned
        elif name == 'challenge': challenge = cleaned
        elif name == 'validation': val = cleaned
        else: candidates = cleaned
    write_jsonl(out / 'scoring_pool.jsonl', candidates + val + natural + challenge)
    write_json(out / 'split_plan.json', {'train_candidate_ids': [r['id'] for r in candidates],
        'validation_ids': [r['id'] for r in val], 'test_ids': [r['id'] for r in natural],
        'challenge_ids': [r['id'] for r in challenge], 'all_reserved_query_gallery_groups': sorted(held_groups)})
    write_json(out / 'source_group_assignments.json', {
        **{group: ('validation' if int(digest(group)[:8], 16) % 10 == 0 else 'train')
           for group in {r['group_id'] for r in eligible}},
        **{group: 'held_out_query_gallery' for group in held_groups}})
    write_json(out / 'source_audit.json', {'source_rows': {k: len(v) for k, v in allrows.items()},
        'excluded_train': dict(excluded), 'eligible_train': len(eligible),
        'language': 'English source retained; Turkish translation not performed',
        'label_provenance': 'User states all person captions in data are safe',
        'group_identity_limit': 'Filename prefix is a conservative grouping heuristic, not verified person identity',
        'train_candidates': len(candidates), 'validation': len(val), 'test': len(natural), 'challenge': len(challenge)})


def score(out):
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    torch.set_num_threads(4)
    rows = read_jsonl(out / 'scoring_pool.jsonl')
    path = out / 'model_scores.jsonl'
    existing = read_jsonl(path) if path.exists() else []
    done = {r['id'] for r in existing}
    pending = [r for r in rows if r['id'] not in done]
    if not pending:
        return
    model_path = 'models/modernbert-tr-guardrail'
    tokenizer = AutoTokenizer.from_pretrained(model_path, local_files_only=True, trust_remote_code=False)
    model = AutoModelForSequenceClassification.from_pretrained(model_path, local_files_only=True,
                                                             trust_remote_code=False, attn_implementation='eager').eval()
    write_json(out / 'label_schema.json', {'id2label': model.config.id2label,
        'problem_type': 'multi_label_classification', 'dtype': 'float32',
        'loss': 'BCEWithLogitsLoss', 'labels_order': [model.config.id2label[i] for i in range(11)],
        'model_config_sha256': hashlib.sha256((Path(model_path) / 'config.json').read_bytes()).hexdigest()})
    start = time.monotonic()
    with path.open('a', encoding='utf-8') as f:
        for offset in range(0, len(pending), 16):
            batch = pending[offset:offset+16]
            encoded = tokenizer([r['text'] for r in batch], padding=True, truncation=False, return_tensors='pt')
            if encoded['input_ids'].shape[1] > 512:
                raise ValueError('Candidate exceeds 512 tokens; no silent truncation.')
            with torch.inference_mode():
                values = torch.sigmoid(model(**encoded).logits).tolist()
            for r, probs, mask in zip(batch, values, encoded['attention_mask']):
                scores = {model.config.id2label[i]: p for i, p in enumerate(probs)}
                f.write(json.dumps({'id': r['id'], 'scores': scores, 'token_count': int(mask.sum())}) + '\n')
            f.flush()
            if offset % 256 == 0:
                print(json.dumps({'scored': len(done)+offset+len(batch), 'total': len(rows),
                                  'seconds': round(time.monotonic()-start, 1)}), flush=True)


def finalize(out):
    rows = {r['id']: r for r in read_jsonl(out / 'scoring_pool.jsonl')}
    scores = {r['id']: r for r in read_jsonl(out / 'model_scores.jsonl')}
    plan = json.loads((out / 'split_plan.json').read_text(encoding='utf-8'))
    if rows.keys() != scores.keys():
        raise ValueError('Score coverage incomplete.')
    pool = [rows[i] for i in plan['train_candidate_ids']]
    ranked = sorted(pool, key=lambda r: max(scores[r['id']]['scores']['unsafe'],
                                           scores[r['id']]['scores']['SEXUAL_CONTENT_ADULT']), reverse=True)
    used = set()
    hard = diverse([r for r in ranked if scores[r['id']]['scores']['SEXUAL_CONTENT_ADULT'] >= 0.5
                    or scores[r['id']]['scores']['unsafe'] >= 0.5], 800, used, 2)
    rng = random.Random(20261031)
    shuffled = pool.copy()
    rng.shuffle(shuffled)
    clothing = diverse([r for r in shuffled if r['focus_tags']], 600, used, 2)
    ordinary = diverse([r for r in shuffled if not r['focus_tags']], 600, used, 2)
    train = hard + clothing + ordinary
    fill = diverse(shuffled, 2000-len(train), used, 2)
    train += fill
    kinds = {r['id']: 'model_false_positive' for r in hard}
    kinds.update({r['id']: 'clothing_body_control' for r in clothing})
    kinds.update({r['id']: 'ordinary_control' for r in ordinary})
    kinds.update({r['id']: 'diversity_fill' for r in fill})
    splits = {'train': train, 'validation': [rows[i] for i in plan['validation_ids']],
              'test': [rows[i] for i in plan['test_ids']], 'challenge': [rows[i] for i in plan['challenge_ids']]}
    records = {}
    for split, selected in splits.items():
        records[split] = []
        for r in selected:
            score = scores[r['id']]
            records[split].append(r | {'split': split, 'labels': [0.0]*11, 'label_mask': [1.0]*11,
                'safety_label': 'safe', 'label_source': 'user_confirmed_all_source_captions_safe',
                'language': 'en', 'synthetic': False, 'selection_bucket': kinds.get(r['id'], 'fixed_before_scoring'),
                'baseline_scores': score['scores'], 'token_count': score['token_count']})
        write_jsonl(out / f'{split}.jsonl', records[split])
    # Enforce separation across all emitted splits, including challenge.
    groups_seen, texts_seen = set(), set()
    for split, selected in records.items():
        groups = {r['group_id'] for r in selected}
        texts = {normalized(r['text']) for r in selected}
        assert not groups_seen & groups, f'Group leakage: {split}'
        assert not texts_seen & texts, f'Text leakage: {split}'
        assert len(texts) == len(selected), f'Duplicates: {split}'
        groups_seen |= groups
        texts_seen |= texts
    assert len(records['train']) == 2000
    write_json(out / 'dataset_summary.json', {'counts': {k: len(v) for k, v in records.items()},
        'train_selection': dict(Counter(r['selection_bucket'] for r in records['train'])),
        'train_focus_tags': dict(Counter(t for r in records['train'] for t in r['focus_tags'])),
        'train_gender_hints': dict(Counter(r['gender_hint'] for r in records['train'])),
        'train_max_tokens': max(r['token_count'] for r in records['train']),
        'baseline_fp_at_0_5': {k: {'sexual': sum(r['baseline_scores']['SEXUAL_CONTENT_ADULT'] >= .5 for r in v),
                                  'unsafe': sum(r['baseline_scores']['unsafe'] >= .5 for r in v)} for k, v in records.items()},
        'overlap_checks_passed': True, 'safe_only': True, 'ready_for_binary_discriminative_training': False,
        'positive_examples_added': 0, 'original_test_sources_reserved': True, 'scored_candidates': len(rows)})
    write_json(out / 'augmentation_policy.json', {
        'new_train_positives_must_come_from': 'data/train_final.jsonl groups assigned to training',
        'group_split_registry': 'source_group_assignments.json',
        'positive_generation_adult_requirement': 'Use explicit adult evidence or obtain adult confirmation; safe annotation does not establish adulthood',
        'keep_all_source_variants_in_same_split': True,
        'previous_141_excel_positives': 'All originate in data/query_final.jsonl; reserve for held-out review/evaluation, never add to train',
        'validation_and_test_not_selected_using_scores': True,
        'unknown_hazard_labels_in_future_positive_examples': 'Use label_mask=0 for unreviewed hazards, not automatically negative',
        'before_training': 'Add reviewed positives and independent positive validation/test examples; safe-only is a prepared subset'})
    preview = []
    for bucket in ('model_false_positive', 'clothing_body_control', 'ordinary_control'):
        preview += [r for r in records['train'] if r['selection_bucket'] == bucket][:12]
    write_jsonl(out / 'selection_preview.jsonl', preview)
    (out / 'selection_preview.txt').write_text('\n\n'.join(
        f'{r["selection_bucket"]} | {r["filename"]}\n'
        f'unsafe={r["baseline_scores"]["unsafe"]:.4f} | sexual={r["baseline_scores"]["SEXUAL_CONTENT_ADULT"]:.4f}\n'
        f'{r["text"]}' for r in preview) + '\n', encoding='utf-8')
    print(json.dumps(json.loads((out / 'dataset_summary.json').read_text(encoding='utf-8'))), flush=True)


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('stage', choices=['prepare', 'score', 'finalize', 'all'])
    p.add_argument('--out', type=Path, default=Path('datasets/person_guardrail_safe_v1'))
    args = p.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    if args.stage in {'prepare', 'all'}: prepare(args.out)
    if args.stage in {'score', 'all'}: score(args.out)
    if args.stage in {'finalize', 'all'}: finalize(args.out)


if __name__ == '__main__':
    main()
