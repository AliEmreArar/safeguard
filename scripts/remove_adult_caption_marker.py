"""Remove the Turkish adult marker from all active caption text and rebuild pairs."""
import argparse
from collections import Counter, defaultdict
from datetime import datetime
import csv
import hashlib
import html
import json
from pathlib import Path
import re
from zoneinfo import ZoneInfo

from build_caption_candidates_500 import normal, upper_first

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'datasets/person_guardrail_tr_v3_paired_review'
TARGET=ROOT/'datasets/person_guardrail_tr_v4_no_adult_marker_review'
SPLITS=('train','validation','test','challenge','legacy_review')
MARKER=re.compile(r'\byetişkin(?:ler(?:in|i|e|den|de)?|in|i|e|den|de)?\b',re.I)
TEXT_KEYS={'text','caption','safe_text','sexual_text','source_caption_tr','source_caption','appearance_phrase'}


def read(path):
    return [json.loads(x) for x in path.read_text(encoding='utf-8-sig').splitlines() if x.strip()]


def write_rows(path,rows):
    path.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')


def write_json(path,obj):
    path.write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')


def sha(text):
    return hashlib.sha256(text.encode()).hexdigest()


def clean_caption(text):
    # If "adult" is the only person noun in a clause, retain that subject as
    # "person"; otherwise simply remove the age adjective.
    if MARKER.search(text):
        first=re.split(r'[;.!?]',text,maxsplit=1)[0]
        if MARKER.search(first) and not re.search(r'\b(kadın|erkek|kişi|birey)\b',first,re.I):
            text=MARKER.sub('kişi',text,count=1)
        text=MARKER.sub('',text)
    text=re.sub(r'\s+',' ',text).strip()
    text=re.sub(r'\s+([,;:.!?])',r'\1',text)
    text=re.sub(r'([,;])\s*[,;]+',r'\1',text)
    text=re.sub(r'^[,;:.!?]+\s*','',text)
    return upper_first(text)


def clean_fields(obj):
    if isinstance(obj,list):
        return [clean_fields(x) for x in obj]
    if isinstance(obj,dict):
        return {k:(MARKER.sub('',v).strip() if k=='appearance_phrase' else clean_caption(v))
                if k in TEXT_KEYS and isinstance(v,str) else clean_fields(v)
                for k,v in obj.items()}
    return obj


def assert_caption_fields_clean(obj):
    if isinstance(obj,list):
        for value in obj:assert_caption_fields_clean(value)
    elif isinstance(obj,dict):
        for key,value in obj.items():
            if key in TEXT_KEYS and isinstance(value,str):
                assert not MARKER.search(value),(key,value)
            else:assert_caption_fields_clean(value)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--revise-own-output',action='store_true')
    args=parser.parse_args()
    stamp=datetime.now(ZoneInfo('Europe/Istanbul')).strftime('%Y%m%d_%H%M%S')
    run=ROOT/'results'/f'caption_marker_removed_{stamp}'
    run.mkdir(parents=True,exist_ok=False)
    if TARGET.exists():
        previous=json.loads((TARGET/'dataset_manifest.json').read_text())
        if not args.revise_own_output or previous.get('caption_marker_removed')!='yetişkin' or previous.get('source_dataset')!=SOURCE.relative_to(ROOT).as_posix():
            raise ValueError('Refusing to overwrite a different dataset')
    TARGET.mkdir(parents=True,exist_ok=args.revise_own_output)
    hashes={s:sha((SOURCE/f'{s}.jsonl').read_text()) for s in SPLITS}
    parent=json.loads((SOURCE/'dataset_manifest.json').read_text())
    oldrows=[r for split in SPLITS for r in read(SOURCE/f'{split}.jsonl')]
    oldpairs=read(SOURCE/'pairs_500.jsonl')
    cleaned=[]
    changed=occurrences=0
    for old in oldrows:
        row=clean_fields(old)
        if row['text']!=old['text']:
            changed+=1
            row['caption_transform']='adult_marker_removed'
            row['parent_text_sha256']=sha(old['text'])
        occurrences+=len(MARKER.findall(old['text']))
        row.pop('pair_ids',None)
        row.pop('paired_record_ids',None)
        row.pop('pair_side',None)
        assert row['labels']==old['labels'] and row['label_mask']==old['label_mask']
        assert row['text']
        cleaned.append(row)
    # Deduplicate only equivalent safe records from the same source group.
    # Prefer original safe record identities over added age-aligned copies.
    cleaned.sort(key=lambda r:r['id'].startswith('paired-safe-'))
    canonical={}
    aliases={}
    for row in cleaned:
        key=(row['split'],row['group_id'],normal(row['text']),tuple(row['labels']),tuple(row['label_mask']))
        if key in canonical:
            keep=canonical[key]
            assert row['safety_label']==keep['safety_label']=='safe'
            aliases[row['id']]=keep['id']
            keep.setdefault('merged_equivalent_record_ids',[]).append(row['id'])
        else:
            canonical[key]=row
            aliases[row['id']]=row['id']
    rows=list(canonical.values())
    byid={r['id']:r for r in rows}
    pairs=[]
    for old in oldpairs:
        p=clean_fields(old)
        safe=byid[aliases[old['safe_id']]]
        sexual=byid[aliases[old['sexual_id']]]
        assert safe['split']==sexual['split']==p['split']
        assert safe['group_id']==sexual['group_id']==p['group_id']
        for r,side,other in [(safe,'safe',sexual),(sexual,'sexual_candidate',safe)]:
            r.setdefault('pair_ids',[]).append(p['pair_id'])
            r.setdefault('paired_record_ids',[]).append(other['id'])
            r['pair_side']=side
        p.update(safe_id=safe['id'],sexual_id=sexual['id'],safe_text=safe['text'],sexual_text=sexual['text'])
        p.pop('neutral_preserves_user_confirmed_adulthood',None)
        p['adulthood_evidence_location']='metadata_only'
        p['adult_marker_in_model_text']=False
        pairs.append(p)
    assert len(pairs)==500 and len({p['safe_id'] for p in pairs})==500
    assert sum(r.get('labels_are_proposed',False) for r in rows)==500
    ordered={s:[r for r in rows if r['split']==s] for s in SPLITS}
    groups_seen,texts_seen=set(),set()
    duplicates=0
    for split,values in ordered.items():
        groups={r['group_id'] for r in values}
        texts={normal(r['text']) for r in values}
        assert not groups_seen & groups
        assert not texts_seen & texts
        groups_seen|=groups;texts_seen|=texts
        duplicates+=len(values)-len(texts)
        assert_caption_fields_clean(values)
        write_rows(TARGET/f'{split}.jsonl',values)
    safe_pairs=[byid[p['safe_id']] for p in pairs]
    sexual_pairs=[byid[p['sexual_id']] for p in pairs]
    view=[r for a,b in zip(safe_pairs,sexual_pairs) for r in (a,b)]
    new359=[r for r in sexual_pairs if r['batch']=='new_359']
    for name,values in [('pairs_500',pairs),('safe_counterparts_500',safe_pairs),
                        ('sexual_candidates_500',sexual_pairs),('paired_view_1000',view),
                        ('new_359',new359)]:
        assert_caption_fields_clean(values)
        write_rows(TARGET/f'{name}.jsonl',values)
    write_rows(run/'pairs_500.jsonl',pairs)
    for name,values in [('sexual_500',sexual_pairs),('new_359',new359)]:
        (run/f'{name}.txt').write_text('\n\n'.join(f"{i}. [{r['filename']}] [{r['split']}]\n{r['text']}" for i,r in enumerate(values,1))+'\n',encoding='utf-8')
    (run/'pairs_500.txt').write_text('\n\n'.join(f"{i}. [{p['filename']}] [{p['split']}]\nSAFE: {p['safe_text']}\nSEXUAL ADAY: {p['sexual_text']}" for i,p in enumerate(pairs,1))+'\n',encoding='utf-8')
    with (run/'pairs_500.csv').open('w',encoding='utf-8-sig',newline='') as file:
        writer=csv.writer(file)
        writer.writerow(['pair_id','split','filename','safe','sexual_candidate','human_decision','notes'])
        for p in pairs:
            values=[p['pair_id'],p['split'],p['filename'],p['safe_text'],p['sexual_text'],'','']
            writer.writerow(["'"+v if v.lstrip().startswith(('=','+','-','@')) else v for v in values])
    body=[]
    for i,p in enumerate(pairs,1):
        vals=[str(i),p['split']+' · '+p['filename'],p['safe_text'],p['sexual_text']]
        body.append('<tr>'+''.join('<td>'+html.escape(v)+'</td>' for v in vals)+'</tr>')
    page='''<!doctype html><html lang="tr"><meta charset="utf-8"><title>500 caption çifti</title>
<style>body{font:16px/1.55 system-ui;margin:24px;color:#182332;background:#f5f8fc}h1{font-size:25px}input{font:inherit;padding:10px;width:70%;margin:14px 0}table{border-collapse:collapse;width:100%;background:white}td,th{padding:12px;border:1px solid #d7dfea;vertical-align:top;text-align:left}td:nth-child(3),td:nth-child(4){width:40%}th{position:sticky;top:0;background:#e6edf7}</style>
<h1>500 safe / sexual aday çifti</h1><p>Güncel temizlenmiş caption'lar. Yaş doğrulaması yalnız metadata'da saklanır. Pozitif etiketler inceleme bekler.</p>
<input id="filter" placeholder="Dosya, kıyafet, kelime veya split ara"><span id="count">500 çift</span>
<table><thead><tr><th>No</th><th>Kaynak</th><th>SAFE</th><th>SEXUAL ADAY</th></tr></thead><tbody>'''+''.join(body)+'''</tbody></table><script>const rows=[...document.querySelectorAll('tbody tr')];document.querySelector('#filter').addEventListener('input',e=>{let n=0;const q=e.target.value.toLocaleLowerCase('tr');for(const r of rows){r.hidden=!r.textContent.toLocaleLowerCase('tr').includes(q);if(!r.hidden)n++}document.querySelector('#count').textContent=n+' çift'});</script></html>'''
    (run/'review.html').write_text(page,encoding='utf-8')
    manifest={**parent,'source_dataset':SOURCE.relative_to(ROOT).as_posix(),'source_split_hashes':hashes,
        'safe':sum(r['safety_label']=='safe' for r in rows),'total':len(rows),
        'counts':{s:{'safe':sum(r['safety_label']=='safe' for r in v),'sexual_candidates':sum(r.get('labels_are_proposed',False) for r in v),'total':len(v)} for s,v in ordered.items()},
        'caption_marker_removed':'yetişkin','removed_marker_occurrences':occurrences,
        'changed_input_captions':changed,'remaining_marker_in_caption_fields':0,
        'adulthood_evidence_location':'metadata_only','adulthood_explicit_on_both_sides':False,
        'same_group_equivalent_rows_merged':len(oldrows)-len(rows),
        'safe_counterparts':500,'pairs':500,'paired_view_safe':500,'paired_view_sexual_candidates':500,
        'pair_splits':dict(Counter(p['split'] for p in pairs)),
        'inherited_duplicate_text_rows':duplicates,
        'age_alignment_added_safe_before_cleanup':parent['added_safe'],
        'run_directory':run.relative_to(ROOT).as_posix(),
        'sampling_note':'Paired views reference records already in full splits. Do not concatenate them.',
        'ready_for_training':False,'training_started':False}
    manifest.pop('added_safe',None)
    manifest.pop('reused_existing_safe',None)
    assert len(view)==1000 and len(new359)==359
    assert all(sha((SOURCE/f'{s}.jsonl').read_text())==hashes[s] for s in SPLITS)
    write_json(TARGET/'dataset_manifest.json',manifest)
    write_json(run/'quality_check.json',manifest)
    write_json(TARGET/'record_id_aliases.json',aliases)
    write_json(TARGET/'label_schema.json',json.loads((SOURCE/'label_schema.json').read_text()))
    readme=f'''# Güncel Türkçe guardrail — caption'lardan yaş işareti kaldırıldı

**{manifest['safe']} safe + 500 sexual adayı = {manifest['total']} kayıt.**
Kullanıcının isteğiyle “yetişkin” sözcüğü bütün aktif caption/metin alanlarından
kaldırıldı. Özne olarak tek başına kullanıldığı yerlerde “kişi” bırakıldı.
Noktalama ve ilk harfler düzeltildi. Diğer yaş sıfatları değiştirilmedi.
Yetişkinlik doğrulaması kaynak metadata'sında korunur; modele yalnız `text` verilir.
Metadata'yı girdiye birleştirme.

Sözcük kaldırılınca aynı kaynak grubunda eşdeğer hale gelen
{len(oldrows)-len(rows)} safe kayıt birleştirildi. Eski kimlik bağlantıları
`record_id_aliases.json` ile korunur. 500 çiftin tamamı aynı grup/split'te kalır.
Önceden var olan iki farklı kaynak grubunun train içi metin tekrarı korunmuştur;
splitler arası metin veya grup çakışması yoktur. Gerçek kişi kimliği doğrulanmadı.

`pairs_500.jsonl`, `safe_counterparts_500.jsonl`, `sexual_candidates_500.jsonl`,
`new_359.jsonl` ve `paired_view_1000.jsonl` temizlenmiş görünümlerdir.
Çift görünümündeki 1.000 satır tam split dosyalarında zaten vardır; tekrar ekleme.
500 sexual etiket önceki gibi inceleme bekleyen önerilerdir. Etiket/maskeler
değiştirilmedi; maskeli BCE gereği sürer. Query kaynakları train'e alınmadı;
önceden görülmüş query adayları bağımsız nihai test değildir.

Önceki sürüm arşiv/provenans kaynağıdır; bu sürüm aktif eğitim girdisi taslağıdır.
Eğitim başlatılmadı. `dataset_manifest.json` sayımları ve kontrolleri içerir.
'''
    (TARGET/'README.md').write_text(readme,encoding='utf-8')
    (run/'README.md').write_text(readme+'\nİnceleme: `review.html`, `pairs_500.txt`, `pairs_500.csv`.\n',encoding='utf-8')
    latest={'run':run.relative_to(ROOT).as_posix(),'dataset':TARGET.relative_to(ROOT).as_posix()}
    write_json(ROOT/'results/LATEST_PAIRED_DATASET.json',latest)
    write_json(ROOT/'results/LATEST_CAPTION_500.json',latest)
    print(json.dumps({k:v for k,v in manifest.items() if k not in {'source_split_hashes','safe_labels','safe_label_mask'}},ensure_ascii=False))


if __name__=='__main__':
    main()
