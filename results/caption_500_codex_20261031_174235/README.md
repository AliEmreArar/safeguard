# Türkçe guardrail birleşik inceleme veri seti

3.000 safe + 500 sexual adayı = **3.500 kayıt**. Yeni 359 aday, Türkçeye
çevrilmiş 359 farklı kaynaktan ve 359 farklı önek grubundan gelir.
Kaynaklar kullanıcı tarafından yetişkin olarak doğrulanmıştır. Çocuk/ergen
ipuçları, birden fazla kişi ve otomatik çeviri uyarılı kaynaklar yeni üretime alınmadı.

Yeni adaylar Codex tarafından yerelde yazılmış ifade envanteriyle bileşimsel
olarak oluşturuldu; Qwen/Grok/API çıktısı değildir. Envanter ve üretim biçimi
çalışma klasöründedir. Bu yöntem kalıp benzerliği taşıyabilir; bağımsız doğal
örnek çeşitliliği veya semantik etiket doğruluğu garantisi değildir.
Kıyafet adları, dar giysi veya nötr beden tarifi tek başına sexual sayılmaz.
"Seksi/baştan çıkarıcı" gibi nitelemelerin etiketi ayrıca insan incelemesi gerektirir.

Yeni adayların **326'sı train, 33'ü validation** kaynaklıdır; varyantlar
kaynaklarıyla aynı split'te kalır. Mevcut 141 aday query kaynaklıdır ve train'e
eklenmedi. Safe test/challenge ile aynı gruptakiler o split'e, diğerleri
`legacy_review` bölümüne yerleştirildi. Önceki prompt/üslup kararlarında görülen
query kayıtları bağımsız nihai test sayılmaz; bu durum satırlarda işaretlidir.
Gerçek kişi kimliği doğrulanmadı; ayrım önek ve normalize birebir metne dayanır.

`text` Türkçe girdidir. Safe satırların kaynak etiketleri korunur. Pozitif
adayların `labels` alanı **önerilen** hedeftir: yalnız indeks 5
(`SEXUAL_CONTENT_ADULT`) 1. Diğer çıkışlar bilinmeyen olarak `label_mask=0`.
Genel `unsafe` kararı otomatik pozitif veya negatif yapılmadı.
**Maskeli BCE gerekir; standart Trainer label_mask'i kendiliğinden uygulamaz.**
Pozitifler `review_status=pending`, `training_eligible=false` taşır.
Bu dosyalar insan incelemesi öncesi son birleşik taslaktır; eğitim hazır/onaylı
etiketli veri olarak sunulmaz. Eğitim veya yeni model skorlama çalıştırılmadı.

`dataset_manifest.json` kesin sayımları, kontrolleri ve sınırlamaları içerir.
Orijinal 3.000 safe dosya ile mevcut 141 adayın dosyaları değiştirilmedi.

İnceleme: `review.html`, `comparison.csv`, `new_359.txt`, `sexual_500.txt`.
