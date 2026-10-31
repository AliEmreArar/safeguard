# Person guardrail: safe alt veri seti

Kaynak: kullanıcının tamamını safe olarak işaretlediği `data/train_final.jsonl`,
`data/query_final.jsonl`, `data/gallery_final.jsonl`. Kaynak metinler değiştirilmez.
**Dil İngilizcedir. Türkçe çeviri yapılmadı.** Mevcut Türkçe odaklı modelin
İngilizce caption'lara verdiği skorlar, bu dildeki hata seçimi içindir;
Türkçe caption performansı olarak yorumlanmamalıdır.

İlk ölçümde doğal testteki 500 güvenli İngilizce caption'ın **478'inde sexual**,
418'inde genel unsafe skoru 0.5 üzerindedir. Bu yüksek hata yalnız kıyafet
kelimelerine atfedilemez; dil ve caption alanına geçiş de araştırılmalıdır.
Bu veri seti Türkçe performans iyileşmesi kanıtı değildir.

## Dosyalar

- `train.jsonl`: 2.000 safe eğitim örneği; model yanlış pozitifleri, kıyafet/beden ve normal kontrolleri karışık.
- `validation.jsonl`: train kaynak gruplarından önceden ayrılan 250 safe doğrulama örneği.
- `test.jsonl`: query/gallery kaynaklarından rastgele seçilen 500 safe test örneği; her önek grubundan bir caption.
- `challenge.jsonl`: testten ayrı kaynak gruplarından 250 safe kıyafet/beden örneği. Kasıtlı zor test alt kümesidir; doğal dağılım değildir.
- `dataset_summary.json`: kesin sayımlar, seçim grupları, giysi ve cinsiyet ipuçları, başlangıç modelinin yanlış pozitif sayıları.
- `selection_preview.txt` / `selection_preview.jsonl`: seçim gruplarından örnekler ve skorlar.
- `label_schema.json`: yerel modelden okunan 11 etiketin sırası ve yapılandırma hash'i.
- `source_group_assignments.json`: gelecekteki varyantları da aynı split'te tutmak için bütün kaynak öneklerinin ayrımı.
- `augmentation_policy.json`: sonradan eklenecek sexual örnekler için ayrım ve etiket kuralları.
- `source_audit.json`, `input_signature.json`: kaynak sayıları, elenen tekrarlar ve dosya hash'leri.
- `scoring_pool.jsonl`, `model_scores.jsonl`: seçimin denetlenebilir havuzu ve yerel model skorları; bunlar ek eğitim satırları değildir.

## Etiket biçimi

Her JSONL satırında `text` girdidir. `labels`, modelin gerçek `id2label`
sırasındaki **11 float** değerden oluşur. Kaynakların tamamı kullanıcı
tarafından safe olarak etiketlendiği için bütün değerler `0.0`'dır.
Modelin yüksek skoru bu etiketleri değiştirmez.

Sıra: `unsafe`, `VIOLENT_CRIMES`, `NON_VIOLENT_CRIMES`, `HATE_DISCRIMINATION`,
`HARASSMENT_OFFENSIVE`, `SEXUAL_CONTENT_ADULT`, `CSAE`, `SELF_HARM_SUICIDE`,
`INJECTION_JAILBREAK`, `MISINFORMATION_POLITICAL`, `PRIVACY_VIOLATION`.

```json
{"text":"...","labels":[0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0,0.0],"label_mask":[1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0,1.0],"safety_label":"safe"}
```

Eğitimde `text` tokenize edilir; `labels` çok etiketli sigmoid/BCEWithLogitsLoss
hedefidir. Bu bir tek sınıflı softmax etiketi değildir. Diğer alanlar kaynak,
ayrım ve seçim metadata'sıdır; metne birleştirilmemelidir. Mevcut safe satırlarda
`label_mask` tamamen 1'dir. İleride bazı hazard etiketleri bilinmeyen pozitifler
eklenirse, `label_mask=0` konan çıkışların kayba katılmaması için maskeli BCE
uygulayan eğitim kodu gerekir; standart Trainer bunu otomatik yapmaz.

**Bu aşama safe alt kümesini hazırlar. Sexual pozitifler henüz eklenmedi;
tam fine-tune veri seti veya eğitime hazır iki sınıflı veri seti değildir.**
Pozitif validation/test örnekleri de ayrıca gereklidir. Şimdilik testlerde
yalnız yanlış pozitif oranı ölçülebilir, sexual recall/F1 ölçülemez.

## Seçim

Train kaynağından query/gallery ile metni çakışan satırlar ve normalize
tekrarlar çıkarılır. 6.000 adaylık havuz, kıyafet/beden odaklı ve diğer
caption'ları kapsar. 800 model yanlış pozitifi, 600 kıyafet/beden kontrolü,
600 normal kontrol hedeflenir; kota yetmezse farklı adaylarla tamamlama
`diversity_fill` olarak kaydedilir. Kesin dağılım özet JSON'dadır.
Kontrol grupları da yüksek skor alabilir; gruplar örneklerin seçilme yolunu
anlatır, kesin model-doğru/model-yanlış ayrımı değildir.

Yanlış pozitif seçimi için `SEXUAL_CONTENT_ADULT >= 0.5` veya `unsafe >= 0.5`
kullanılır; ikisi ayrı çıkışlardır. Skorlar yalnız train seçimini etkiler.
Validation, rastgele doğal test ve kıyafet challenge seçimleri skorlar
görülmeden sabitlenir. Kıyafet kategorileri ve cinsiyet sözcüğü ipuçlarıyla
seçim çeşitlendirilir. Bu ipuçları gerçek kişi kimliği/cinsiyet beyanı değildir.

Skorlama yalnız yerel modelde CPU ile yapılır. Metinler sessizce kırpılmaz.
Ham skorların 11'i de kaynak satırına kaydedilir; API kullanımı yoktur.

## Kaynak ayrımı ve ilerideki sexual üretim

Dosya adının `_` öncesi kısmı ihtiyatlı bir gruplama anahtarıdır. Bunun gerçek
person_id olduğu doğrulanmadı; kişi düzeyinde sızıntısızlık garantisi değildir.
Önek ve normalize birebir metin çakışması tüm yayımlanan split'ler arasında
kontrol edilir. Query/gallery grupları bütünüyle eğitim dışında tutulur.

Önceden Excel'den üretilen **141 sexual adayın tamamı query kaynağından gelir**.
Bunlar train'e eklenmemelidir. İnceleme sonrası yalnız kaynak gruplarına uygun
held-out değerlendirme için ayrılabilir. Test sonuçlarıyla prompt/etiket/eşik
ayarı yapıldıysa o örnekler nihai bağımsız test sayılmaz; yeni test gerekir.

Yeni eğitim pozitifleri `source_group_assignments.json` içinde `train` olan
kaynaklardan üretilmelidir. Safe etiketi yetişkinlik kanıtı değildir: cinsel
varyant üretmeden önce açık yetişkin kanıtı veya kullanıcı doğrulaması gerekir;
çocuk/ergen sinyalli kaynaklardan cinsel varyant üretilmez.
Aynı kaynak ve bütün varyantları aynı split'te kalır. Yeni pozitifte yalnız
sexual etiketi gözden geçirildiyse diğer hazard'lar otomatik 0 yapılmamalıdır.

## Tekrar üretme

```powershell
.\.venv\Scripts\python.exe -m reid_guardrail.build_safe_dataset all
```

Kaynak hash'leri aynıysa kaydedilmiş skorlar kullanılır; tekrar skorlama yapılmaz.
Kaynaklar değişirse yeni çıktı klasörü kullanılmalıdır. Model ağırlıkları
değiştirilecekse de eski skor klasörü kullanılmamalıdır.
