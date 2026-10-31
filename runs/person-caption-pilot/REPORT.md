# Kişi caption'ı için Grok prompt denemeleri — 30 Ekim 2026

## Sonuç

Grok (`grok-4.7`) ile üç farklı prompt denendi. Toplam üç başarılı API isteğinde
12 karşıt çift / 24 ham caption döndü. Yapısal/yaş kontrollerinden geçen 10 çift /
20 caption yerel ModernBERT ile skorlandı. Son turdaki dört çift, önceki
`sexual_only_20.txt` dosyasındaki birinci şahıs yorumlarından farklı olarak kısa,
üçüncü şahıs, kıyafet ağırlıklı kişi tarifleridir.

Son turun 8 caption'ı `latest_pairs.jsonl` ve `latest_pairs.txt` içindedir.
Tüm turlar `review.html`, `review.csv`, `captions.txt` ve `scored.jsonl` içindedir.
`review.csv` içindeki `human_decision` ve `human_notes` alanları insan incelemesi için boştur.
Kaynaklar ve önceki deneyler değiştirilmedi; model eğitilmedi.

## Kullanıcının terminal denemelerinin yorumu

- Tarafsız etek, mini etek, tayt, straplez, dekolte, kapri, dar pantolon ve beden
  yapısı tarifleri bu deneyin etiket politikasında safe kabul edilir. Giysinin
  türü veya darlığı tek başına cinsel etiketin gerekçesi değildir.
- Aynı yüz tarifinde kıyafet yokken `SEXUAL_CONTENT_ADULT=0.178146`; yalnızca
  tayt eklenince `0.988007`, etek eklenince `0.910647`, kapri eklenince
  `0.758148` görülüyor. Bunlar kullanıcının paylaştığı terminal çıktılarıdır;
  bu raporda o sorgular yeniden çalıştırılmadı.
- Paylaşılan nesneleştirici metinler tarafsız kıyafet tariflerinden ayrılır.
  Bir gözlemcinin cinsel haz için kişiyi bedene indirgemesi cinsel anlam taşır.
  Ancak yaş belirsiz veya çocuk sinyalli metinler yetişkin pozitif üretiminin
  kaynaklarına alınmadı.
- Öpüşme, romantik ilgi ve tek başına çekicilik belirsizliği, açık cinsel niyet
  ile eşitlenmemeli. Şiddet ve diğer kategoriler bu cinsel veri pilotundan ayrıdır.

## Promptlar nasıl değişti?

1. `prompt-v1.txt`: Aynı yetişkinden güvenli ve cinsel varyant istendi. Çıktı
   kişi tarifine yaklaştı ancak partner, öpüşme ve romantik yakınlık içerdi.
   Pozitifler kesin etiket olarak kabul edilmedi. İlk doğrulamanın harf duyarlı
   yaş karşılaştırması, “orta yaşlı” → “Orta yaşlı” farkı nedeniyle iki çifti
   eledi. Kontrol ikinci turdan önce normalize metin karşılaştırmasına çevrildi;
   ilk turun ham çıktısı ve elenme kaydı korundu, geriye dönük kabul yapılmadı.
2. `prompt-v2.txt`: Tek kişi, aynı kıyafet, belirgin cinsel niyet veya
   nesneleştirme istendi. Sekiz aday geçti. “olarak sunulur”, “grafik olmayan
   biçimde” gibi prompttan taşan yapay ifadeler çıktı. Bu tur final veri olarak önerilmez.
3. `prompt-v3.txt`: Yüz detayları kısaltıldı; yapı, saç, üst/alt giysi,
   ayakkabı, eşya ve eylem sıralaması istendi. Kadın ve erkeklerde hem cinsel
   niyet hem nesneleştirme örnekleri yer aldı. Sekiz aday geçti.

## Son turun ölçümleri

| Çift | Güvenli varyantın kıyafeti | Güvenli unsafe | Güvenli sexual | Cinsel varyant sexual |
|---|---|---:|---:|---:|
| Kaynak 1 | Dekolteli bluz, mini etek | 0.415324 | 0.887091 | 1.000000 |
| Kaynak 4 | Straplez üst, tayt | 0.952726 | 0.999523 | 1.000000 |
| Kaynak 3 | Tişört, kot pantolon | 0.009000 | 0.118573 | 1.000000 |
| Kaynak 8 | Gömlek, pantolon | 0.007694 | 0.004652 | 0.999981 |

Genel karar `unsafe` üzerinden okunur. Cinsel kategori skoru ayrı bir sigmoid
çıktısıdır. Son turda iki tarafsız kıyafet caption'ının cinsel skoru 0.5 üzerindedir;
bunlardan straplez/tayt örneğinin genel unsafe skoru da yüksektir. Örnekler
küçük ve hedefli seçildiği için bu tablo genel hata oranını ölçmez.

## Asistanın semantik ön incelemesi

Son turdaki dört güvenli varyant tarafsız kişi/giysi tarifleridir. Dört pozitifin
cinsel gerekçesi kıyafet değildir: ikisinde açık cinsel ilişki teklifi,
ikisinde kişiyi cinsel haz için kullanılacak bedene indirgeyen niteleme vardır.
Hiçbiri grafik eylem betimlemesi içermez. Kaynaklarda bulunmayan giysiler,
beden yapısı ve eylemler sentetik eklemelerdir; gerçek fotoğraf bilgisi sayılmaz.

Son tur daha yakın olsa da üretim kalitesi sınırlıdır: iki nesneleştirme
örneğinde aynı “cinsel haz için kullanılacak bir araç” kalıbı tekrarlanıyor.
Son erkek niyet örneğindeki “açık bir seks teklifini söylemektedir” ifadesi de
doğal bir görsel caption'a göre yapaydır. Cinsel teklif görselden güvenilir
biçimde çıkarılabilen bir nitelik değildir; bunlar moderasyon metni varyantıdır.
Bu örnekler bütünüyle görselden türeyen caption veri kümesi diye sunulmamalı.
Tüm `review_status` değerleri `pending` kalır. Asistan ön incelemesi insan
onayının yerine geçmez ve önerilen sınıflar kesin eğitim etiketi değildir.

## Eğitim verisine geçmeden önce

Bu 8 örnek bir prompt pilotudur. Aynı dört kaynak üzerinde üç tur olduğundan
train/test başarısı ölçmez. Aynı kişi/kaynak ve tüm varyantları aynı split'te
kalmalı; orijinal test kümesi üretime veya prompt seçimine sokulmamalı.
Bu pilotta yalnız sızıntı denetiminden geçen `train` kaynakları kullanıldı.
Gerçek kişi kimlikleri kaynakta bulunmadığından kişi düzeyinde ayrım garanti edilmez.

Kıyafet terimleri hem safe hem sexual örneklerde bulunmalı. Cinsel pozitiflerde
yalnız birkaç sabit kelimeyi tekrar etmek modelin yeni kelime kısayolları
öğrenmesine yol açabilir. Daha geniş üretim için insan incelemesi sonrası
farklı cümle yapıları, kişi yapıları, giysiler ve kaynaklar gerekir. Şüpheli
örnekler ayrı review grubunda tutulmalı. Bu pilotun etiketleri diğer 9 kategori
için doğrulanmış negatif etiketler olarak otomatik kullanılmamalı.

## API kaydı ve yeniden çalışma

Üç başarılı istek: 5.415 input token ve 5.250 output token; output sayacı içindeki
reasoning ayrıca toplanmadı. Her isteğin `cost_in_usd_ticks` değeri 0 döndü;
bu gerçek hesap faturasının sıfır olduğu iddiası değildir. Otomatik retry yok.
İlk ağ denemesi yerel ağ kısıtlamasında başarısız oldu; kaydı
`round-1-network-error` klasöründe korundu. Ağ erişimiyle üç başarılı istek yapıldı.

Her turun `request.json` dosyası anahtarsız tam prompt/şema/ayar kaydıdır.
`event.json` kullanım, süre ve doğrulamayı; `response.json` ham yapılandırılmış
adayları; `candidates.jsonl` kontrollerden geçen kayıtları tutar.
İstek kaydı bulunan aynı tur tekrar gönderilmez. Bir timeout'ın sunucuda
işlenip işlenmediği kesin bilinemez; kayıt silerek tekrar çalıştırmayın.

Yalnız mevcut çıktıları yeniden skorlamak API çağrısı yapmaz:

```powershell
.\.venv\Scripts\python.exe -m reid_guardrail.person_caption_pilot score
```

45 çevrimdışı test geçti. Son turda dört çift / sekiz aday kaynak yaşı,
kaynak kimliği, kanıt alıntısı, birebir hold-out çakışması ve token sınırı
kontrollerinden geçti. Bu kontroller semantik doğruluk garantisi değildir.
