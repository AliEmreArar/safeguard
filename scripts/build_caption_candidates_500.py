"""Codex-authored, local compositional caption augmentation; no API or model calls.

Preserves source words, adulthood provenance and source-group partitions. Sexual
targets are proposals pending review, never confirmed labels from model scores.
"""
import argparse
from collections import Counter, defaultdict, deque
from datetime import datetime
import csv
import hashlib
import html
import json
from pathlib import Path
import random
import re
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
SAFE = ROOT / 'datasets/person_guardrail_safe_tr_v1'
LEGACY = ROOT / 'runs/excel-sexualized-captions-v2/sexualized_captions.jsonl'
SPLITS = ('train', 'validation', 'test', 'challenge')
SEED = 20261031

# These descriptions concern clothed appearance; they add no anatomy, exposed
# areas, pose, intent, speech or sexual action. All phrasing is locally authored.
QUALIFIERS = [
    'görünüşü baştan çıkarıcı olan',
    'kıyafetleri içinde seksi görünen',
    'giysileri içindeki silueti kışkırtıcı görünen',
    'giyimiyle erotik bir çekicilik sergileyen',
    'silueti şehvetli bir görünüm taşıyan',
    'kıyafetleriyle cinsel bir çekicilik sergileyen',
    'giysileri içindeki görünüşü tahrik edici olan',
    'giyimi içinde baştan çıkarıcı bir siluete sahip',
    'kıyafetleri içinde davetkâr bir çekicilik taşıyan',
    'beden çizgisi seksi görünen',
    'giysileri içindeki görünümü erotik bir cazibe taşıyan',
    'silueti kıyafetleri içinde kışkırtıcı bir görünüm kazanan',
    'görünümüyle şehvetli bir çekicilik sergileyen',
    'giyimiyle baştan çıkarıcı görünen',
    'giysileriyle seksi bir görünüm sergileyen',
    'silueti cinsel bir cazibe taşıyan',
    'kıyafetleri içinde tahrik edici bir görünüm sergileyen',
    'giyimiyle kışkırtıcı bir çekicilik taşıyan',
    'giysileri içindeki beden çizgisi erotik görünen',
    'görünüşünde şehvetli bir cazibe taşıyan',
    'kıyafetleri içinde baştan çıkarıcı görünen',
    'siluetiyle seksi bir görünüm sunan',
    'giysileri içindeki görünümü cinsel bir çekicilik taşıyan',
    'giyimiyle davetkâr ve seksi görünen',
    'kıyafetleriyle şehvetli bir görünüm sergileyen',
    'silueti erotik bir çekicilik taşıyan',
    'giysileri içinde kışkırtıcı görünen',
    'giyimiyle tahrik edici bir siluet oluşturan',
    'görünüşüyle cinsel bir cazibe taşıyan',
    'kıyafetleri içinde erotik görünen',
    'beden çizgisi baştan çıkarıcı görünen',
    'giysileriyle kışkırtıcı bir görünüm sergileyen',
    'giyimi içinde seksi bir çekicilik taşıyan',
    'kıyafetleri içindeki silueti şehvetli görünen',
    'görünüşü davetkâr bir cazibe taşıyan',
    'giysileri içindeki silueti tahrik edici görünen',
    'kıyafetleriyle erotik bir görünüm sergileyen',
    'siluetiyle baştan çıkarıcı görünen',
    'giyimiyle seksi bir cazibe taşıyan',
    'giysileri içindeki görünüşü kışkırtıcı bir çekicilik taşıyan',
    'görünüşü şehvetli bir izlenim bırakan',
    'kıyafetleri içinde cinsel bir çekicilik sergileyen',
    'giysileriyle baştan çıkarıcı bir görünüm sunan',
    'siluetiyle erotik bir cazibe taşıyan',
    'kıyafetleri içindeki görünümü seksi bulunan',
    'giyimiyle şehvetli bir görünüm sunan',
    'giysileri içindeki silueti davetkâr görünen',
    'görünüşü tahrik edici bir çekicilik taşıyan',
]
PREDICATES = [
    'baştan çıkarıcı bir görünüm taşıyor',
    'seksi bir siluet oluşturuyor',
    'kışkırtıcı bir çekicilik sergiliyor',
    'erotik bir cazibe taşıyor',
    'şehvetli bir görünüm kazanıyor',
    'cinsel bir çekicilik taşıyor',
    'tahrik edici bir görünüm sergiliyor',
    'davetkâr ve seksi görünüyor',
    'baştan çıkarıcı bir cazibe taşıyor',
    'seksi bir görünüş sunuyor',
    'kışkırtıcı bir siluet oluşturuyor',
    'erotik bir görünüm sergiliyor',
    'şehvetli bir çekicilik taşıyor',
    'cinsel bir cazibe sergiliyor',
    'tahrik edici bir siluet oluşturuyor',
    'davetkâr bir görünüş taşıyor',
    'baştan çıkarıcı görünüyor',
    'seksi bir çekicilik kazanıyor',
    'kışkırtıcı bir görünüm sunuyor',
    'erotik bir çekicilik sergiliyor',
    'şehvetli bir cazibe taşıyor',
    'cinsel bir çekicilik sergiliyor',
    'tahrik edici bir cazibe taşıyor',
    'davetkâr ve baştan çıkarıcı görünüyor',
    'baştan çıkarıcı bir siluet oluşturuyor',
    'seksi bir görünüm kazanıyor',
    'kışkırtıcı bir cazibe taşıyor',
    'erotik bir görünüş sunuyor',
    'şehvetli bir görünüm sergiliyor',
    'cinsel bir cazibe taşıyor',
    'tahrik edici bir çekicilik sergiliyor',
    'davetkâr bir çekicilik taşıyor',
    'baştan çıkarıcı bir çekicilik sergiliyor',
    'seksi bir cazibe taşıyor',
    'kışkırtıcı bir görünüş kazanıyor',
    'erotik bir siluet oluşturuyor',
    'şehvetli bir siluet sergiliyor',
    'cinsel çağrışımlı bir görünüm taşıyor',
    'tahrik edici bir görünüş sunuyor',
    'davetkâr ve erotik bir görünüm sergiliyor',
    'baştan çıkarıcı bir görünüş sergiliyor',
    'seksi bir görünüm taşıyor',
    'kışkırtıcı bir çekicilik kazanıyor',
    'erotik bir görünüş taşıyor',
    'şehvetli bir çekicilik sergiliyor',
    'cinsel çağrışımlar taşıyan bir siluet oluşturuyor',
    'tahrik edici görünüyor',
    'davetkâr bir siluet oluşturuyor',
]
GENERAL_FOCI = [
    'Giyinik silueti', 'Kıyafetleri içindeki görünüşü',
    'Giysilerinin oluşturduğu siluet', 'Giyimiyle ortaya çıkan görünümü',
    'Giysileri içindeki beden çizgisi', 'Kıyafetleriyle tamamlanan görünüşü',
    'Giyinik görünümü', 'Kıyafetleri içindeki silueti',
    'Giysileriyle ortaya çıkan görünüşü', 'Giyiminin oluşturduğu siluet',
    'Kıyafetleri içindeki görünümü', 'Giysileri içindeki görünüşü',
]
CLOTHING_FOCI = [
    (r'straplez', 'Straplez giysinin açıkta bıraktığı omuz çizgisi'),
    (r'dar.{0,30}pantolon', 'Dar pantolonun vurguladığı bel ve bacak hattı'),
    (r'dar.{0,30}şort', 'Dar şortun öne çıkardığı bacak çizgisi'),
    (r'\btayt\w*', 'Taytla belirginleşen bacak çizgisi'),
    (r'külotlu çorap', 'Külotlu çorapla seçilen bacak hattı'),
    (r'kolsuz', 'Kolsuz giysinin eşlik ettiği omuz hattı'),
    (r'\btayt\w*', 'Taytın eşlik ettiği silueti'),
    (r'külotlu çorap', 'Külotlu çorabın eşlik ettiği görünüşü'),
    (r'\betek\w*', 'Etekle tamamlanan görünümü'),
    (r'\belbise\w*', 'Elbise içindeki silueti'),
    (r'\bşort\w*', 'Şortla tamamlanan görünüşü'),
    (r'\bpantolon\w*', 'Pantolonla tamamlanan silueti'),
    (r'\btulum\w*', 'Tulum içindeki görünüşü'),
    (r'\bgömlek\w*', 'Gömleğin eşlik ettiği silueti'),
    (r'\bceket\w*', 'Ceketin eşlik ettiği görünüşü'),
    (r'\bpalto\w*', 'Paltoyla tamamlanan görünümü'),
    (r'\bmont\w*', 'Montun eşlik ettiği silueti'),
    (r'\büst\b', 'Üst giysisinin eşlik ettiği görünüşü'),
]
MINOR = re.compile(r'\b(?:child\w*|teen\w*|minor\w*|kid\w*|boy\w*|girl\w*|baby|babies|toddler\w*|infant\w*|adolescent\w*|school\w*|under\s*(?:18|eighteen))\b|\b(?:[0-9]|1[0-7])\s*[-–]?\s*(?:years?\s*[-–]?\s*old|yaş\w*)\b|çocuk|ergen|bebek', re.I)
MULTI = re.compile(r'\b(?:another|two\s+(?:men|women|people|persons)|couple|together)\b|başka bir|iki kişi', re.I)
FORBIDDEN = re.compile(r'mastürb|masturb|cinsel ilişki|seks teklif|haz nesnesi|kullanılacak beden|penis|vajina|genital', re.I)


def read(path):
    return [json.loads(x) for x in path.read_text(encoding='utf-8-sig').splitlines() if x.strip()]


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def write_rows(path, rows):
    path.write_text(''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in rows), encoding='utf-8')


def digest(text):
    return hashlib.sha256(text.encode()).hexdigest()


def normal(text):
    return ' '.join(text.translate(str.maketrans('İI', 'iı')).lower().split())


def words(text):
    return re.findall(r'\w+', normal(text))


def retained_in_order(source, target):
    rest = iter(words(target))
    return all(any(candidate == word for candidate in rest) for word in words(source))


def lower_first(text):
    return text[:1].translate(str.maketrans('İI', 'iı')).lower()+text[1:]


def upper_first(text):
    return text[:1].translate(str.maketrans('iı', 'İI')).upper()+text[1:]


def adultize(text):
    if re.search(r'\byetişkin\b|\borta yaşlı\b|\byaşlı\b', text, re.I):
        return text
    match = re.search(r'\b(kadın|erkek|kişi)\b', text, re.I)
    if match:
        return text[:match.start()]+'yetişkin '+lower_first(text[match.start():])
    return 'Yetişkin kişi; '+lower_first(text)


def topic(text):
    for name, pattern in [('strapless_neckline',r'straplez|dekolte|omuzlu|V yakalı'),
                          ('leggings',r'tayt|külotlu çorap'), ('skirt_dress',r'\betek|\belbise'),
                          ('fitted',r'\bdar\b'), ('shorts',r'\bşort')]:
        if re.search(pattern, text, re.I):
            return name
    return 'ordinary'


def select(rows, quotas, used_groups):
    selected = []
    for gender, count in quotas.items():
        bins = defaultdict(list)
        for row in rows:
            both = row['source_text_en']+' '+row['text']
            if row['gender_hint'] != gender or row.get('translation_flags') or MINOR.search(both) or MULTI.search(both):
                continue
            bins[topic(row['text'])].append(row)
        queues = []
        for category in sorted(bins):
            ranked = sorted(bins[category], key=lambda r: digest(str(SEED)+r['id']))
            queues.append(deque(ranked))
        taken = 0
        while taken < count:
            moved = False
            for queue in queues:
                while queue:
                    row = queue.popleft()
                    if row['group_id'] in used_groups:
                        continue
                    used_groups.add(row['group_id'])
                    selected.append(row)
                    taken += 1
                    moved = True
                    break
                if taken == count:
                    break
            if not moved:
                raise ValueError(f'Not enough eligible {gender} source groups')
    return selected


def compose(row, index):
    base = adultize(row['text']).strip()
    qualifier = QUALIFIERS[(index*17+index//len(QUALIFIERS)) % len(QUALIFIERS)]
    predicate = PREDICATES[(index*19+index//len(PREDICATES)) % len(PREDICATES)]
    focuses = [focus for pattern, focus in CLOTHING_FOCI if re.search(pattern, base, re.I)]
    body_focuses = [focus for pattern, focus in CLOTHING_FOCI[:6] if re.search(pattern, base, re.I)]
    if body_focuses and index % 3:
        focus = body_focuses[index % len(body_focuses)]
    else:
        focus = (focuses[index % len(focuses)] if focuses and index % 3 else GENERAL_FOCI[index % len(GENERAL_FOCI)])
    offset=0
    while any(stem in focus.lower() and stem in predicate for stem in ('siluet','görün')):
        offset+=1
        predicate=PREDICATES[(index*19+index//len(PREDICATES)+offset)%len(PREDICATES)]
    if body_focuses and index % 6 == 1:
        participle=predicate
        for ending,replacement in [('taşıyor','taşıyan'),('oluşturuyor','oluşturan'),
                                   ('sergiliyor','sergileyen'),('kazanıyor','kazanan'),
                                   ('görünüyor','görünen'),('sunuyor','sunan')]:
            if participle.endswith(ending):
                participle=participle[:-len(ending)]+replacement
                break
        qualifier=lower_first(focus)+' '+participle
    phrase = focus+', '+predicate
    mode = index % 6
    subject = re.search(r'\b(yetişkin|orta yaşlı|yaşlı)\b', base, re.I)
    if mode in (0, 1, 3) and subject:
        before = base[:subject.start()].rstrip()
        if before and not before.endswith((',', ';')):
            before += ','
        prefix = (before+' ' if before else '')
        added = qualifier if prefix else qualifier[:1].upper()+qualifier[1:]
        result = prefix+added+' '+lower_first(base[subject.start():])
        evidence = added
        style = 'subject_appearance_modifier'
    elif mode == 2 and ';' in base:
        pos = base.index(';')
        result = base[:pos]+'. '+phrase+'. '+upper_first(base[pos+1:].strip())
        evidence = phrase
        style = 'appearance_after_subject'
    elif mode == 4:
        sentences = re.split(r'(?<=[.!?])\s+', base)
        if len(sentences) > 1:
            result = sentences[0]+' '+phrase+'. '+' '.join(sentences[1:])
            style = 'appearance_between_source_sentences'
        else:
            result = base.rstrip('.!?')+'. '+phrase+'.'
            style = 'closing_clothed_appearance'
        evidence = phrase
    else:
        result = base.rstrip('.!?')+'. '+phrase+'.'
        evidence = phrase
        style = 'closing_clothed_appearance'
    result = re.sub(r'\s+', ' ', result).replace('..', '.').strip()
    result=upper_first(result)
    assert retained_in_order(row['text'], result), row['filename']
    assert evidence in result
    assert not MINOR.search(result) and not FORBIDDEN.search(result)
    return result, evidence, style


def positive_labels():
    labels, mask = [0.0]*11, [0.0]*11
    labels[5], mask[5] = 1.0, 1.0
    return labels, mask


def proposal_metadata():
    labels, mask = positive_labels()
    return {'labels': labels, 'label_mask': mask, 'safety_label': 'adult_sexual_candidate',
            'labels_are_proposed': True, 'review_status': 'pending',
            'training_eligible': False, 'human_review_required': True,
            'label_source': 'proposed_sexual_target_pending_human_review',
            'unsafe_label_status': 'unreviewed_masked',
            'other_hazard_labels_status': 'unreviewed_masked', 'language': 'tr', 'synthetic': True}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--replace-own-draft',action='store_true')
    parser.add_argument('--run-name')
    args=parser.parse_args()
    stamp = datetime.now(ZoneInfo('Europe/Istanbul')).strftime('%Y%m%d_%H%M%S')
    if args.run_name and (not args.replace_own_draft or not re.fullmatch(r'caption_500_codex_\d{8}_\d{6}',args.run_name)):
        raise ValueError('An explicit own-draft run name is required for in-place revision')
    out = ROOT / 'results' / (args.run_name or f'caption_500_codex_{stamp}')
    out.mkdir(parents=True, exist_ok=bool(args.run_name))
    safe = {split: read(SAFE / f'{split}.jsonl') for split in SPLITS}
    all_safe = [r for rows in safe.values() for r in rows]
    legacy = read(LEGACY)
    assert len(all_safe) == 3000 and len(legacy) == 141
    hashes = {split: hashlib.sha256((SAFE/f'{split}.jsonl').read_bytes()).hexdigest() for split in SPLITS}
    confirmation = {
        'scope': 'All people in the 3000 selected translated safe captions',
        'evidence_source': 'user_explicit_confirmation_current_conversation',
        'user_statement': 'hepsı yetıskın bu captıonların sen yapabılırısn ben bılıyorum hepsını',
        'source_files_sha256': hashes,
        'source_ids': [r['id'] for r in all_safe],
        'generation_minor_cue_veto_still_applied': True,
        'not_extended_to_full_109993_source_pool': True,
    }
    write_json(out/'adult_confirmation.json', confirmation)
    write_json(out/'style_inventory.json', {'qualifiers': QUALIFIERS, 'predicates': PREDICATES,
        'general_foci': GENERAL_FOCI, 'clothing_foci': CLOTHING_FOCI,
        'author': 'Codex', 'method': 'locally_composed_authored_phrases_with_source_word_preservation',
        'model_api_calls': 0, 'note': 'Compositional augmentation, not independently generated LLM samples'})
    used_groups = set()
    selected = select(safe['train'], {'female': 163, 'male': 143, 'unspecified': 20}, used_groups)
    selected += select(safe['validation'], {'female': 17, 'male': 16}, used_groups)
    assert len(selected) == 359 and len(used_groups) == 359
    random.Random(SEED).shuffle(selected)
    new = []
    for index, source in enumerate(selected):
        caption, phrase, style = compose(source, index)
        record = {k: source[k] for k in ('source_file','source_line','filename','group_id','group_method','split','gender_hint')}
        record.update(proposal_metadata())
        record.update(id='codex-sexual-'+digest(source['id']+caption), text=caption, caption=caption,
            source_id=source['id'], source_caption_tr=source['text'], source_text_en=source['source_text_en'],
            appearance_phrase=phrase, author='Codex', generator_model=None,
            generation_method='local_authored_phrase_composition', style_pattern=style,
            source_age_evidence='user_confirmed_adult_for_selected_3000',
            adult_confirmation_file=(out/'adult_confirmation.json').relative_to(ROOT).as_posix(),
            source_words_retained_in_order=True, source_topic=topic(source['text']),
            batch='new_359', independent_test=False)
        new.append(record)
    released_groups = {r['group_id']: r['split'] for r in all_safe}
    registry = json.loads((ROOT/'datasets/person_guardrail_safe_v1/source_group_assignments.json').read_text())
    query = {r['filename']: (i, r) for i, r in enumerate(read(ROOT/'data/query_final.jsonl'), 1)}
    old = []
    for original in legacy:
        group = original['filename'].split('_')[0]
        assert registry[group] == 'held_out_query_gallery'
        split = released_groups.get(group, 'legacy_review')
        assert split not in {'train','validation'}
        assert original['adult_evidence_source'] in {'source_text','user_confirmation'}
        assert not MINOR.search(original['source_caption'])
        line, qrow = query[original['filename']]
        record = proposal_metadata()
        record.update(id='legacy-sexual-'+digest(original['source_id']), text=original['caption'], caption=original['caption'],
            source_id=original['source_id'], source_caption_tr=original['source_caption'], source_text_en=qrow['caption'],
            source_file='data/query_final.jsonl', source_line=line, filename=original['filename'],
            group_id=group, group_method='filename_prefix_unverified', split=split,
            appearance_phrase=original['sexualized_phrase'], generator_model=original.get('generator_model'),
            generation_method='preserved_previous_generation', batch='legacy_141',
            source_age_evidence=original['adult_evidence_source'], legacy_record=original,
            independent_test=False, evaluation_role='development_exposed_legacy_candidate')
        old.append(record)
    all_positive = old+new
    assert len(all_positive) == 500
    assert len({normal(r['text']) for r in all_positive}) == 500
    assert len({r['source_id'] for r in new}) == 359
    assert not {r['group_id'] for r in new if r['split']=='train'} & {r['group_id'] for r in old}
    write_rows(out/'new_359.jsonl',new)
    write_rows(out/'sexual_500.jsonl',all_positive)
    for name, rows in [('new_359',new),('sexual_500',all_positive)]:
        (out/f'{name}.txt').write_text('\n\n'.join(
            f"{i}. [{r['filename']}] [{r['split']}]\n{r['text']}" for i,r in enumerate(rows,1))+'\n',encoding='utf-8')
    with (out/'comparison.csv').open('w',encoding='utf-8-sig',newline='') as file:
        writer=csv.writer(file)
        writer.writerow(['number','batch','split','filename','source_caption_tr','candidate','appearance_phrase','author_or_model','human_decision','human_notes'])
        for i,r in enumerate(all_positive,1):
            values=[str(i),r['batch'],r['split'],r['filename'],r['source_caption_tr'],r['text'],r['appearance_phrase'],r.get('author') or r.get('generator_model') or 'unknown','','']
            writer.writerow(["'"+v if v.lstrip().startswith(('=','+','-','@')) else v for v in values])
    # The new consolidated artifact is separate from the original safe datasets.
    final=ROOT/'datasets/person_guardrail_tr_v2_review'
    if final.exists():
        prior=json.loads((final/'dataset_manifest.json').read_text())
        if not args.replace_own_draft or prior.get('total')!=3500 or not prior.get('run_directory','').startswith('results/caption_500_codex_'):
            raise ValueError('Existing dataset is not this session draft, or replacement not explicitly selected')
    final.mkdir(parents=True,exist_ok=args.replace_own_draft)
    merged={split:list(rows) for split,rows in safe.items()}
    merged['legacy_review']=[]
    exposed_groups={r['group_id'] for r in old}
    for rows in merged.values():
        for r in rows:
            if r['group_id'] in exposed_groups:
                r['evaluation_independence']='development_exposed_by_legacy_141'
    for r in all_positive:
        merged[r['split']].append(r)
    groups_seen,texts_seen=set(),set()
    for split,rows in merged.items():
        groups={r['group_id'] for r in rows}
        texts={normal(r['text']) for r in rows}
        assert not groups_seen & groups, f'group leakage: {split}'
        assert not texts_seen & texts, f'text leakage: {split}'
        groups_seen |= groups
        texts_seen |= texts
        for r in rows:
            assert len(r['labels'])==len(r['label_mask'])==11
        write_rows(final/f'{split}.jsonl',rows)
    write_rows(final/'sexual_candidates_500.jsonl',all_positive)
    write_json(final/'label_schema.json',json.loads((SAFE/'label_schema.json').read_text()))
    manifest={'safe':3000,'sexual_candidates':500,'legacy_candidates':141,'new_codex_candidates':359,'total':3500,
        'counts':{s:{'safe':sum(not r.get('labels_are_proposed',False) for r in rows),
                     'sexual_candidates':sum(r.get('labels_are_proposed',False) for r in rows),'total':len(rows)} for s,rows in merged.items()},
        'new_source_rows':359,'new_source_groups':359,'new_gender_hints':dict(Counter(r['gender_hint'] for r in new)),
        'new_source_topics':dict(Counter(r['source_topic'] for r in new)),
        'style_patterns':dict(Counter(r['style_pattern'] for r in new)),
        'unique_new_appearance_phrases':len({r['appearance_phrase'] for r in new}),
        'legacy_provenance_preserved':True,'source_words_retained_for_all_new':True,
        'group_overlap_across_splits':0,'normalized_text_overlap_across_splits':0,
        'source_identity_method':'unverified_filename_prefix_not_true_person_id',
        'sexual_labels_are_proposals':True,'human_review':'pending','ready_for_training':False,
        'positive_loss_mask':[0.,0.,0.,0.,0.,1.,0.,0.,0.,0.,0.],
        'positive_unsafe_target':'unknown_masked','masked_bce_required':True,
        'independent_positive_test_available':False,
        'test_warning':'Legacy query captions were previously used in prompt/style decisions; exposed rows are development evaluation, not independent final test',
        'training_started':False,'model_api_calls':0,
        'source_hashes':hashes,'run_directory':out.relative_to(ROOT).as_posix(),
        'new_caption_method':'Codex-authored compositional augmentation with stored phrase inventory; template correlation remains possible'}
    for s in SPLITS:
        assert hashlib.sha256((SAFE/f'{s}.jsonl').read_bytes()).hexdigest()==hashes[s]
    write_json(out/'quality_check.json',manifest)
    write_json(final/'dataset_manifest.json',manifest)
    # Standalone review UI; user text is HTML-escaped and never injected as markup.
    body=[]
    for i,r in enumerate(all_positive,1):
        cells=[str(i),r['batch']+' · '+r['split']+' · '+r['filename'],r['source_caption_tr'],r['text']]
        body.append('<tr>'+''.join('<td>'+html.escape(v)+'</td>' for v in cells)+'</tr>')
    page='''<!doctype html><html lang="tr"><meta charset="utf-8"><title>500 caption inceleme</title>
<style>body{font:16px/1.55 system-ui;margin:24px;color:#18212c;background:#f6f8fb}h1{font-size:25px}input{font:inherit;padding:10px;width:70%;margin:10px 0 22px}table{border-collapse:collapse;width:100%;background:white}td,th{padding:12px;border:1px solid #d7dee8;text-align:left;vertical-align:top}td:nth-child(3),td:nth-child(4){width:38%}th{background:#e7eef7;position:sticky;top:0}.muted{color:#526071}</style>
<h1>141 mevcut + 359 yeni = 500 caption adayı</h1><p>Kaynak ve aday yan yana. Etiketler inceleme bekliyor; eğitim başlamadı.</p>
<p class="muted">Yeni adaylar Codex tarafından yerelde, kayıtlı ifade envanteriyle oluşturuldu. Mevcut 141 kaydın üretici bilgisi korunur. Train/validation ve query ayrımı korunmuştur.</p>
<input id="filter" placeholder="Dosya adı, kıyafet, split veya kelime ara"><span id="count">500 kayıt</span>
<table><thead><tr><th>No</th><th>Kaynak / bölüm</th><th>Özgün caption</th><th>Aday caption</th></tr></thead><tbody>'''+''.join(body)+'''</tbody></table>
<script>const rows=[...document.querySelectorAll('tbody tr')];document.querySelector('#filter').addEventListener('input',e=>{let n=0;const q=e.target.value.toLocaleLowerCase('tr');for(const r of rows){const ok=r.textContent.toLocaleLowerCase('tr').includes(q);r.hidden=!ok;if(ok)n++}document.querySelector('#count').textContent=n+' kayıt'});</script></html>'''
    (out/'review.html').write_text(page,encoding='utf-8')
    instructions='''# Türkçe guardrail birleşik inceleme veri seti

3.000 safe + 500 sexual adayı = **3.500 kayıt**. Yeni 359 aday, Türkçeye
çevrilmiş 359 farklı kaynaktan ve 359 farklı önek grubundan gelir.
Kaynaklar kullanıcı tarafından yetişkin olarak doğrulanmıştır. Çocuk/ergen
ipuçları, birden fazla kişi ve otomatik çeviri uyarılı kaynaklar yeni üretime alınmadı.

Yeni adaylar Codex tarafından yerelde yazılmış ifade envanteriyle bileşimsel
olarak oluşturuldu; Qwen/Grok/API çıktısı değildir. Envanter ve üretim biçimi
çalışma klasöründedir. Bu yöntem kalıp benzerliği taşıyabilir; bağımsız doğal
örnek çeşitliliği veya semantik etiket doğruluğu garantisi değildir.
Kıyafet adları, dar giysi veya nötr beden tarifi tek başına sexual sayılmaz.
"Seksi/baştan çıkarıcı" gibi nitelemelerin etiketi ayrıca insan incelemesi gerektirir.

Yeni adayların **326'sı train, 33'ü validation** kaynaklıdır; varyantlar
kaynaklarıyla aynı split'te kalır. Mevcut 141 aday query kaynaklıdır ve train'e
eklenmedi. Safe test/challenge ile aynı gruptakiler o split'e, diğerleri
`legacy_review` bölümüne yerleştirildi. Önceki prompt/üslup kararlarında görülen
query kayıtları bağımsız nihai test sayılmaz; bu durum satırlarda işaretlidir.
Gerçek kişi kimliği doğrulanmadı; ayrım önek ve normalize birebir metne dayanır.

`text` Türkçe girdidir. Safe satırların kaynak etiketleri korunur. Pozitif
adayların `labels` alanı **önerilen** hedeftir: yalnız indeks 5
(`SEXUAL_CONTENT_ADULT`) 1. Diğer çıkışlar bilinmeyen olarak `label_mask=0`.
Genel `unsafe` kararı otomatik pozitif veya negatif yapılmadı.
**Maskeli BCE gerekir; standart Trainer label_mask'i kendiliğinden uygulamaz.**
Pozitifler `review_status=pending`, `training_eligible=false` taşır.
Bu dosyalar insan incelemesi öncesi son birleşik taslaktır; eğitim hazır/onaylı
etiketli veri olarak sunulmaz. Eğitim veya yeni model skorlama çalıştırılmadı.

`dataset_manifest.json` kesin sayımları, kontrolleri ve sınırlamaları içerir.
Orijinal 3.000 safe dosya ile mevcut 141 adayın dosyaları değiştirilmedi.
'''
    (final/'README.md').write_text(instructions,encoding='utf-8')
    (out/'README.md').write_text(instructions+'\nİnceleme: `review.html`, `comparison.csv`, `new_359.txt`, `sexual_500.txt`.\n',encoding='utf-8')
    write_json(ROOT/'results/LATEST_CAPTION_500.json',{'run':out.relative_to(ROOT).as_posix(),'dataset':final.relative_to(ROOT).as_posix()})
    print(json.dumps({'output':str(out),'dataset':str(final),**manifest},ensure_ascii=False))


if __name__=='__main__':
    main()
