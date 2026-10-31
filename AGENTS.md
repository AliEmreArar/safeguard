# Bu proje için çalışma sınırları

- Kullanıcının bu oturumdaki açık GPU seçimi fiziksel indeks **5**'tir. Bu seçim,
  üst dizindeki eski GPU 7 talimatının bu proje için yerini alır.
- GPU işlerini `CUDA_VISIBLE_DEVICES=GPU-df6a0bca-a90a-9d22-c5c1-69cf30f6f8b6`
  ile sınırla; uygulama içinde bu kart `cuda:0` olur.
- Yalnız bu proje klasörüne yaz. Diğer projeleri, ortak model deposunu,
  diğer kullanıcıların süreçlerini ve conda ortamlarını değiştirme.
- Mevcut oturumun conda ortamında çalış; başka conda ortamının Python'unu kullanma.
  Bu oturumda gözlenen ortam `base` (`/home/proje1bursiyer/miniconda3`).
- Bağımsız çalıştırıcılar ve önbellekler proje içinde tutulur; ortak modeller
  yalnız okunur. Global kurulum veya servis yapılandırması yapma.
- Çalışma ve hedef veri dili Türkçedir. Şimdilik yalnız seçilmiş 3.000 safe
  örnek çevrilecek; 109.993 kaynak kaydın tümü bu talebin kapsamında değildir.
- Kullanıcının sonraki talebi: mevcut 141 caption adayını, seçilmiş Türkçe
  setten 359 yeni adayla toplam 500'e tamamlamak ve birleşik inceleme seti
  hazırlamak. Kullanıcı seçilmiş 3.000 kayıttaki herkesin yetişkin olduğunu
  açıkça doğruladı; kapsam dışındaki kaynaklara genelleme yapma. Çocuk/ergen
  sinyalli kayıtlar cinselleştirici varyant üretiminden yine dışlanır.
- Son birleşik sürüm `datasets/person_guardrail_tr_v4_no_adult_marker_review/` altındadır;
  geçerli çift çalışmasını `results/LATEST_PAIRED_DATASET.json` gösterir.
  500 sexual adayın her birinin aynı split/grupta safe karşılığı vardır.
  Tam split dosyaları ile `paired_view_1000.jsonl` aynı kayıtları içerir;
  bunları birleştirip eğitimde aynı satırları tekrar sayma.
  Pozitif üretim geçmişini `results/LATEST_CAPTION_500.json` gösterir.
  İnceleme bekleyen cinsel aday etiketlerini kesin etiket diye kullanma.
- Kullanıcı tüm caption'lardan “yetişkin” sözcüğünün kaldırılmasını istedi.
  Aktif model girdilerine bu sözcüğü yeniden ekleme. Yetişkinlik doğrulamasını
  yalnız metadata'da tut; metadata'yı `text` girdisine birleştirme.
  Önceki V1/V2/V3 ve üretim çalışmaları tarihsel/provenans arşivleridir.
- Guardrail eğitimini henüz başlatma. Sexual adaylar ayrı inceleme gerektirir.
