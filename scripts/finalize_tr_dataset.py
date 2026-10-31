"""Validate and export translated safe captions without loading or training a model."""
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / 'datasets/person_guardrail_safe_v1'
RUN = ROOT / 'results/translate_tr_3000_qwen38_20261031'
OUT = ROOT / 'datasets/person_guardrail_safe_tr_v1'
SPLITS = ('train', 'validation', 'test', 'challenge')


def read(path):
    return [json.loads(x) for x in path.read_text(encoding='utf-8-sig').splitlines() if x.strip()]


def main():
    originals = [r for s in SPLITS for r in read(SOURCE / f'{s}.jsonl')]
    original_by_id = {r['id']: r for r in originals}
    translated = read(RUN / 'translations.jsonl')
    assert len(translated) == len(originals) == 3000, 'Translation coverage is incomplete'
    assert len({r['id'] for r in translated}) == 3000
    assert {r['id'] for r in translated} == set(original_by_id)
    config = json.loads((RUN / 'config.json').read_text())
    for split in SPLITS:
        assert hashlib.sha256((SOURCE / f'{split}.jsonl').read_bytes()).hexdigest() == config['source_sha256'][split]
    for row in translated:
        original = original_by_id[row['id']]
        assert row['text'].strip() and row['language'] == 'tr'
        assert row['source_text_en'] == original['text']
        for key in ('split', 'source_file', 'source_line', 'filename', 'group_id', 'labels', 'label_mask'):
            assert row[key] == original[key], (row['id'], key)
        assert row['labels'] == [0.0]*11 and row['label_mask'] == [1.0]*11
        assert 'baseline_scores' not in row and 'token_count' not in row
    order = {r['id']: i for i, r in enumerate(originals)}
    translated.sort(key=lambda r: order[r['id']])
    texts = defaultdict(list)
    for row in translated:
        texts[' '.join(row['text'].casefold().split())].append({'id': row['id'], 'split': row['split']})
    overlaps = [v for v in texts.values() if len({r['split'] for r in v}) > 1]
    within = [v for v in texts.values() if len(v) > 1]
    OUT.mkdir(parents=True, exist_ok=True)
    for split in SPLITS:
        selected = [r for r in translated if r['split'] == split]
        (OUT / f'{split}.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in selected), encoding='utf-8')
    shutil.copyfile(SOURCE / 'label_schema.json', OUT / 'label_schema.json')
    summary = {'counts': dict(Counter(r['split'] for r in translated)), 'language': 'tr',
        'translation_model': config['model'], 'quantization': 'Q4_K_M', 'thinking_enabled': False,
        'gpu_physical_index': 5, 'source_rows_checked': 3000, 'source_metadata_unchanged': True,
        'source_english_hashes_unchanged': True, 'label_vectors_checked': 3000, 'label_dimensions': 11,
        'machine_translation_flagged': sum(bool(r['translation_flags']) for r in translated),
        'translation_flag_counts': dict(Counter(f for r in translated for f in r['translation_flags'])),
        'translation_exact_duplicate_groups': within, 'cross_split_translation_duplicates': overlaps,
        'human_review': 'pending', 'safe_only': True, 'sexual_positives_added': 0,
        'turkish_guardrail_scores_measured': False, 'guardrail_training_started': False,
        'ready_for_training': False, 'source_dataset': SOURCE.relative_to(ROOT).as_posix(),
        'translation_run': RUN.relative_to(ROOT).as_posix()}
    (OUT / 'quality_check.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    (OUT / 'README.md').write_text('''# Türkçe safe person caption alt kümesi

Kullanıcının isteğiyle seçilmiş 3.000 safe caption Türkçeye çevrildi:
2.000 train, 250 validation, 500 test ve 250 challenge.

Çeviri: yerel Qwen3.8 27B, Q4_K_M (4 bit), thinking kapalı, fiziksel GPU 5.
Çeviriler otomatik üretilmiştir; insan tarafından tüm satırlar incelenmemiştir.
Kullanıcı mevcut aşamada küçük çeviri hatalarını kabul ederek toplu çeviri istedi.
Otomatik terim kontrolleri semantik doğruluk garantisi değildir; işaretler
`translation_flags` alanında ve kalite raporundadır.

`text` Türkçe girdidir; `source_text_en` özgün İngilizce metindir.
Kaynak kimliği, dosya/satır, grup, split, 11 sıfırlık safe etiketi ve label mask
aynen korunmuştur. Safe etiketleri kullanıcının kaynak veri beyanından gelir.
`source_baseline_scores_en` yalnız İngilizce kaynağın eski skorlarıdır;
Türkçe ölçümü değildir. Türkçe token uzunlukları henüz guardrail tokenizer'ıyla ölçülmedi.

Kaynaklar ve bütün varyantları aynı split'te kalmalıdır. Grup ayrım kaydı:
`../person_guardrail_safe_v1/source_group_assignments.json`.
Çeviride oluşabilecek birebir metin tekrarları `quality_check.json` içinde
raporlanır; eğitimden önce varsa splitler arası metin çakışmaları giderilmelidir.

Bu alt küme yalnız safe örnekler içerir. Sexual pozitifler henüz eklenmedi,
guardrail eğitimi başlamadı. Tam fine-tune verisi değildir.
Önceki 141 query kaynaklı sexual aday train'e eklenmemelidir.

Kaynak/çeviri karşılaştırmaları ve tekrar başlatılabilir işlem kayıtları:
`../../results/translate_tr_3000_qwen38_20261031/`.
''', encoding='utf-8')
    print(json.dumps({k: v for k, v in summary.items() if 'duplicate' not in k}, ensure_ascii=False))


if __name__ == '__main__':
    main()
