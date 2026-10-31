"""Add source-grounded safe counterparts and export 500 linked contrast pairs."""
from collections import Counter, defaultdict
from datetime import datetime
import csv
import hashlib
import html
import json
from pathlib import Path
import re
from zoneinfo import ZoneInfo

from build_caption_candidates_500 import adultize, upper_first, normal, retained_in_order

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'datasets/person_guardrail_tr_v2_review'
TARGET=ROOT/'datasets/person_guardrail_tr_v3_paired_review'
SPLITS=('train','validation','test','challenge','legacy_review')


def read(path):
    return [json.loads(x) for x in path.read_text(encoding='utf-8-sig').splitlines() if x.strip()]


def write_rows(path,rows):
    path.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def write_json(path,value):
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def main():
    stamp=datetime.now(ZoneInfo('Europe/Istanbul')).strftime('%Y%m%d_%H%M%S')
    run=ROOT/'results'/f'safe_sexual_pairs_{stamp}'
    run.mkdir(parents=True,exist_ok=False)
    if TARGET.exists() and any(TARGET.iterdir()):
        raise ValueError('Target already contains a dataset; choose a new target version')
    TARGET.mkdir(parents=True,exist_ok=True)
    signatures={split:sha((SOURCE/f'{split}.jsonl').read_text()) for split in SPLITS}
    parent=json.loads((SOURCE/'dataset_manifest.json').read_text())
    rows={split:read(SOURCE/f'{split}.jsonl') for split in SPLITS}
    flat=[r for values in rows.values() for r in values]
    inherited_duplicates=sum(len(values)-len({normal(r['text']) for r in values}) for values in rows.values())
    positives=[r for r in flat if r.get('labels_are_proposed')]
    assert len(positives)==500 and len(flat)==3500
    by_text={normal(r['text']):r for r in flat if r.get('safety_label')=='safe'}
    all_by_text={normal(r['text']):r for r in flat}
    new_safe=[]
    paired_safe=[]
    pairs=[]
    reused=0
    for positive in positives:
        # Reuse the neutral source, rather than deleting isolated sexual keywords
        # from the positive and accidentally leaving sexualized assertions behind.
        neutral=upper_first(adultize(positive['source_caption_tr'])).strip()
        key=normal(neutral)
        assert retained_in_order(positive['source_caption_tr'],neutral)
        assert re.search(r'\byetişkin\b|\borta yaşlı\b|\byaşlı\b',neutral,re.I)
        assert not re.search(r'erotik|şehvet|seksi|tahrik|baştan çıkar|kışkırt|cinsel',neutral,re.I)
        if key in by_text:
            safe=by_text[key]
            assert safe['split']==positive['split'] and safe['group_id']==positive['group_id']
            reused+=1
        else:
            assert key not in all_by_text
            safe={
                'id':'paired-safe-'+sha(positive['source_id']+'|'+neutral),
                'text':neutral,'language':'tr','labels':[0.0]*11,'label_mask':[1.0]*11,
                'safety_label':'safe','labels_are_proposed':False,
                'label_source':'user_confirmed_safe_source_with_user_confirmed_adulthood',
                'review_status':'source_safe_user_confirmed',
                'source_id':positive['source_id'],'source_file':positive['source_file'],
                'source_line':positive['source_line'],'filename':positive['filename'],
                'group_id':positive['group_id'],'group_method':positive['group_method'],
                'split':positive['split'],'source_caption_tr':positive['source_caption_tr'],
                'source_text_en':positive['source_text_en'],
                'adult_evidence_source':positive['source_age_evidence'],
                'text_transform':('preserved_safe_source' if neutral==positive['source_caption_tr'] else 'adulthood_alignment_only'),
                'synthetic':neutral!=positive['source_caption_tr'],
                'augmentation_family':positive['source_id'],
                'counterpart_origin_batch':positive['batch'],
                'independent_test':False if positive['batch']=='legacy_141' else None,
            }
            if positive['batch']=='legacy_141':
                safe['evaluation_independence']='development_exposed_by_legacy_141'
            rows[safe['split']].append(safe)
            by_text[key]=safe
            all_by_text[key]=safe
            new_safe.append(safe)
        pair_id='pair-'+sha(positive['id'])
        for record,side,other in [(safe,'safe',positive),(positive,'sexual_candidate',safe)]:
            record.setdefault('pair_ids',[]).append(pair_id)
            record.setdefault('paired_record_ids',[]).append(other['id'])
            record['pair_side']=side
            record['augmentation_family']=positive['source_id']
        paired_safe.append(safe)
        pairs.append({'pair_id':pair_id,'split':positive['split'],'group_id':positive['group_id'],
            'filename':positive['filename'],'source_id':positive['source_id'],
            'safe_id':safe['id'],'sexual_id':positive['id'],
            'safe_text':safe['text'],'sexual_text':positive['text'],
            'source_caption_tr':positive['source_caption_tr'],
            'safe_labels':safe['labels'],'safe_label_mask':safe['label_mask'],
            'sexual_proposed_labels':positive['labels'],'sexual_label_mask':positive['label_mask'],
            'sexual_review_status':positive['review_status'],
            'pair_type':'source_matched_contrast',
            'strict_minimal_pair_verified':False,
            'source_word_retention_for_positive':positive.get('source_words_retained_in_order',False),
            'neutral_preserves_user_confirmed_adulthood':True})
    assert len(new_safe)==467 and reused==33 and len(pairs)==500
    assert len({r['id'] for r in paired_safe})==500
    group_seen,text_seen=set(),set()
    final_duplicates=0
    total_ids=[]
    for split,values in rows.items():
        groups={r['group_id'] for r in values}
        texts={normal(r['text']) for r in values}
        assert not group_seen & groups,split
        assert not text_seen & texts,split
        final_duplicates+=len(values)-len(texts)
        group_seen|=groups
        text_seen|=texts
        total_ids.extend(r['id'] for r in values)
        for r in values:
            assert len(r['labels'])==len(r['label_mask'])==11
        write_rows(TARGET/f'{split}.jsonl',values)
    assert len(total_ids)==len(set(total_ids))==3967
    assert final_duplicates==inherited_duplicates
    write_rows(TARGET/'pairs_500.jsonl',pairs)
    write_rows(TARGET/'safe_counterparts_500.jsonl',paired_safe)
    write_rows(TARGET/'sexual_candidates_500.jsonl',positives)
    write_rows(TARGET/'paired_view_1000.jsonl',[r for safe,sexual in zip(paired_safe,positives) for r in (safe,sexual)])
    write_rows(run/'added_safe_467.jsonl',new_safe)
    write_rows(run/'pairs_500.jsonl',pairs)
    (run/'pairs_500.txt').write_text('\n\n'.join(
        f"{i}. [{p['filename']}] [{p['split']}]\nSAFE: {p['safe_text']}\nSEXUAL ADAY: {p['sexual_text']}"
        for i,p in enumerate(pairs,1))+'\n',encoding='utf-8')
    with (run/'pairs_500.csv').open('w',encoding='utf-8-sig',newline='') as file:
        writer=csv.writer(file)
        writer.writerow(['pair_id','split','filename','safe','sexual_candidate','sexual_review_status','human_decision','notes'])
        for p in pairs:
            values=[p['pair_id'],p['split'],p['filename'],p['safe_text'],p['sexual_text'],p['sexual_review_status'],'','']
            writer.writerow(["'"+v if v.lstrip().startswith(('=','+','-','@')) else v for v in values])
    body=[]
    for i,p in enumerate(pairs,1):
        values=[str(i),p['split']+' · '+p['filename'],p['safe_text'],p['sexual_text']]
        body.append('<tr>'+''.join('<td>'+html.escape(v)+'</td>' for v in values)+'</tr>')
    page='''<!doctype html><html lang="tr"><meta charset="utf-8"><title>500 safe / sexual çift</title>
<style>body{font:16px/1.55 system-ui;margin:24px;background:#f6f8fb;color:#172331}h1{font-size:25px}input{padding:10px;font:inherit;width:70%;margin:16px 0}table{border-collapse:collapse;width:100%;background:white}td,th{padding:12px;border:1px solid #d6dde8;vertical-align:top;text-align:left}td:nth-child(3),td:nth-child(4){width:40%}th{position:sticky;top:0;background:#e5edf6}</style>
<h1>500 safe / sexual aday çifti</h1><p>Aynı kaynaktan nötr ve cinselleştirici görünüş tarifi. İki tarafta da yetişkinlik bilgisi korunur. Pozitif adaylar inceleme bekler.</p>
<input id="filter" placeholder="Dosya, kıyafet, split veya kelime ara"><span id="count">500 çift</span>
<table><thead><tr><th>No</th><th>Kaynak</th><th>SAFE</th><th>SEXUAL ADAY</th></tr></thead><tbody>'''+''.join(body)+'''</tbody></table><script>const rows=[...document.querySelectorAll('tbody tr')];document.querySelector('#filter').addEventListener('input',e=>{const q=e.target.value.toLocaleLowerCase('tr');let n=0;for(const r of rows){r.hidden=!r.textContent.toLocaleLowerCase('tr').includes(q);if(!r.hidden)n++}document.querySelector('#count').textContent=n+' çift'});</script></html>'''
    (run/'review.html').write_text(page,encoding='utf-8')
    counts={split:{'safe':sum(r['safety_label']=='safe' for r in values),
        'sexual_candidates':sum(r.get('labels_are_proposed',False) for r in values),'total':len(values)} for split,values in rows.items()}
    manifest={'source_dataset':SOURCE.relative_to(ROOT).as_posix(),'source_split_hashes':signatures,
        'safe':3467,'sexual_candidates':500,'total':3967,'counts':counts,
        'pairs':500,'safe_counterparts':500,'reused_existing_safe':33,'added_safe':467,
        'paired_view_safe':500,'paired_view_sexual_candidates':500,
        'pair_splits':dict(Counter(p['split'] for p in pairs)),
        'safe_labels':[0.0]*11,'safe_label_mask':[1.0]*11,
        'positive_labels_are_proposed':True,'human_review':'sexual_candidates_pending',
        'ready_for_training':False,'masked_bce_required':True,
        'source_matched_pairs_are_not_all_verified_strict_minimal_pairs':True,
        'pair_group_and_split_alignment_verified':True,
        'adulthood_explicit_on_both_sides':True,
        'normalized_text_overlap_across_splits':0,'group_overlap_across_splits':0,
        'inherited_duplicate_text_rows':inherited_duplicates,
        'new_duplicate_text_rows_added':0,'source_group_is_unverified_filename_prefix':True,
        'independent_positive_test_available':False,
        'test_warning':parent['test_warning'],
        'training_started':False,'model_api_calls':0,'run_directory':run.relative_to(ROOT).as_posix(),
        'sampling_note':'The full dataset includes the original safe captions and age-aligned safe counterparts. Sample by source/pair when needed to prevent accidental overweighting. Never concatenate paired_view_1000 with the full split files.'}
    assert all(sha((SOURCE/f'{split}.jsonl').read_text())==signatures[split] for split in SPLITS)
    write_json(TARGET/'dataset_manifest.json',manifest)
    write_json(run/'quality_check.json',manifest)
    write_json(TARGET/'label_schema.json',json.loads((SOURCE/'label_schema.json').read_text()))
    readme='''# Türkçe guardrail — 500 safe / sexual aday çifti

**3.467 safe + 500 sexual adayı = 3.967 kayıt (benzersiz kayıt kimlikleri).**
Önceki 3.000 safe kayıt korunur. 500 adayın her birine nötr karşılık bağlandı:
33 nötr metin zaten birebir vardı, 467 yeni nötr karşılık eklendi.
Yeni safe metinler özgün safe kaynak tarifleridir; yalnız kayıtlı kullanıcı
doğrulamasına dayanan yetişkinlik bilgisi iki tarafta eşitlenmiştir.
Pozitiflerdeki cinselleştirici sözcükleri mekanik olarak silerek üretilmedi.

`pairs_500.jsonl`: safe/sexual metinleri, kayıt kimlikleri ve split/grup ile
500 kaynak eşleştirmesi. `safe_counterparts_500.jsonl` ve
`sexual_candidates_500.jsonl` karşılıkların ayrı görünümleridir.
`paired_view_1000.jsonl`: 500 safe + 500 sexual adayından dengeli çift görünümü.
**Bu görünümleri tam split dosyalarına tekrar ekleme; aynı kayıtlar zaten var.**
Eğitimde gerektiğinde kaynak/çift bazında örnekleme kullan; yetişkinlik eklenmiş
safe varyantlar ile özgün safe metinler aynı kaynağın farklı görünümleridir.

Safe etiketleri 11 sıfır, label_mask 11 birdir. Sexual etiketleri önceki
sürümdeki inceleme bekleyen öneriler olarak korunur; diğer hazard ve genel
unsafe hedefleri bilinmeyen/maskeli kalır. Maskeli BCE gerekir.
Önceki Türkçe sette bulunan iki train-içi birebir metin tekrarı korunmuştur;
bu işlem yeni birebir metin tekrarı eklemedi. Çift görünümündeki 500 safe metin farklıdır.
Kaynak eşleşmesi tüm çiftlerin kusursuz minimal çift olduğunu kanıtlamaz:
özellikle eski 141 üretimde kaynak ayrıntıları ayrıca incelenmelidir.

Her çift aynı split ve gruptadır; query kaynaklı 141 aday train'e alınmadı.
Önceden görülen query adayları bağımsız nihai test sayılmaz.
Önek grup anahtarı doğrulanmış kişi kimliği değildir.
`dataset_manifest.json` kesin sayımları ve sınırlamaları içerir.
Eski veri dosyaları değiştirilmedi. Eğitim başlamadı.
'''
    (TARGET/'README.md').write_text(readme,encoding='utf-8')
    (run/'README.md').write_text(readme+'\nİnceleme: `review.html`, `pairs_500.txt`, `pairs_500.csv`.\n',encoding='utf-8')
    write_json(ROOT/'results/LATEST_PAIRED_DATASET.json',{'run':run.relative_to(ROOT).as_posix(),'dataset':TARGET.relative_to(ROOT).as_posix()})
    print(json.dumps(manifest,ensure_ascii=False))


if __name__=='__main__':
    main()
