# Yeni sohbet / ajan için devir notu

Güncelleme: 31 Ekim 2026, Europe/Istanbul.

## Aktif sürüm: “yetişkin” işareti caption'lardan kaldırıldı

Kullanıcı sözcüğün etiket ipucu olmaması için bütün caption'lardan
“yetişkin” sözcüğünü kaldırmamı istedi. İşlem tamamlandı.

- Aktif veri: `datasets/person_guardrail_tr_v4_no_adult_marker_review/`.
- Geçerli inceleme çıktıları: `results/caption_marker_removed_20261031_180558/`.
  İki `LATEST_*` işaretçisi bu sürümü gösterir.
- 1.145 girdi caption'ı değiştirildi; aktif caption/metin alanlarında kalan
  sözcük sayısı **0**. `text`, `caption`, çift safe/sexual metinleri, Türkçe
  kaynak caption alanları ve gömülü legacy caption alanları temizlendi.
  Diğer yaş sıfatları kaldırılmadı. Tek başına özne olan “yetişkin” yerine
  “kişi” bırakıldı; noktalama ve ilk harfler düzeltildi.
- Yaş doğrulama bilgileri metadata'da, geçmiş kaynaklar arşivde korunur.
  İngilizce kaynak metadata'sı model girdisi değildir. Modele yalnız `text` ver.
- Kelime kaldırılınca aynı split/grupta eşdeğer hale gelen 323 safe kayıt
  birleştirildi; `record_id_aliases.json` eski kimlikleri yeni kanonik kimliğe
  bağlar. Çiftlerin bağlantıları yeniden kuruldu.
- Güncel toplam: **3.144 safe + 500 sexual adayı = 3.644 kayıt**.
  Train: 2.003+326=2.329; validation: 250+33=283;
  test: 546+46=592; challenge: 295+45=340; legacy_review: 50+50=100.
- 500 çift, dengeli 1.000 satırlık çift görünümü ve yeni 359 aday görünümü
  korunur; bütün aktif görünümler temizlendi. Etiket ve maskeler değişmedi.
  Çiftlerin split/grup/metin/kimlik bağları ve 359 alıntı eşleşmesi doğrulandı.
- Yeni caption alanlarına bu kelimeyi yeniden ekleme. Önceki üretim ve çift
  betikleri arşiv sürümlerini yeniden oluşturabilir; etkin çıktıya geçmeden
  `scripts/remove_adult_caption_marker.py` aşaması veya aynı temizlik uygulanmalı.
- V1/V2/V3 ve eski sonuç klasörleri provenans arşividir; aktif girdiler V4'tür.
  İnceleme durumu ve test bağımsızlığı sınırlamaları sürer. Eğitim başlamadı.

## En güncel sürüm: 500 safe / sexual aday çifti

Kullanıcı 500 sexual adayın cinsel olmayan karşılıklarının safe etiketiyle
eklenmesini istedi. `scripts/build_safe_sexual_pairs.py` bu çalışmayı tamamladı.

- Güncel veri seti: `datasets/person_guardrail_tr_v3_paired_review/`.
- Çalışma ve kullanıcı inceleme dosyaları:
  `results/safe_sexual_pairs_20261031_175130/`.
  `results/LATEST_PAIRED_DATASET.json` güncel yolları gösterir.
- 500 adayın nötr kaynak caption'ları alındı. Pozitif tarafta eklenen,
  kullanıcı tarafından doğrulanmış yetişkinlik bilgisi safe tarafta da korundu;
  yalnız bu sözcüğün sınıf ipucuna dönüşmesi azaltılmak istendi.
  Pozitiflerden birkaç sözcük silerek nötr metin oluşturulmadı.
- Bu 500 nötr metnin 33'ü zaten sette birebir vardı, aynı kayıt kimlikleri
  kullanıldı. 467 yeni nötr karşılık safe olarak eklendi.
- Toplam: **3.467 safe + 500 sexual adayı = 3.967 kayıt**.
  Train: 2.294+326=2.620; validation: 282+33=315;
  test: 546+46=592; challenge: 295+45=340; legacy_review: 50+50=100.
- `pairs_500.jsonl` çift bağlantılarını ve iki metni içerir. Ayrıca
  `safe_counterparts_500.jsonl`, `sexual_candidates_500.jsonl` ve
  `paired_view_1000.jsonl` vardır. Sonuncusu 500 safe + 500 adaydır;
  bunlar tam split dosyalarında zaten bulunur, tekrar birleştirilmemelidir.
- Her çiftin iki tarafının kayıt kimliği, metni, grup/split eşitliği ve
  bidirectional pair_ids bağlantıları doğrulandı. Safe vektörleri 11 sıfır,
  maskeleri 11 birdir. Pozitif önerileri ve bilinmeyen hazard maskeleri korundu.
- Kaynak/grup eşleştirmeleri kusursuz minimal çift garantisi değildir;
  özellikle eski 141 örnekte semantik kaynak korunumu ayrıca incelenmelidir.
- Genel sette orijinal safe metinler ile yetişkinlik eklenmiş nötr karşılıklar
  birlikte bulunur. Eğitimde kaynak/çift bazında örnekleme düşünülebilir;
  aynı kaynak varyantlarını istemeden tekrar tekrar ağırlıklandırma.
- Önceki Türkçe sette bulunan iki train-içi birebir metin tekrarı korundu.
  Bu adım yeni birebir metin tekrarı eklemedi. Splitler arası grup ve
  normalize birebir metin çakışması yok. Gerçek person_id doğrulanmadı.
- V2 kaynak dosyalarının hash'leri değişmedi. Query kaynaklı 141 örnek train'e
  alınmadı; bağımsız pozitif nihai test eksikliği sürer. Sexual etiketler
  inceleme bekler; eğitim veya yeni model/API üretimi çalıştırılmadı.

## En son tamamlanan çalışma: 500 aday / 3.500 kayıt

Kullanıcı mevcut 141 caption'ın üslubuyla, çevrilmiş safe kaynaklardan yeni
adayları Codex'in hazırlamasını istedi. Hedef 500 olduğundan 359 yeni aday
hazırlandı (141+360=501 olurdu). Kullanıcı ayrıca seçilmiş 3.000 caption'daki
herkesin yetişkin olduğunu açıkça doğruladı; kapsam ve kaynak hash'leri
`results/caption_500_codex_20261031_174400/adult_confirmation.json` içindedir.
Bu doğrulama tüm 109.993 kaynak kayda genellenmez; çocuk/ergen sinyalleri
üretimden dışlanmaya devam eder.

- Geçerli çalışma: `results/caption_500_codex_20261031_174400/`.
  `results/LATEST_CAPTION_500.json` güncel yolu gösterir. Daha önceki
  `174052` ve `174235` klasörleri bu işin ara taslaklarıdır.
- Yeni adaylar 359 ayrı safe kaynak ve 359 ayrı önek grubundan gelir:
  326 train, 33 validation. 180 kadın, 159 erkek, 20 belirsiz kaynak ipucu.
- Yeni metinler Codex tarafından yerelde yazılmış ifade envanteriyle
  bileşimsel üretildi; Qwen/Grok/API çıktısı veya tek tek bağımsız LLM örneği
  değildir. Envanter `style_inventory.json` içinde, üretim yöntemi satırlarda
  açıktır. Kalıp korelasyonu olasılığı ve semantik insan incelemesi gereği sürer.
- 359 yeni caption'da kaynak sözcüklerinin sırası ve varlığı denetlendi.
  Bu kontrol bütün semantik veya Türkçe anlatım sorunlarını kanıtlamaz.
- Önceki 141 kaydın metadata'sında Grok üreticisi yazıyordu; kullanıcı bunları
  Codex'in oluşturduğunu söylemiş olsa da kayıtlı üretici değiştirilmedi.
- `new_359.txt`, `sexual_500.txt`, `comparison.csv`, `review.html` kullanıcı
  incelemesi içindir. 500 farklı normalize aday metni vardır.
- Birleşik sürüm: `datasets/person_guardrail_tr_v2_review/`.
  Train: 2.000 safe + 326 aday = 2.326; validation: 250+33=283;
  test: 500+46=546; challenge: 250+45=295; legacy_review: 50 aday.
  Toplam 3.500 kayıt. Grup ve normalize birebir metin split çakışması yok.
- Query kaynaklı eski 141 aday train'e alınmadı. Safe test/challenge ile
  grup eşleşenler aynı split'te, diğer 50'si `legacy_review` içinde.
  Önceden prompt/üslup kararlarına etki eden bu kayıtlar bağımsız nihai test
  sayılmaz; maruz kalmış safe grup satırları da işaretlendi.
- Pozitiflerin hedefleri **öneridir**, inceleme bekler. Yalnız sexual indeks 5
  için önerilen hedef 1/mask 1; genel unsafe ve diğer hazard hedefleri
  bilinmeyen olarak mask 0. Maskeli BCE gerekir, standart Trainer bu maskeyi
  otomatik uygulamaz. `training_eligible=false`, `ready_for_training=false`.
- Orijinal 3.000 safe dosya ve eski 141 aday dosyası değiştirilmedi.
  Eğitim veya yeni model/API üretimi/skorlaması başlatılmadı.

## Yeni oturumdaki kullanıcı kararları — 31 Ekim 2026

- Çalışma ve hedef veri dili **Türkçe** olarak kesinleştirildi.
- Şimdilik yalnız `person_guardrail_safe_v1` içindeki **3.000 seçilmiş safe
  örnek** çevrilecek; bütün 109.993 kaynağın çevirisi istenmedi.
- Bu proje için kullanıcının güncel GPU seçimi fiziksel **5**'tir. Üst
  dizindeki önceki GPU 7 kuralı bu açık talebin yerini tutmaz.
- Yalnız proje klasörüne yazılacak ve mevcut conda ortamında çalışılacak;
  başka ortamlar, ortak model deposu ve diğer süreçler değiştirilmeyecek.
  Ayrıntılar yerel `AGENTS.md` dosyasında.
- Yerel Qwen3.5-4B küçük çeviri denemesinde ayrıntı hataları ve tekrar yaptı;
  `results/translate_tr_pilot_20261031_170100/` eğitime kullanılacak veri değildir.
  Bu ilk denemede mevcut `translate` ortamının Python'u kullanılmıştı; kullanıcı
  ortam sınırını sonradan belirtti. Bu ortama paket kurulmadı/değiştirilmedi.
- Ortak depoda `qwen3.8:27b-q4_K_M` bulundu. Ağırlıklar salt okunur:
  `/mnt/aselsanlab_ds/proje3/ollama_models/`. Bağımsız çalıştırıcı yalnız
  proje `.cache/ollama/` dizinine açıldı; global kurulum yapılmadı.
- GPU 5 UUID: `GPU-df6a0bca-a90a-9d22-c5c1-69cf30f6f8b6`.
  Qwen sunucusu yalnız `127.0.0.1:18085` üzerinde; günlük
  `results/qwen38_gpu5_server.log`. Mevcut base Python'u kullanan çeviri betiği:
  `scripts/translate_tr_local.py`.
- Qwen3.8 çeviri çalışmasının dosyaları:
  `results/translate_tr_qwen38_20261031_165000/`. Gerçek tamamlanma sayısını
  `progress.json`, `summary.json` ve `translations.jsonl` üzerinden kontrol et;
  bu paragraf tamamlanmış çeviri veya insan incelemesi iddiası değildir.
- Kullanıcı daha sonra Qwen3.8 ile thinking kapalı toplu çeviriyi açıkça istedi;
  küçük çeviri hatalarının bu aşamada kabul edilebilir olduğunu belirtti.
  **Asıl 3.000 satırlık çalışma**:
  `results/translate_tr_3000_qwen38_20261031/`. Pilot klasörüyle karıştırma.
  Aynı Qwen3.8 Q4_K_M modeli GPU 5 üzerinde 32 paralel yuva ile çalışıyor;
  ilerleme `progress.json`, kalıcı sonuçlar `translations.jsonl` içindedir.
  Kullanıcı Qwen3.8 ile devam edilmesini istedi; Qwen3.6'ya geçilmedi.
  İşlem bitince `python3 scripts/finalize_tr_dataset.py` kaynak eşleşmelerini
  doğrular ve `datasets/person_guardrail_safe_tr_v1/` dizinine dışa aktarır.
- **Çeviri ve dışa aktarma tamamlandı:** Türkçe dizinde 2.000 train, 250
  validation, 500 test ve 250 challenge vardır. 3.000 kaynak metni/kimliği,
  dosya/satır, split/grup, 11 boyutlu etiket ve label mask eşleşmesi doğrulandı.
  İngilizce kaynak hash'leri değişmedi; splitler arası birebir Türkçe metin
  çakışması yok. 41 kayıt otomatik terim kontrolünde işaretlendi; bunlar
  kesin çeviri hatası sayısı değildir (ör. brown hair → kumral).
  Tüm 3.000 çeviri korundu, insan incelemesi yapılmış sayılmadı.
  Yeni istek hatası yok; guardrail skorlama/eğitim çalıştırılmadı.
  Qwen3.8 sunucusu GPU 5 üzerinde açık bırakıldı.
- Eğitim henüz başlamayacak. Sexual veriyi çoğaltma ve fine-tuning sonraki
  aşamalardır. İngilizce başlangıç skorlarını Türkçe skorları gibi kullanma.
- Kullanıcı sonradan kendi kurup çalıştırdığı Qwen erotic modelini denememi
  istedi. Mevcut `qwen3-30b-a3b-erotic-q4` (Qwen3 30B-A3B Q4_K_M)
  `127.0.0.1:18086` üzerinde GPU 4'teydi; bu mevcut servise istek gönderildi,
  GPU yerleşimi/ayarları veya çalışan sohbeti değiştirilmedi. Dört yetişkinliği
  doğrulanmış query kaynağında iki küçük tur, toplam 12 aday üretildi.
  İlk JSON turu çoğunlukla kaynağı tekrarladı; kısa düz metin turu görünüş
  nitelemesi ekledi ama bazı kaynak özelliklerini düşürdü. Sonuç ve inceleme:
  `results/qwen_erotic_caption_pilot_20261031_173023/REVIEW.md`.
  İlk tur: `results/qwen_erotic_caption_pilot_20261031_172947/`.
  Train'e veya safe sete ekleme yapılmadı; bütün adaylar inceleme bekler.

Aşağıdaki bölümler önceki teslimatın kayıtlarıdır; dil, ortam ve GPU bakımından
yukarıdaki güncel kullanıcı kararları esas alınır.

## Amaç ve kullanıcının istediği caption biçimi

Kullanıcı `ytu-ce-cosmos/modernbert-tr-guardrail` modelini person-captioning
alanına uyarlamak istiyor. Tayt, etek, straplez, dekolte, dar pantolon ve
tarafsız beden tarifleri modelde yüksek `SEXUAL_CONTENT_ADULT` skoru
doğurabiliyor. Bu kelimeler tek başına sexual etiketinin gerekçesi olmayacak.
Hedef, bu yanlış pozitifleri azaltırken gerçek hedef pozitifleri kaçırmamak.

Kullanıcıyla birkaç kez düzeltildikten sonra kabul edilen üretim biçimi:

- Kısa, üçüncü şahıs, sokak kamerasındaki kişiyi tarif eden caption.
- Saç, yapı, giysinin rengi/türü, katman, ayakkabı ve eşya gibi kaynak özellikleri korunur.
- Pozitif adayı, görünüş/giysi/beden hatları üzerinde cinselleştirici anlatım kullanır.
- Seks teklifi, diyalog, içsel niyet, birinci şahıs arzu yorumu veya cinsel eylem sahnesi eklenmez.
- “Haz nesnesidir”, “kullanılacak beden”, “seks teklif etmektedir”, mastürbasyon/birliktelik sahneleri önceki denemelerde hedefi kaçırdı. Bunlara dönme.
- “Erotik/seksi/baştan çıkarıcı” gibi nitelemeler içeren çıktılar kesin doğru etiket sayılmadı. Bazıları sınırdadır; insan incelemesi ve net etiket yönergesi gerekir. Tek bir tetik sözcüğü ezberletecek veri üretme.

## Şu anki durum

**Safe alt veri seti hazır; sexual pozitifler bu sete eklenmedi; eğitim başlamadı.**
Kullanıcının son veri hazırlama talebi önce safe seçimi, daha sonra sexual
örnekleri çoğaltıp eklemekti. Sonraki GitHub yükleme ve bu devir notu talepleri tamamlanmaktadır.

Repo: https://github.com/AliEmreArar/safeguard

Dal: `main`. Veri/kodların yüklendiği commit: `09ffe10`.
Güncel commit'i `git log -1` ile kontrol et; bu not daha sonraki bir commit'te olabilir.
Yerel çalışma klasörü: `C:\Users\emre\Desktop\Asellab\safeguard`.

## Kaynak person verileri

Kullanıcı `data/` altındaki caption'ların tamamının safe olduğunu belirtti:

| Dosya | Kayıt |
|---|---:|
| `data/train_final.jsonl` | 99.993 |
| `data/query_final.jsonl` | 3.250 |
| `data/gallery_final.jsonl` | 6.750 |

Şema: `filename`, `caption`. Metinler **İngilizce**.
Türkçeye çevrilsin mi sorusu soruldu ama yanıt gelmedi; özgün dil korunarak
ilerlendi. Kullanıcının açıkça İngilizceyi tercih ettiği varsayılmamalı.
Çeviri yapılmadı; yeni dilde çalışılacaksa seçim/skorlar yeniden değerlendirilmeli.
Eski `merged_captions.json` ise yüz tarifleri içerir: 4.800 train, 1.199 test.
Yeni person kaynaklarıyla aynı veri kümesi değildir.

## Hazırlanan safe veri seti

Ana dizin: `datasets/person_guardrail_safe_v1/`.
Önce bu dizindeki `README.md`, `dataset_summary.json`, `quality_check.json`
ve `augmentation_policy.json` dosyalarını oku.

| Bölüm | Satır | Kaynak / amaç |
|---|---:|---|
| `train.jsonl` | 2.000 | Yalnız train kaynak grupları |
| `validation.jsonl` | 250 | Train kaynağından grup bazında önceden ayrıldı |
| `test.jsonl` | 500 | Query/gallery'den rastgele, skor kullanılmadan seçildi |
| `challenge.jsonl` | 250 | Ayrı query/gallery gruplarında kıyafet/beden odaklı test |

Train seçimi: 800 özellikle model yanlış pozitiflerinden seçilmiş örnek,
600 kıyafet/beden kontrolü, 600 normal kontrol. Kontrol grupları da yüksek
skor alabilir; bunlar seçim kategorileri, model-doğru kategorileri değildir.
6.000 train adayı ve 1.000 değerlendirme örneği olmak üzere 7.000 caption
yerel modelle skorlandı. Skorlar etiketleri değiştirmedi.

Train havuzunda hold-out metniyle çakışan 278 satır ve train içi 1.019 tekrar
çıkarıldı. Dosya adının `_` öncesi kısmı grup anahtarıdır. Bu gerçek person_id
olarak doğrulanmadı; ihtiyatlı bir gruplama yöntemidir. Yayımlanan split'ler
arasında önek ve normalize birebir metin çakışması yoktur. Yakın anlamsal
tekrar veya gerçek kişi düzeyinde sızıntısızlık garanti edilmiş değildir.

`source_group_assignments.json` bütün kaynak öneklerinin ayrım kaydıdır.
Yeni varyantlar/pozitifler kaynaklarıyla aynı split'te kalmalıdır.
`selection_preview.txt` örnekleri ve skorları okunabilir biçimde gösterir.
`scoring_pool.jsonl` ve `model_scores.jsonl` seçim kayıtlarıdır, ek train satırları değildir.

### Önemli başlangıç ölçümü

500 güvenli İngilizce doğal test caption'ının 478'inde sexual, 418'inde
genel unsafe skoru 0.5 üzerindedir. Bu yüzden sorunu yalnız kıyafet
kelimelerine bağlama: dil ve caption alanına geçiş de etkili olabilir.
Bu sonuç Türkçe performans ölçümü değildir.

## Model ve etiket biçimi

Yerel model: `models/modernbert-tr-guardrail/` (~149,3 milyon parametre).
İndirme: `reid_guardrail/download_guardrail.py`; sabit revision bu dosyadadır.
Ağırlıklar GitHub'a yüklenmedi; yeniden indirilir. Uzak model kodu çalıştırılmaz.

Çıkış sırası yerel config'ten doğrulandı:

```text
0 unsafe
1 VIOLENT_CRIMES
2 NON_VIOLENT_CRIMES
3 HATE_DISCRIMINATION
4 HARASSMENT_OFFENSIVE
5 SEXUAL_CONTENT_ADULT
6 CSAE
7 SELF_HARM_SUICIDE
8 INJECTION_JAILBREAK
9 MISINFORMATION_POLITICAL
10 PRIVACY_VIOLATION
```

11 bağımsız sigmoid / çok etiketli BCE yapısıdır; softmax değildir.
`unsafe` ile `SEXUAL_CONTENT_ADULT` ayrı skorlar ve ayrı karar eşikleridir.
Mevcut safe satırlar `text`, 11 float sıfırdan oluşan `labels`, tamamen bir
olan `label_mask` ve kaynak/seçim metadata'sı içerir. Safe etiketinin kaynağı
kullanıcı beyanıdır; model tahmini değildir.

İlerideki pozitiflerin diğer hazard etiketlerini kontrol etmeden hepsini 0
yapma; bilinmeyen çıkışlarda maskeli loss gerekebilir. Standart Trainer
`label_mask` alanını otomatik uygulamaz. Sexual adayı ile genel unsafe
kararını da etiket yönergesi olmadan eşitleme. Diğer yeteneklerin
unutulmamasını ayrıca değerlendir.

## Sexual çıktıların durumu ve kritik sızıntı bulgusu

Son kabul edilen üretim biçimine ait ana çıktı:
`runs/excel-sexualized-captions-v2/`.

- `sexualized_captions.txt`: 141 caption adayı.
- `comparison.csv`: kaynak/aday yan yana.
- `sexualized_captions.jsonl`: kaynak kimliği, aday, cinselleştirici alıntı ve metadata.
- `all_rows.jsonl`: dışlanan kayıt dahil 142 kaynak.
- `README.md`, `quality_check.json`: yöntem, kısıtlar ve kontroller.

Kaynak: `Guardrail Test - query_final_tr (modernbert-tr-guardrail).xlsx`.
142 kayıttan `26682_2.jpg` açık erkek çocuk tarifidir; dönüştürülmedi.
2 kaynak açık yetişkin, 139'u yaş bakımından belirsizdi. Kullanıcı **bu
139 kayıttaki tüm kişilerin yetişkin olduğunu açıkça doğruladı**; bu bilgi
metadata'da kullanıcı beyanı olarak saklandı. Bu doğrulama bütün yeni
99.993 train kaydına genellenemez. Safe etiketi de yetişkinlik kanıtı değildir.
Çocuk/ergen sinyalli kaynaklardan cinsel varyant üretilmez.

**141 adayın tamamı `data/query_final.jsonl` kaynaklarından geliyor.
Mevcut ayrımı korurken bu adayları train'e EKLEME.** İncelenmiş olanlar
held-out değerlendirmeye ayrılabilir. Önceden prompt/eşik/etiket seçimine
etki etmiş örnekler nihai bağımsız test sayılmaz; gerektiğinde yeni test ayır.
Yeni train pozitiflerini ayrım kaydında `train` olan kaynaklardan üret.

Grok ile 24 başarılı istek kullanıldı. Otomatik retry yoktu. Dört alıntı
alanında yazım/harf/ek farkı yerelde düzeltildi; caption metinleri değiştirilmedi.
Ham yanıtlar korunur. Bütün pozitif adaylar `review_status=pending`.
Henüz bu setin bütün satırları insan tarafından etiketlenmedi.

Eski denemeler de repoda, fakat uygun final veri olarak varsayma:
`runs/person-caption-pilot/`, `runs/person-caption-visual/`,
`runs/sexual-only-20-user-adult-confirmed/`.
İlk ikisinde kullanıcının sonradan istemediği teklif/eylem/metin yorumu
üslupları vardır. `sexual-only-20` önceki asistanın yerelde yazdığı örneklerdir;
README bunu açıklar, Grok çıktısı diye sunma.
`runs/excel-sexualized-captions/` ilk reddedilen istek kaydıdır, final çıktı v2'dir.

## Ortam, komutlar ve testler

Python 3.12, `.venv`. Etkinleştirme zorunlu değil:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-inference.txt
.\.venv\Scripts\python.exe -m reid_guardrail.download_guardrail
.\guardrail.bat
.\.venv\Scripts\python.exe -m pytest -q -m "not live"
```

`guardrail.bat`: art arda metin girerek yerel test; `/exit` ile çıkar.
`--text "..."` ve `--threshold 0.7` destekler.

Safe seti yeniden üretme: `python -m reid_guardrail.build_safe_dataset all`
(sanal ortam Python'unu kullan). Kaynaklar aynıysa 7.000 kayıtlık skor
önbelleğini kullanır. Kaynak veya model ağırlıkları değişirse yeni çıktı
klasörü kullan; eski skorları yeni modelin sonucu gibi kullanma.

Kodlar: `reid_guardrail/build_safe_dataset.py`, `sexualize_excel.py`,
`person_caption_pilot.py`, `test_text.py`.
Önce mevcut kodu oku; yeni üretimde eski kaynak/split/üslup varsayımlarını
körü körüne kullanma. Başlamış/tamamlanmış API isteklerini yeniden gönderme.

Son kontrol: 45 çevrimdışı test geçti. 3.000 yayımlanan safe kaydın
kaynak-satır/metin/görsel eşleşmesi, 11 boyutlu etiketleri ve split ayrımı
doğrulandı. Etiketlerle modele forward verilerek sonlu BCE loss alındı;
backward/optimizer/eğitim çalıştırılmadı. Seçilen train metinlerinin en uzunu
154 token, bütün yayımlanan satırlar 256 token altındadır.

Yerel GPU kontrolü: RTX 4060 Ti **8 GB** (16 GB değil).
Kurulu Torch `2.15.0+cpu`; CUDA kullanılamıyor. GPU eğitimi için uyumlu CUDA
kurulumu gerekir. Kullanıcıya 16 GB'ın kısa caption'lar için makul olduğu,
8 GB ile küçük batch ve checkpointing denenebileceği söylendi; ölçülmüş
eğitim belleği veya eğitim süresi yoktur.

## Anahtarlar ve yetki bağlamı

`.env` yereldir, Git dışında. Anahtarı okumaya/dökmeye/yazışmaya gerek yok;
kod `XAI_API_KEY` ve `XAI_MODEL` kullanır. Önceki çalışmada `grok-4.7` ayarlıydı.
Başka makinede `.env.example` üzerinden kullanıcı yerelde doldurmalıdır.
GitHub'da anahtar/model ağırlığı/sanal ortam yoktur. Veri/kodlar yüklenmeden
önce 139 dosyada anahtar taraması yapıldı, eşleşme bulunmadı.

Kullanıcı bu proje kapsamında Grok API ile veri üretimine izin verdi.
Son talep safe seçimi ve kaydetmeydi; henüz yeni büyük sexual üretimi veya
eğitim başlatılmadı. Kapsama uygun küçük somut denemelerle ilerle; eski
yanlış üslubu tekrar çoğaltma. Kullanıcı verilerin ve sexual çıktıların
GitHub'a yüklenmesini açıkça istedi; yükleme tamamlandı. Bu notun GitHub'a
eklenmesi de kullanıcının devam edebilme talebinin parçasıdır.

## Sıradaki işler

1. Gerekirse kullanıcıyla hedef dil ve pozitif etiket yönergesini netleştir.
2. Safe alt kümesi / kaynak grup ayrımını koru. Yeni train pozitifleri için
   yetişkinliği doğrulanmış uygun train kaynaklarını seç.
3. Kabul edilen kişi-caption üslubunda küçük yeni örnekler üret; doğal
   caption ve etiket kalitesini görmeden büyük üretime geçme. Safe/sexual
   taraflarda aynı giysi kelimelerini ve çeşitli cümle yapılarını bulundur.
4. İncelenmiş pozitifleri doğru split ve label mask'leriyle ekle; pozitif
   validation/test de ayır. Mevcut safe-only setle doğrudan eğitime başlama.
5. CUDA ortamını kurup küçük eğitim pilotunda bellek ve adım süresini ölç.
6. Giysi challenge yanlış pozitif oranı ile sexual recall'ı birlikte ölç;
   diğer hazard'larda gerilemeyi de kontrol et. Testle eşik ayarlama.

Yeni sohbete kısa başlangıç mesajı:

> AliEmreArar/safeguard reposundaki DEVIR_NOTU.md dosyasını ve orada belirtilen güncel veri seti notlarını oku. Safe veri seçimi tamamlandı; train kaynaklarından, kabul edilen kişi-caption üslubunda sexual adayları hazırlama ve fine-tune veri setini tamamlama aşamasından devam edeceğiz. Henüz eğitim başlatma.
