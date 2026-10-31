# Küçük Qwen erotic caption denemesi

Kullanıcının çalıştırdığı `qwen3-30b-a3b-erotic-q4` sunucusu
(`127.0.0.1:18086`) denendi. Qwen3 30B-A3B, Q4_K_M; thinking kapalı.
Mevcut sunucu ayarları, GPU yerleşimi ve terminal sohbet geçmişi değiştirilmedi.
Her istekte yalnız o denemenin mesajları gönderildi.

İki turda dört yetişkinliği doğrulanmış kaynaktan 12 çıktı alındı:

- İlk tur: ayrıntılı yönerge ve JSON şeması, 8 çıktı, 4,37 saniye.
  Altı çıktı kaynak caption'ını birebir tekrarladı. Eklenen göz ifadesi
  kaynaktan gelmiyordu. Alıntı alanları da denetlenmelidir.
  Kayıtlar: `../qwen_erotic_caption_pilot_20261031_172947/`.
- İkinci tur: kısa yönerge, bir biçim örneği ve düz metin, 4 çıktı, 1,54 saniye.
  Çıktılar kısa üçüncü şahıs betimleme biçiminde kaldı ve grafik olmayan
  görünüş nitelemeleri ekledi. `comparison.txt` ve `comparison.csv` yan yana
  kaynak, önceki Grok adayı ve yeni Qwen çıktısını içerir.

Asistanın ikinci tur gözlemleri:

1. `27098_2.jpg`: kaynakta bulunan açık ten bilgisi düştü.
2. `27019_2.jpg`: bu küçük örnekte kaynak ayrıntıları büyük ölçüde korundu.
3. `27082_3.jpg`: koyu renk kısa kollu iç üst kayboldu; "seksi bir dengede"
   ifadesi doğal caption dili açısından zayıf.
4. `26615_1.jpg`: beyaz dairesel göğüs baskısı kayboldu.

Kısa promptla uyum arttı ancak aynı görünüş kalıbı tekrarlanıyor ve bazı
kaynak ayrıntıları düşüyor. "Seksi/baştan çıkarıcı" sözcükleri tek başına
kesin sexual etiketi sayılmadı. Bunlar insan incelemesi bekleyen adaylardır.
Bu dört kaynaklık deneme modelin genel kalitesini ölçen bir benchmark değildir.

Kaynaklar önceki 141 adayın query kaynaklarıdır. İki kaynakta açık yetişkin
bilgisi, diğer ikisinde önceki kayıtlı kullanıcı doğrulaması vardır.
Çocuk/ergen kaydı kullanılmadı. Bu pilot held-out deney kaydıdır; train'e
veya 3.000 safe Türkçe kayda hiçbir satır eklenmedi. Eğitim başlatılmadı.

Tekrarlama yeni üretim yapar; tamamlanan denemeyi incelemek için kaydedilmiş
çıktıları aç. Betik: `scripts/pilot_qwen_caption_style.py`; ikinci tur `--plain`.
