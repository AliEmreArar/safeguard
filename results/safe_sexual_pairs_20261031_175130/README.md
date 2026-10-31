# Türkçe guardrail — 500 safe / sexual aday çifti

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

İnceleme: `review.html`, `pairs_500.txt`, `pairs_500.csv`.
