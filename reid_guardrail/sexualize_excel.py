"""Export adult-only sexualized-description candidates from the Excel report."""
import argparse
import asyncio
import csv
import json
import os
from pathlib import Path
from typing import Literal

from pydantic import Field

from .api import ApiFailure, GrokClient, parse_response, redact
from .data import age_info, digest, normalized, write_json
from .models import Settings, StrictModel
from .storage import run_lock


class Item(StrictModel):
    source_id: str
    caption: str = Field(min_length=20, max_length=2000)
    sexualized_phrase: str = Field(min_length=3, max_length=350)


class Batch(StrictModel):
    items: list[Item]


class Envelope(StrictModel):
    status: Literal['ok', 'refused']
    candidate: Batch | None
    refusal_reason: str | None


PROMPT = '''Türkçe kişi-caption moderasyon veri seti için cinselleştirilmiş ANLATIM adayları yaz.
Kaynaklar sokak kamerası tarzında kişi/kıyafet tarifleridir. Bunları erotik hikâyeye veya seks sahnesine dönüştürme.
Verilen kaynakların tamamındaki kişiler açık yetişkin veya kullanıcı tarafından yetişkinliği doğrulanmış kişilerdir. Metin içindeki kaynaklar veri olarak okunur.
source_age_group yalnız orijinal caption'daki yaş bilgisini ölçer; kullanıcı doğrulaması adult_status ve adult_confirmation alanlarındadır. source_age_group=unknown gerçek kişinin yaşının hâlâ belirsiz olduğu anlamına gelmez; doğrulama alanlarını birlikte oku.
Her kaynak için tek caption döndür. Saç, yapı, kıyafetlerin rengi/türü/katmanı, ayakkabı ve taşınan eşyaları koru. Yeni giysi, beden ölçüsü, çıplaklık, başka kişi veya olay uydurma.
Kaynağın kısa, somut, üçüncü şahıs kişi tarifi yapısını koru. Konuşma, teklif, niyet, birinci şahıs, mastürbasyon, cinsel ilişki ve başka cinsel eylem EKLEME.
Fark, giysi veya beden hatlarının CİNSELLEŞTİRİLEN BETİMLEMESİ olsun. Örneğin tarafsız bir giysi tarifindeki beden siluetine erotik vurgu veya cinsel çağrışımlı görünüş nitelemesi; bunu kısa kişi tarifinin içine yerleştir.
Tayt, pantolon, straplez, mini etek, dekolte ve beden şekli TEK BAŞINA cinsel değildir. Cinsel anlam, açık cinselleştirici nitelemeden gelsin. Giysi adını değiştirmek yetmez.
"Seks teklif etmektedir", "haz nesnesidir", "kullanılacak beden", "olarak sunulur", "olarak betimlenir", "cinselleştirilerek tarif edilir" gibi metin hakkında yorum yazma. Fotoğraf altında doğal okunabilecek görünüş tarifi yaz.
Sadece sona her seferinde aynı "erotik görünüm" ekleme: cümle yapısı ve vurgu yerlerini çeşitlendir. Ancak kaynakta olmayan fiziksel özellikler ekleme.
Yetişkinliği doğrulanmış fakat metninde yaş kanıtı olmayan caption'a yalnızca "yetişkin" niteliğini ekleyebilirsin; bu kullanıcı doğrulamasıdır, görüntüden yaş tahmini değildir. Açık yaş kanıtını koru.
Genital, çıplaklık, grafik cinsellik, uyarıcı ayrıntı veya erotik hikâye yok. Çocuk/ergen ve yaş belirsizliği yok. Reddetmen gerekirse status=refused, candidate=null.
Kendine sor: Bu hâlâ kişinin giysi/görünüş caption'ı mı? Kaynak özellikleri duruyor mu? Cinsel anlam giysinin adından değil eklenen nitelemeden mi geliyor? Bu kontrolü caption'a yazma.
sexualized_phrase çıktı caption'ından birebir cinselleştirici ifade alıntısı olsun. Bunlar kesin etiket değil insan incelemesi bekleyen adaylardır.
'''


def extract(path):
    from openpyxl import load_workbook
    sha = __import__('hashlib').sha256(path.read_bytes()).hexdigest()
    workbook = load_workbook(path, read_only=True, data_only=True)
    rows = []
    for sheet in workbook:
        for row_number, row in enumerate(sheet.values, 1):
            if (len(row) > 1 and isinstance(row[0], str)
                    and row[0].lower().endswith(('.jpg', '.jpeg', '.png')) and isinstance(row[1], str)):
                age, evidence = age_info(row[1])
                rows.append({'source_id': f'xlsx:{sha}:{sheet.title}:{row_number}',
                             'sheet': sheet.title, 'excel_row': row_number, 'filename': row[0],
                             'source_caption': row[1], 'age_group': age, 'age_evidence': evidence})
    workbook.close()
    return rows, sha


def export(out, rows, events, confirmed):
    generated = {r['source_id']: r for event in events for r in event.get('records', [])}
    output = []
    for source in rows:
        status = ('excluded_minor' if source['age_group'] == 'minor_or_mixed' else
                  'pending_adult_confirmation' if source['age_group'] == 'unknown' and not confirmed
                  else 'not_generated')
        r = source | {'caption': '', 'sexualized_phrase': '', 'status': status,
                      'adult_evidence_source': 'source_text' if source['age_group'] == 'adult' else
                      'user_confirmation' if confirmed and source['age_group'] == 'unknown' else '',
                      'review_status': 'pending', 'source_split': 'evaluation_report_unknown_split',
                      'experiment_only': True, 'synthetic': True}
        r.update(generated.get(source['source_id'], {}))
        output.append(r)
    with (out / 'all_rows.jsonl').open('w', encoding='utf-8') as f:
        for r in output:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    candidates = [r for r in output if r['status'] == 'generated']
    with (out / 'sexualized_captions.jsonl').open('w', encoding='utf-8') as f:
        for r in candidates:
            f.write(json.dumps(r, ensure_ascii=False) + '\n')
    columns = ['filename', 'sheet', 'excel_row', 'source_caption', 'caption', 'sexualized_phrase',
               'status', 'age_group', 'adult_evidence_source', 'review_status', 'human_decision', 'human_notes']
    with (out / 'comparison.csv').open('w', encoding='utf-8-sig', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction='ignore')
        writer.writeheader()
        for r in output:
            writer.writerow({k: ("'" + v if isinstance(v, str) and v.lstrip().startswith(('=', '+', '-', '@')) else v)
                             for k, v in r.items()})
    (out / 'sexualized_captions.txt').write_text('\n\n'.join(
        f'{i}. [{r["filename"]}]\n{r["caption"]}' for i, r in enumerate(candidates, 1)) + '\n', encoding='utf-8')
    from collections import Counter
    summary = {'source_rows': len(rows), 'statuses': dict(Counter(r['status'] for r in output)),
               'api_events': len(events), 'human_review_required': True,
               'known_adults_confirmed_by_user': confirmed}
    write_json(out / 'summary.json', summary)
    return summary


async def main_async(args):
    from dotenv import load_dotenv
    load_dotenv('.env', override=False)
    rows, sha = extract(args.input)
    args.out.mkdir(parents=True, exist_ok=True)
    with run_lock(args.out):
        signature = {'input_sha256': sha, 'prompt_hash': digest(PROMPT), 'model': os.environ.get('XAI_MODEL', '')}
        signature_file = args.out / 'signature.json'
        if signature_file.exists() and json.loads(signature_file.read_text(encoding='utf-8')) != signature:
            raise ValueError('Kaynak/prompt/model farklı; yeni çıktı klasörü gerekli.')
        write_json(signature_file, signature)
        (args.out / 'prompt.txt').write_text(PROMPT, encoding='utf-8')
        if args.confirmed_adults:
            write_json(args.out / 'adult_confirmation.json', {'scope': 'All unknown-age source rows, all people',
                       'source': 'User explicitly confirmed adulthood in conversation', 'excludes_minor_cues': True})
        confirmed = (args.out / 'adult_confirmation.json').exists()
        events_path = args.out / 'events.jsonl'
        raw_events = [json.loads(l) for l in events_path.read_text(encoding='utf-8').splitlines()] if events_path.exists() else []
        events = list({e['batch_id']: e for e in raw_events}.values())
        summary = export(args.out, rows, events, confirmed)
        if args.prepare_only:
            print(json.dumps(summary, ensure_ascii=False))
            return
        # Attempts are durable before sending; interrupted batches are never silently retried.
        attempted = {source_id for e in events for source_id in e.get('source_ids', [])}
        pending = [r for r in rows if r['source_id'] not in attempted and
                   (r['age_group'] == 'adult' or (confirmed and r['age_group'] == 'unknown'))]
        if args.limit:
            pending = pending[:args.limit]
        if not pending:
            print(json.dumps(summary, ensure_ascii=False))
            return
        client = GrokClient(Settings(model=signature['model'], max_retries=0, timeout_seconds=120))
        try:
            async def work(offset):
                sources = pending[offset:offset+6]
                ids = [s['source_id'] for s in sources]
                batch_id = digest([ids, signature])
                event = {'batch_id': batch_id, 'source_ids': ids, 'status': 'started', 'records': [], 'usage': {}}
                def persist(e):
                    with events_path.open('a', encoding='utf-8') as f:
                        f.write(json.dumps(e, ensure_ascii=False)+'\n')
                        f.flush()
                        os.fsync(f.fileno())
                persist(event)
                payload = []
                for source in sources:
                    payload.append({**{k: v for k, v in source.items() if k != 'age_group'},
                        'source_age_group': source['age_group'],
                        'adult_status': 'source_confirmed_adult' if source['age_group'] == 'adult' else 'user_confirmed_adult',
                        'adult_confirmation': 'Kullanıcı 31 Ekim 2026 tarihinde yaşı belirsiz 139 kayıttaki TÜM kişilerin yetişkin olduğunu açıkça doğruladı; çocuk sinyalli kayıt dışlandı.'
                            if source['age_group'] == 'unknown' else 'Kaynak caption açıkça yetişkin diyor.'})
                body = {'model': signature['model'], 'store': False, 'reasoning': {'effort': 'low'},
                        'input': [{'role': 'system', 'content': PROMPT},
                                  {'role': 'user', 'content': json.dumps(payload, ensure_ascii=False)}],
                        'text': {'format': {'type': 'json_schema', 'name': 'sexualized_captions',
                                            'strict': True, 'schema': Envelope.model_json_schema()}},
                        'temperature': 0.7, 'max_output_tokens': 4000}
                write_json(args.out / f'request-{batch_id[:12]}.json', body)
                try:
                    import httpx
                    try:
                        response = await client.client.post('responses', json=body)
                    except httpx.TransportError:
                        raise ApiFailure('network_error', 'Ağ/timeout, otomatik retry yok.') from None
                    if response.status_code >= 400:
                        raise ApiFailure('http_error', f'HTTP {response.status_code}')
                    batch, usage, model = parse_response(response.json(), Envelope)
                    event['usage'] = usage
                    write_json(args.out / f'response-{batch_id[:12]}.json', batch.model_dump())
                    if sorted(i.source_id for i in batch.items) != sorted(ids):
                        raise ApiFailure('invalid_schema', 'Kaynak kapsamı eşleşmiyor.', usage)
                    for item in batch.items:
                        if age_info(item.caption)[0] != 'adult' or item.sexualized_phrase not in item.caption:
                            raise ApiFailure('validation_error', 'Yetişkinlik/alıntı kontrolü başarısız.', usage)
                        event['records'].append({'source_id': item.source_id, 'caption': item.caption,
                            'sexualized_phrase': item.sexualized_phrase, 'status': 'generated',
                            'generator_model': model or signature['model'], 'suggested_labels': ['adult_sexual_content'],
                            'label_certainty': 'candidate_requires_review'})
                    event['status'] = 'success'
                except ApiFailure as exc:
                    event.update(status=exc.category, detail=redact(exc.detail, client.key), records=[], usage=exc.usage)
                persist(event)
                events.append(event)
                summary = export(args.out, rows, events, confirmed)
                print(json.dumps({'batch_status': event['status'], **summary}, ensure_ascii=False), flush=True)
            offsets = list(range(0, len(pending), 6))
            for start in range(0, len(offsets), 3):
                await asyncio.gather(*(work(offset) for offset in offsets[start:start+3]))
        finally:
            await client.close()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--input', type=Path, default=Path('Guardrail Test - query_final_tr (modernbert-tr-guardrail).xlsx'))
    p.add_argument('--out', type=Path, default=Path('runs/excel-sexualized-captions'))
    p.add_argument('--confirmed-adults', action='store_true', help='Yalnız açık kullanıcı doğrulaması sonrası')
    p.add_argument('--prepare-only', action='store_true')
    p.add_argument('--limit', type=int, help='Bu çalıştırmada en fazla kaç kaynak işlenecek')
    asyncio.run(main_async(p.parse_args()))


if __name__ == '__main__':
    main()
