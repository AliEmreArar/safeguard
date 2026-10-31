# Yeni sohbet / ajan için devir notu

Güncelleme: 31 Ekim 2026, Europe/Istanbul.

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
