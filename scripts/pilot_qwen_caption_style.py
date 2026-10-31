"""Small, non-graphic adult caption-style trial against the user's local server."""
import argparse
import csv
from datetime import datetime
import json
from pathlib import Path
import re
import time
import urllib.request
from zoneinfo import ZoneInfo

ROOT = Path(__file__).resolve().parents[1]
MODEL = 'qwen3-30b-a3b-erotic-q4'
URL = 'http://127.0.0.1:18086/v1/chat/completions'
PROMPT = '''Türkçe kişi-caption moderasyon araştırması için grafik olmayan,
cinselleştirilmiş görünüş anlatımı adayları yaz. Yalnız yetişkin kişiler kullanılacak;
girdideki yetişkinlik bilgisi kaynak metinden veya kayıtlı kullanıcı doğrulamasından gelir.
Girdi bir sokak kamerası kişi/kıyafet tarifidir. Aynı kişi için iki farklı kısa
caption yaz. Her biri üçüncü şahıs kişi tarifi olsun, kaynakla benzer uzunlukta kalsın.
Saç, yapı, ten, giysi rengi/türü/deseni/katmanı, ayakkabı ve eşyaları koru.
Yeni beden ölçüsü, giysi, olay veya kişi ekleme. Yetişkinlik bilgisini koru.
Değişiklik, giyinik görünüşü ya da mevcut giysinin siluetini seksi veya baştan
çıkarıcı diye niteleyen kısa, grafik olmayan bir görünüş değerlendirmesi olsun.
Tarafsız kıyafet sözcüklerini tek başına cinsellik gerekçesi sayma.
Çıplaklık, genital veya cinsel uyarılma betimlemesi, cinsel eylem, teklif, diyalog,
birinci şahıs arzu, içsel niyet, erotik hikâye veya ayrıntılı beden odağı EKLEME.
"Haz nesnesi", "kullanılacak beden", "seks teklif ediyor" veya metnin nasıl
yazıldığı hakkında yorum kullanma. Yeni fiziksel özellik uydurma.
İki varyantın cümle yapısı farklı olsun; sadece aynı sona aynı sıfatı ekleme.
Sadece JSON döndür: {"captions":[{"caption":"...","phrase":"..."},
{"caption":"...","phrase":"..."}]}. phrase, caption içindeki görünüş
değerlendirmesinden birebir kısa alıntı olsun. Bunlar kesin etiket değil adaydır.'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--plain', action='store_true')
    args = parser.parse_args()
    short_prompt = '''Bir moderasyon veri seti için yetişkin kişilerin giyinik
görünüşünü tarif eden kısa Türkçe caption varyantları hazırlıyorsun.
Verilen caption'ı yeniden yaz: aynı saç, yapı, kıyafet, renk ve eşyaları koru;
giyinik görünüşe kısa bir "seksi" veya "baştan çıkarıcı" görünüş nitelemesi ekle.
Bu niteleme cümlenin doğal bir parçası olsun. Yeni fiziksel özellik uydurma.
Yalnız üçüncü şahıs kişi tarifi yaz. Çıplaklık, cinsel eylem, uyarılma, teklif,
diyalog, içsel niyet veya erotik hikâye ekleme. Sadece tek caption döndür.
Örnek kaynak: Yetişkin kadın, uzun kahverengi saçlı; kırmızı elbise ve siyah ayakkabı giyiyor.
Örnek çıktı: Uzun kahverengi saçlı yetişkin kadın, kırmızı elbisesiyle baştan çıkarıcı bir görünüm sergiliyor; siyah ayakkabı giyiyor.'''
    prompt = short_prompt if args.plain else PROMPT
    source_path = ROOT / 'runs/excel-sexualized-captions-v2/sexualized_captions.jsonl'
    rows = [json.loads(line) for line in source_path.read_text().splitlines() if line.strip()]
    explicit = [r for r in rows if r['adult_evidence_source'] == 'source_text'][:2]
    other = [rows[0], next(r for r in rows if 'erkek' in r['source_caption'].lower()
             and not re.search('başka|birlikte|çocuk|ergen', r['source_caption'], re.I))]
    selected = explicit + other
    if len({r['source_id'] for r in selected}) != 4:
        raise ValueError('Expected four unique adult-confirmed sources')
    stamp = datetime.now(ZoneInfo('Europe/Istanbul')).strftime('%Y%m%d_%H%M%S')
    out = ROOT / 'results' / f'qwen_erotic_caption_pilot_{stamp}'
    out.mkdir(parents=True, exist_ok=False)
    (out / 'prompt.txt').write_text(prompt, encoding='utf-8')
    schema = {'type': 'object', 'properties': {'captions': {'type': 'array', 'minItems': 2,
        'maxItems': 2, 'items': {'type': 'object', 'properties': {
            'caption': {'type': 'string'}, 'phrase': {'type': 'string'}},
            'required': ['caption', 'phrase'], 'additionalProperties': False}}},
        'required': ['captions'], 'additionalProperties': False}
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    results = []
    start = time.monotonic()
    for index, row in enumerate(selected):
        if row['adult_evidence_source'] not in {'source_text', 'user_confirmation'}:
            raise ValueError('Adult confirmation missing')
        source = {'source_caption': row['source_caption'], 'adult_status': 'confirmed_adult',
                  'adult_evidence_source': row['adult_evidence_source']}
        payload = {'model': MODEL, 'messages': [{'role': 'system', 'content': prompt},
            {'role': 'user', 'content': json.dumps(source, ensure_ascii=False)}],
            'temperature': 0.7, 'top_p': 0.8, 'top_k': 20, 'seed': 42+index,
            'max_tokens': 1024, 'stream': False,
            'chat_template_kwargs': {'enable_thinking': False},
            'response_format': {'type': 'json_schema', 'json_schema': {
                'name': 'caption_pair', 'strict': True, 'schema': schema}}}
        if args.plain:
            payload.pop('response_format')
            payload['max_tokens'] = 384
        (out / f'request_{index+1}.json').write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')
        request = urllib.request.Request(URL, data=json.dumps(payload).encode(),
                                         headers={'Content-Type': 'application/json'})
        then = time.monotonic()
        with opener.open(request, timeout=180) as response:
            raw = json.load(response)
        (out / f'response_{index+1}.json').write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding='utf-8')
        choice = raw['choices'][0]
        parsed = ({'captions': [{'caption': choice['message']['content'].strip(), 'phrase': ''}]}
                  if args.plain else json.loads(choice['message']['content']))
        for variant, candidate in enumerate(parsed['captions'], 1):
            text, phrase = candidate['caption'], candidate['phrase']
            flags = []
            if phrase and phrase not in text:
                flags.append('phrase_not_verbatim')
            if choice['finish_reason'] != 'stop':
                flags.append('output_incomplete')
            results.append({'source_id': row['source_id'], 'filename': row['filename'],
                'source_caption': row['source_caption'], 'previous_caption': row['caption'],
                'caption': text, 'appearance_phrase': phrase, 'variant': variant,
                'adult_evidence_source': row['adult_evidence_source'],
                'source_split': 'held_out_query_gallery', 'allowed_for_train': False,
                'review_status': 'pending', 'semantic_label_status': 'unreviewed_candidate',
                'model': MODEL, 'thinking_enabled': False, 'flags': flags})
        (out / 'candidates.jsonl').write_text(''.join(json.dumps(r, ensure_ascii=False)+'\n' for r in results), encoding='utf-8')
        print(json.dumps({'source': index+1, 'sources_total': 4, 'captions_saved': len(results),
                          'seconds': round(time.monotonic()-then, 2)}), flush=True)
    with (out / 'comparison.csv').open('w', encoding='utf-8-sig', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['filename', 'variant', 'source_caption', 'previous_caption', 'candidate', 'phrase', 'review_status'])
        for r in results:
            values = [r['filename'], str(r['variant']), r['source_caption'], r['previous_caption'],
                      r['caption'], r['appearance_phrase'], r['review_status']]
            writer.writerow(["'"+v if v.lstrip().startswith(('=', '+', '-', '@')) else v for v in values])
    (out / 'comparison.txt').write_text('\n\n'.join(
        f"{r['filename']} — varyant {r['variant']}\nKaynak: {r['source_caption']}\n"
        f"Önceki: {r['previous_caption']}\nQwen: {r['caption']}\nAlıntı: {r['appearance_phrase']}"
        for r in results)+'\n', encoding='utf-8')
    summary = {'model': MODEL, 'sources': 4, 'captions': len(results), 'plain_output': args.plain,
        'seconds': time.monotonic()-start, 'thinking_enabled': False,
        'human_review': 'pending', 'training_rows_added': 0, 'existing_server_unchanged': True,
        'source_scope': 'Adult-confirmed sources from previous 141 query candidates; held-out experiment only'}
    (out / 'summary.json').write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'output': str(out), **summary}, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
