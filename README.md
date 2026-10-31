# Türkçe ReID moderasyon verisi pilotu

## Güncel veri dosyaları — 31 Ekim 2026

- [Safe person veri seti ve formatı](datasets/person_guardrail_safe_v1/README.md): 2.000 train, 250 validation, 500 test ve 250 kıyafet challenge örneği. Kaynak İngilizce korunur; 11 çıkışlı modele uygun etiketler ve başlangıç skorları içerir. Sexual pozitifler henüz bu eğitim alt kümesine eklenmedi.
- [Seçilen safe örneklerin ön izlemesi](datasets/person_guardrail_safe_v1/selection_preview.txt).
- [141 cinselleştirilmiş caption adayı](runs/excel-sexualized-captions-v2/sexualized_captions.txt), [kaynakla karşılaştırma CSV'si](runs/excel-sexualized-captions-v2/comparison.csv) ve [üretim notları](runs/excel-sexualized-captions-v2/README.md). Aday etiketleri insan incelemesi bekler; açık çocuk kaydı dışlandı.
- Kaynak person dosyaları `data/` altındadır. Query/gallery eğitim dışında tutulur. Önceki 141 sexual adayın tamamı query kaynaklı olduğundan train'e eklenmemelidir; yeni eğitim pozitifleri train kaynak gruplarından üretilmelidir.

## Kişi caption'ı için son prompt denemeleri

Önceki denemedeki teklif ve nesneleştirme cümleleri istenen caption biçimine
uygun bulunmadı. Sonraki [görsel caption denemesinin değerlendirmesi](runs/person-caption-visual/REVIEW.md)
ve [seçilmiş karşıt çift](runs/person-caption-visual/selected_pair.txt) burada.
Bu da küçük bir biçim pilotudur; diğer çıktılardaki sorunlar raporda açıkça belirtilir.

30 Ekim 2026'da Grok ile üç küçük prompt turu çalıştırıldı. Son turdaki dört
güvenli/cinsel karşıt çift [metin dosyasında](runs/person-caption-pilot/latest_pairs.txt),
tüm turlar ve yerel model skorları [inceleme ekranında](runs/person-caption-pilot/review.html).
[Deney raporu](runs/person-caption-pilot/REPORT.md) prompt değişikliklerini,
giysi kaynaklı yanlış pozitifleri ve kalan dil/çeşitlilik sorunlarını açıklar.
Etiketler insan incelemesi bekler; model eğitilmedi.

## Terminalde kendi metnini test et

Proje klasöründe PowerShell açıp çalıştır:

```powershell
.\guardrail.bat
```

Model bir kez yüklenir. `Metin >` satırına metnini yazıp Enter'a bas;
arka arkaya farklı metinler deneyebilirsin. Çıkmak için `/exit` veya Ctrl+C kullan.
API anahtarı gerekmez; metinler yerelde işlenir ve dosyaya kaydedilmez.

Tek metin ve isteğe bağlı karar eşiği:

```powershell
.\guardrail.bat --text "Mavi ceket giyen bir kişi."
.\guardrail.bat --threshold 0.7
```

Doğrudan Python komutu: `.\.venv\Scripts\python.exe -m reid_guardrail.test_text`.
Genel SAFE/UNSAFE kararı `unsafe >= 0.5` üzerinden verilir (eşik değiştirilebilir).
10 kategori skoru ayrıca gösterilir; kategori eşiğinin aşılması genel kararı değiştirmez.
Sigmoid skorları birbirinden bağımsızdır, toplamları 1 olmak zorunda değildir ve
kesin doğruluk / kalibre edilmiş olasılık anlamına gelmez. Token sınırını aşan
metinler sessizce kırpılmadan reddedilir.

Grok üzerinden kontrollü sentetik aday veri üretir. Kaynak JSON/JSONL'yi değiştirmez; model eğitmez. Her aday insan incelemesi bekler. Varsayılan çalışma ağsızdır. Canlı üretim yalnızca `--live` ile başlar.

## Başka bir bilgisayarda devam etme

Bu repo kodları, kaynak JSON/Excel dosyalarını, raporları ve üretilen adayları içerir. API anahtarı ve `.env` dosyası paylaşılmaz. Yaklaşık 600 MB model ağırlığı yeniden indirme komutuyla alınır.

Windows PowerShell'de (Python 3.11 veya üstü ve Git kurulu olmalı):

```powershell
cd "$HOME\Desktop"
git clone https://github.com/AliEmreArar/safeguard.git
cd safeguard
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m pytest -q -m "not live"
```

Mevcut sonuçları okumak veya ağsız test çalıştırmak için API anahtarı gerekmez. Yeni canlı üretim için `.env.example` dosyasını `.env` olarak kopyala, anahtarını yalnızca yerelde gir ve `XAI_MODEL=grok-4.7` ayarla. `.env` Git dışında kalır.

Son 20 cinsel nesneleştirme adayı:

- [İnceleme ekranı](runs/sexual-only-20-user-adult-confirmed/review.html)
- [20 caption metni](runs/sexual-only-20-user-adult-confirmed/sexual_only_20.txt)
- [JSONL](runs/sexual-only-20-user-adult-confirmed/sexual_only_20.jsonl) ve [CSV](runs/sexual-only-20-user-adult-confirmed/sexual_only_20.csv)

Bu 20 aday ek API çağrısı yapılmadan asistan tarafından yerelde yazıldı. Yetişkinlik bilgisi kullanıcının beyanı olarak metadata'da tutulur; kaynak caption'lar değiştirilmedi. Önerilen etiketler insan incelemesi bekler. Aynı dosyaları yeniden oluşturmak için `python scripts/create_sexual_only_20.py` çalıştırılabilir.

Yerel guardrail ölçümünü yeniden yapmak için:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-inference.txt
.\.venv\Scripts\python.exe -m reid_guardrail.download_guardrail
.\.venv\Scripts\python.exe -m reid_guardrail.excel_contrast score --out runs/excel-contrast-10
```

Tamamlanmış pilotların küçük SQLite durum dosyaları ve Excel deneyinin JSONL iş kayıtları repoda korunur. Aynı girdi, prompt, ayarlar ve çıktı klasörüyle devam edildiğinde tamamlanan işler yeniden API'ye gönderilmez. `state.sqlite3` ve `generation_events.jsonl` dosyalarını silmek veya yeni çıktı klasörü kullanmak bu korumayı ortadan kaldırır. `.gitattributes`, Windows'ta satır sonu dönüşümünün kaynak hash'lerini ve devam etme imzalarını değiştirmesini önler. Çalışma kilitleri, önbellekler ve model ağırlıkları repoya dahil değildir.

## Excel'den 10 kaynakla karşılaştırma

Son deney `runs/excel-contrast-10` klasöründedir. [Karşılaştırma ekranı](runs/excel-contrast-10/comparison.html), [CSV](runs/excel-contrast-10/comparison.csv) ve [açıklamalı rapor](runs/excel-contrast-10/REPORT.md) birlikte okunabilir. 10 Excel kaynağı üzerinden 10 Grok isteği yapıldı; `reasoning.effort=low`, paralellik 4 ve retry 0 ile üretim 20.6 saniye sürdü. 10 özgün metin, 10 nötr kıyafet varyantı, açık yetişkin kaynaklardan 2 sınır ve 2 nesneleştirme adayı ile kullanıcının verdiği 3 değişiklik toplam 27 metin olarak yerel guardrail modelinde ölçüldü. Ek kontroller için API çağrısı yapılmadı.

Excel'deki 142 ayrıntı kaydının yalnızca 2'si açık yetişkin bilgisi içeriyor. Bu nedenle 10 kaynağın tamamından cinsel pozitif üretilmedi. `daracık tayt` ve tarafsız beden ölçüsü otomatik block sayılmıyor; kullanıcının block önerisi ile uygulamanın allow/review önerisi ayrı alanlarda korunuyor. Modelin bütün bu metinlere yüksek cinsel skor vermesi doğru etiket oldukları anlamına gelmez.

Guardrail modeli `models/modernbert-tr-guardrail` içine indirildi; revision `b19585c4ae526f9539f7e3213f56624222c0526e`. `config.json` ile 11 etiket ve çok etiketli sigmoid çıktısı doğrulandı. Eğitim yapılmadı; `unsafe` ve `SEXUAL_CONTENT_ADULT` eşikleri ayrı okunur. Deney kaynaklarının split'i bilinmediğinden bu kayıtlar train olarak işaretlenmedi ve önceki train/test dosyaları değiştirilmedi.

Kurulum ve tekrar çalıştırma:

```powershell
python -m pip install -r requirements-inference.txt
python -m reid_guardrail.download_guardrail
python -m reid_guardrail.excel_contrast generate --dry-run
python -m reid_guardrail.excel_contrast generate --out runs/excel-contrast-10
$env:HF_HUB_OFFLINE="1"
$env:TRANSFORMERS_OFFLINE="1"
python -m reid_guardrail.excel_contrast score --out runs/excel-contrast-10
```

Mevcut klasördeki tamamlanmış 10 iş tekrar gönderilmez; prompt/kaynak değişirse yeni çıktı klasörü gerekir. Yeni `--out` ile generate çalıştırmak canlı API kullanımıdır. Model scoring aşaması yerel dosyalardan çalışır. Gerçek bir eğitim/test değerlendirmesi için yanlış pozitiflerden seçilmiş bu küçük deney ayrıca tutulmalıdır.

API'nin `cost_in_usd_ticks` alanı hem önceki hem bu küçük deneyde 0 dönmüştür. Rapordaki liste fiyatı hesabı gerçek hesap harcaması değildir; paneldeki 0 USD ile çelişen bir tahsilat iddiası yapılmaz. Önceki pilotun yerel kaydı 90 iş / 93 HTTP denemesidir; kullanıcının panelde gördüğü 367 isteğin kapsamı bu kayıtlarla doğrulanamadı.

## Kurulum (Windows PowerShell, Python 3.11+)

Proje klasöründe:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Etkinleştirme gerekmez; aşağıdaki komutlar sanal ortamın Python'unu doğrudan çağırır. Başka bir klasörden kurulu paket olarak kullanmak istersen `python -m pip install -e .` çalıştır.

## Anahtar ve model

Mevcut `.env` dosyanı koru. Henüz yoksa boş örneği kopyala:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
notepad .env
```

Dosyaya `XAI_API_KEY=` karşısında kendi anahtarını ve `XAI_MODEL=` karşısında hesabında kullanılabilir, structured output destekleyen güncel model kimliğini yerelde yaz. Anahtarı sohbet, komut satırı argümanı veya config dosyasına koyma. `.env` Git dışında tutulur. Uygulama canlı çalışmada `.env` yükler; mevcut ortam değişkenlerini değiştirmez. Dry-run `.env` okumaz ve anahtar istemez.

Model adı koda sabitlenmemiştir. Öncelik: `--model`, config `model`, `XAI_MODEL`. Canlı çağrı öncesi model adı zorunludur. API hostu sabit `https://api.x.ai/v1` adresidir; anahtarı başka bir sunucuya yönlendiren base URL ayarı yoktur.

## Veri incelemesi

```powershell
.\.venv\Scripts\python.exe -m reid_guardrail inspect --input merged_captions.json --evaluation "Guardrail Test - query_final_tr (modernbert-tr-guardrail).xlsx" --out reports
```

`reports/data_inspection.json` ve `.md` oluşur. Yerel Excel salt okunur işlenir. Online Google Sheets bağlantısına erişildiği iddia edilmez.

Bu klasörde doğrulanan bulgular:

- 5.999 kayıt: 4.800 train, 1.199 test; tüm kaynak etiketleri `["safe"]`.
- Alanlar yalnızca `caption`, `split`, `labels`; kişi/görsel kimliği yok.
- Train/test arasında birebir ortak **8 farklı caption** var. Bunların train kopyaları üretimden çıkarılır. Ek olarak normalize metin çakışmaları ve train içi tam tekrarlar ayıklanır. Üretime uygun 4.775 train kaydı kalır.
- İlk denetimde uygun kayıtların 1.832'si açık yetişkin, 2.917'si yaş belirsiz, 26'sı çocuk/ergen veya karışık yaş sinyalli bulundu. Bu sayımlar muhafazakâr kural tabanlı taramadır.
- Yerel Excel **query_final_tr.jsonl adlı 3.250 caption'lık başka bir kümeyi** özetler. Genel `unsafe >= 0.5` sayısı **142**, tüm veride `SEXUAL_CONTENT_ADULT >= 0.5` sayısı **1.330**. 1.330 sayısı genel unsafe tahmini değildir. Excel'deki gerçek etiket beyanı "Hepsi SAFE"; tam 3.250 tahmin satırı bulunmadığından özet değerler tüm örneklerden yeniden hesaplanmış değildir.

Dosya SHA256 + 1 tabanlı satır numarası ile `source_id` üretilir. Bu kimlik **person_id değildir**. Sağlanırsa gerçek `filename`, `image_id`, `person_id` ve diğer alanlar `source_metadata` içinde aynen korunur. Hold-out kümesiyle bu alanlardan biri çakışan train kaynakları dışlanır. Tam gerçek kişi kimlikleri olmadan kişi düzeyinde sızıntı doğrulanamaz.

## Ağsız dry-run

```powershell
.\.venv\Scripts\python.exe -m reid_guardrail generate --input merged_captions.json --config config.example.json --out runs/dry-run --dry-run
.\.venv\Scripts\python.exe -m reid_guardrail validate --input runs/dry-run/candidates.jsonl --source-file merged_captions.json --out runs/dry-run/validation.json
```

Varsayılan pilot 30 kaynak, 30 normal güvenli, 30 zor güvenli ve üç yetişkin cinsel konseptin her birinden 10 adaydır. Kaynaklar sabit seed ile karıştırılır, önce açık yetişkin kaynaklar seçilir. Yeterli uygun kaynak yoksa kota azaltılır ve eksik raporlanır; yaş bilgisi eklenmez. Bu seçimin çocuk güvenli örnekleri ana pilottan dışlayabileceği raporda belirtilir. Çocukların güvenli tariflerini kapsamak için ayrı güvenli üretim çalışması yapılabilir; yaş filtresi o kaynaklardan cinsel pozitif üretimine izin vermez.

Dry-run aynı şema, planlama, yaş/split doğrulaması, kalıcı kayıt ve dışa aktarma yolunu kullanır. **Yerel şablon fixture üretir; Grok çıktısı değildir ve canlı üretim kalitesini ölçmez.** `mode=dry_run`, `generator_model=offline-fixture-v1` ve doğrulama bayrağı taşır. Şablonlarda üslup çeşitliliği sınırlıdır; canlı prompttaki stil hedeflerinin başarıyla gerçekleştiği varsayılmaz. Bu kayıtlar eğitim verisi olarak otomatik kullanılmamalıdır.

## Küçük canlı pilot

Kullanıcı canlı pilotu açıkça istediğinde aşağıdaki komut kullanılır. Önce 3 kaynak / 9 adaylık canlı deneme:

```powershell
.\.venv\Scripts\python.exe -m reid_guardrail generate --input merged_captions.json --config config.example.json --out runs/live-small --live --sources 3 --quota normal_safe=3 --quota hard_safe=3 --quota objectification=1 --quota sexual_intent=1 --quota sexual_harassment=1
```

30 kaynak / 90 adaylık ilk canlı pilot:

```powershell
.\.venv\Scripts\python.exe -m reid_guardrail generate --input merged_captions.json --config config.example.json --model grok-4.7 --out runs/live-grok-4.7-pilot --live
```

`--model` ile `.env` modelini geçersiz kılabilirsin. API kullanım ücreti doğurur. 2026-10-27 tarihinde kullanıcı isteğiyle `.env` içindeki `XAI_MODEL` değeri `grok-4.7` yapıldı ve bir güvenli sentetik fixture ile canlı structured output testi geçti. Model adı [resmî model sayfasından](https://docs.x.ai/developers/models/grok-4.7) doğrulandı. Kullanıcının ayrıca açıkça onayladığı 30 kaynak / en fazla 90 adaylık canlı pilotun çıktı klasörü `runs/live-grok-4.7-pilot` olarak belirlendi. Test kaydı: `reports/live_api_test.json`. xAI model listesine anahtar ile sorgu gönderilmedi.

Canlı pilot tamamlandı: 90 işten 84 aday kaydedildi; 6 çıktı yaş kanıtı doğrulamasından elendi. Sonuçlar 30 normal güvenli, 30 zor güvenli, 8 nesneleştirme, 8 açık cinsel niyet ve 8 cinsel taciz adayıdır. Her yetişkin konseptinde 2 adaylık eksik korunur; kotayı tamamlamak için yaş filtresi gevşetilmedi veya ek üretim başlatılmadı. 84 aday kaynak dosyayla ayrıca doğrulandı ve hepsi insan incelemesi bekliyor. Yeniden çalıştırma 90 işi de atladı ve ek API çağrısı yapmadı. Bildirilen kullanım üzerinden tahmini pilot maliyeti $1.396936; timeout sonrası bildirilmeyen kullanım ve ayrı canlı pytest bu tahmine dahil değildir. Gerçek ayarlar `runs/live-grok-4.7-pilot/run_config.json`, doğrulama özeti `runs/live-grok-4.7-pilot/verification.json` içindedir.

24 yetişkin pozitif adayına yapılan asistan ön incelemesinde 7 aday için ayrıca REVIEW önerildi: bazı ifadelerde cinsel bağlam belirsiz, birinde hedef konsept farklı, birinde yeni bir kişiye yönelen taciz betimleniyor. Bu bulgular `semantic_review.json` içinde ve CSV/HTML'deki bağımsız inceleme alanlarında görünür. Üretici önerileri ayrı korunur; bu ön inceleme insan onayı veya kesin eğitim etiketi değildir. Diğer kayıtların semantik doğruluğu onaylanmış sayılmaz.

## Kesintiden devam

Aynı komutu aynı ayarlar ve `--out` ile tekrar çalıştır:

```powershell
.\.venv\Scripts\python.exe -m reid_guardrail generate --input merged_captions.json --config config.example.json --model grok-4.7 --out runs/live-grok-4.7-pilot --live
```

İş kimliği; kaynak dosyası/kaydı, konsept/dönüşüm hedefi, stil, çift bilgisi, istenen model, tüm üretim ayarları, mod, prompt sürümü ve prompt hash'ini kapsar. Girdi veya ayarlar değişirse aynı çıktı klasöründe devam engellenir; yeni bir klasör kullan. Aynı klasöre eşzamanlı iki süreç yazamaz.

Her sonuç SQLite transaction ile kalıcılaşır. Başarılı aday hemen JSONL'ye yazılır ve flush/fsync yapılır. Başlangıçta JSONL, SQLite'tan yeniden oluşturulur; yarım yazılmış JSONL satırı veya kayıt dosyası kaybı yeni çağrı doğurmaz. SQLite dosyası korunmalıdır. Tamamlanan işler, tekrarlar ve retler tekrar gönderilmez. Hatalı ağ/şema işleri yalnızca açık `--retry-errors` ile yeniden denenir; retler bu seçenekle de yeniden denenmez.

```powershell
.\.venv\Scripts\python.exe -m reid_guardrail generate --input merged_captions.json --config config.example.json --model grok-4.7 --out runs/live-grok-4.7-pilot --live --retry-errors
```

Ağ hatası, 429 ve 5xx için sınırlı backoff vardır; prompt değiştirilmez. **API yanıtının alınması ile yerel transaction arasındaki çok kısa kesinti aralığında sunucuda işlenmiş isteğin yeniden gönderilmeyeceği garanti edilemez.** Timeout sonrası tekrar da sunucu tarafında ek kullanım doğurabilir. Yerelde kalıcılaşan başarılı işler tekrar gönderilmez.

## İnsan incelemesi ve ayrı doğrulama

```powershell
.\.venv\Scripts\python.exe -m reid_guardrail validate --input runs/live-grok-4.7-pilot/candidates.jsonl --source-file merged_captions.json --out runs/live-grok-4.7-pilot/validation.json
.\.venv\Scripts\python.exe -m reid_guardrail export-review --input runs/live-grok-4.7-pilot/candidates.jsonl --out runs/live-grok-4.7-pilot/review-export
```

Üretim zaten inceleme dosyalarını oluşturur. Dışa aktarma komutu bunları yeniden üretir:

| Dosya | İçerik |
|---|---|
| `candidates.jsonl` | Şeması doğrulanmış sentetik adaylar, kaynak caption ve kimliği |
| `review.csv` | Excel uyumlu UTF-8 BOM; boş `human_decision`, `human_labels`, `reviewer`, `review_notes` |
| `review.html` | Kaynak ve aday yan yana incelenebilen, script içermeyen okunabilir görünüm |
| `pilot_report.json` / `.md` | Hedef/plan/aday/kararla eşleşen öneri kotaları, eksikler ve konsept örnekleri |
| `near_duplicates.json` | Eşik 0.88 karakter benzerliği; çift ilişkisi ve tarama kapsamı |
| `data_audit.json`, `plan.json` | Sızıntı, yaş, kaynak seçimi ve planlanmış işler |
| `events.jsonl`, `errors.jsonl` | Sonuç, ret, boş çıktı, şema, yerel doğrulama, ağ ve HTTP hata kategorileri |
| `state.sqlite3` | Devam etme için asıl kalıcı durum |

CSV formül enjeksiyonuna karşı metin hücrelerini korur; JSONL kaynak metnini aynen tutar. HTML, girdi metinlerini escape eder. CSV/HTML yeniden dışa aktarılırken insan düzenlemelerini üzerine yazmamak için ayrı bir `--out` klasörü kullan. Üretici hiçbir insan kararını içeri alıp otomatik eğitim etiketine dönüştürmez.

`suggested_labels` uygulamaya ait önerilerdir: `safe`, `adult_sexual_content`, `needs_review`. Bunlar ModernBERT sınıf indeksleri değildir. `target_decision`, `generator_decision`, `suggested_decision` ayrı tutulur; uyuşmazlık `review` olur. `content_safety` ile `task_relevance` ayrıdır. Tüm `review_status` değerleri `pending` kalır.

`validate --source-file` şema/yaş dışında gerçek kaynak eşleşmesini, kaynağın üretime uygunluğunu ve üretilen metnin hold-out ile tam çakışmasını da denetler. Yerel otomatik doğrulama **semantik etiket doğruluğunu kanıtlamaz**. İnsanın özellikle şunları incelemesi gerekir: paraphrase anlamı koruyor mu, yeni kıyafet doğru dönüşüm türüyle işaretli mi, sorgu doğal mı, ret/alıntı/olumsuzlama bağlamı doğru mu, cinsel hedef gerçekten block mu, safe/block üslup ve uzunlukları dengeli mi. Üreticinin `added_attributes` beyanı tek başına doğruluk garantisi sayılmaz.

Minimal çiftlerin `pair_id` alanı aynıdır. Bazı kaynaklar bağımsız sorgu üretir ve `pair_id=null` olur. Tüm varyasyonlar `train` kalır. Üretilen metinler hold-out tam eşleşmesine karşı yeniden taranır. Yakın tekrar raporu beklenen çift benzerliklerini de gösterir; semantik tekrar veya kişi düzeyi sızıntı sertifikası değildir. Büyük çalışmalarda en fazla 200.000 karşılaştırma yapılır ve `truncated` açıkça raporlanır. Test kaynağı API'ye gönderilmez; sentetik test üretilmez.

## Etiket ve yaş politikası

Tarafsız beden, kıyafet ve duruş ALLOW; göğüs baskısı/cebi, çapraz askı, tayt, etek, şort, külotlu çorap, dar paça, açık ceket, katmanlar ve tek başına güzel/yakışıklı/şık değerlendirmesi engelleme nedeni değildir. Açık yetişkin kaynaklarda belirgin cinsel nesneleştirme, açık cinsel niyet ve cinsel taciz BLOCK adayıdır. Belirsiz, imalı ve tek başına seksi gibi sınır örnekler REVIEW'dur. Nefret/siyaset/genel hakaret üretimi açılmamıştır.

Yaş filtresi açık sayısal yaş, yetişkin/orta yaşlı gibi kanıtlara bakar. Kadın, erkek, genç, kız veya oğlan tek başına yeterli değildir. Çocuk/ergen ya da karışık yaş sinyali pozitif üretimini engeller. Kaynağın yaş kanıtı çıktıda da korunmalıdır. Kural tabanlı tarama tüm örtük yaş imalarını anlayamaz; belirsiz ve birden fazla kişiyi içeren kaynaklar insan incelemesinde ayrıca kontrol edilmelidir. Çocuk/ergen cinsel pozitif üretimini açan bir seçenek yoktur.

## Açık komutla büyük üretim

İnsan pilot incelemesi tamamlandıktan sonra örneğin 300 kaynak / 900 aday:

```powershell
.\.venv\Scripts\python.exe -m reid_guardrail generate --input merged_captions.json --config config.example.json --out runs/live-large --live --large-run --sources 300 --quota normal_safe=300 --quota hard_safe=300 --quota objectification=100 --quota sexual_intent=100 --quota sexual_harassment=100
```

`--large-run` olmadan 30 kaynak veya 90 iş üzeri talepler reddedilir. Kotalar yeni çıktı klasöründe açıkça verilmelidir. Eksik kaynak kotası otomatik tekrar/yaş ekleme ile doldurulmaz. Paralellik varsayılan 2, timeout 90 saniye, retry en fazla 2'dir; config üzerinden sınırlı aralıklarda değiştirilebilir.

## Testler

API kullanmayan kritik testler:

```powershell
.\.venv\Scripts\python.exe -m pytest -q -m "not live"
```

Yaş kapısı, kaynak/test çakışması, kimlik sızıntısı, JSON/JSONL şeması, çıktı yaşı, tekrar önleme, bozuk JSONL'den onarma, devam etme, ayar değişikliği, retleri yeniden göndermeme, structured output istek gövdesi, API hata sınıfları ve anahtar redaksiyonu mock taşıma ile denetlenir.

Ücretli canlı test ayrıdır; varsayılan olarak atlanır. Çalıştırmak için anahtar/model ortamda mevcutken açıkça:

```powershell
$env:RUN_XAI_LIVE_TESTS="1"
.\.venv\Scripts\python.exe -m pytest -q -m live
Remove-Item Env:RUN_XAI_LIVE_TESTS
```

Bu test `.env` otomatik yüklemez; shell ortam değişkenlerini kullanır ve bir güvenli örnek için çağrı yapar. Gerçek anahtarı komut geçmişine yazmak yerine yerel ortamını güvenli şekilde yapılandır.

## API ve model referansları

2026-10-27 tarihinde resmî xAI belgelerinden API/SDK ve structured output kullanımı kontrol edildi:

- [Responses REST ve Python SDK örneği](https://docs.x.ai/developers/rest-api-reference/inference/responses)
- [Responses / Chat Completions karşılaştırması](https://docs.x.ai/developers/model-capabilities/text/comparison)
- [Structured outputs, JSON Schema ve Pydantic örneği](https://docs.x.ai/developers/model-capabilities/text/structured-outputs)
- [Model listesi](https://docs.x.ai/developers/models)
- [ModernBERT-TR Guardrail model kartı](https://huggingface.co/ytu-ce-cosmos/modernbert-tr-guardrail)

Bu proje SDK bağımlılığı yerine `httpx` ile resmî Responses REST uç noktasını kullanır. `text.format` içinde strict JSON Schema gönderilir, Pydantic ile yerelde tekrar doğrulanır, `store=false` ayarlanır. Resmî Python SDK örnekleri de incelendi; canlı entegrasyon `grok-4.7` ile bir güvenli fixture üzerinde sınandı. Üretim kullanım sayaçları kaydedilir. Grok 4.7 için 2026-10-27 tarihli [resmî fiyat snapshot'ı](https://docs.x.ai/developers/models/grok-4.7) ile standart kısa bağlam kullanımının tahmini maliyeti hesaplanır: milyon token başına normal girdi $2, cache girdisi $0.50, çıktı $6. Çıktı sayacının içindeki reasoning token'ları ikinci kez ücretlendirilmez. Diğer modeller veya doğrulanmamış uzun bağlam fiyatları için maliyet uydurulmaz. Tahmin fatura değildir; bildirilmeyen/timeout kullanımı ve ayrı canlı pytest dahil değildir. Mevcut canlı pytest kullanım sayaçlarını kalıcılaştırmaz.

ModernBERT kartı genel unsafe ve kategori skorlarını ayrı, çok etiketli sigmoid çıktılar olarak açıklar. Modelin gerçek `config.json` etiket eşlemesi bu teslimatta alınmadı/doğrulanmadı; dolayısıyla eğitim hedef vektörü oluşturulmadı. Veri üretimi için model ağırlıkları indirilmedi.
