# Excel caption'larının cinselleştirilmiş anlatım adayları

31 Ekim 2026. Kaynak Excel değiştirilmedi.

Tamamlanan çıktı: **141 ayrı kaynak için 141 benzersiz aday**. Açık çocuk
kaydı hariç bütün kaynaklar işlendi. 24 başarılı API yanıtı kaydedildi.
Dört kanıt alıntısında yazım/büyük-küçük harf/ek farkı yerelde düzeltildi;
caption metinleri değiştirilmedi. Ham yanıtlar ve düzeltme kaydı korunur.
141 yetişkinlik ve birebir alıntı kontrolü geçti; istenmeyen teklif/eylem
ifadelerine yönelik metin taramasında eşleşme bulunmadı. Bu tarama tüm
semantik hataları yakalama garantisi değildir. 45 çevrimdışı test geçti.

- `sexualized_captions.txt`: yalnız üretilen caption'lar ve kaynak görsel dosya adları.
- `comparison.csv`: Excel'de açılabilen UTF-8 BOM dosyası; özgün caption ve aday yan yana. İnsan kararı ve notları için boş alanlar içerir.
- `sexualized_captions.jsonl`: kaynak kimliği, özgün metin, aday, cinselleştirici ifade ve metadata.
- `all_rows.jsonl`: dışlanan kayıt dahil tüm kaynakların durumları.
- `summary.json`: kaynak/çıktı sayımları.
- `quality_check.json`: son kapsam, yetişkinlik, alıntı eşleşmesi ve kaynak bütünlüğü kontrolleri.

142 kaynak kaydından açık çocuk ifadesi içeren `26682_2.jpg` dönüştürülmedi.
Yaşı metinde bulunmayan 139 kaydın tamamındaki kişilerin yetişkin olduğu
kullanıcı tarafından açıkça doğrulandı. Bu bilgi görüntüden çıkarılmadı;
`adult_evidence_source=user_confirmation` olarak tutuldu. İki kaynak zaten
açık yetişkin ifadesi içerir. Yetişkinlik doğrulamasının kapsamı
`adult_confirmation.json` içindedir.

Hedef, kişi ve kıyafet tarifine cinselleştirici görünüş nitelemesi eklemektir.
Kıyafet adları, dar giysi veya beden şekli tek başına sexual sayılmaz.
Seks teklifi, cinsel eylem veya birinci şahıs arzu cümlesi üretim hedefi değildir.
Eklenen nitelemeler gerçek görüntüden doğrulanmış özellik değildir.

Özellikle yalnızca “seksi”, “baştan çıkarıcı” veya “kışkırtıcı” gibi nitelemeler
içeren adaylar, belirlenen etikete göre sınırda kalabilir. Üretici çıktısı
kesin eğitim etiketi yapılmadı; bütün `review_status` değerleri `pending`.
Kaynak split'i bilinmediğinden kayıtlar train olarak işaretlenmedi.
Orijinal safe caption'lar karşıt çift olarak korunur, ancak kaynaklarda split
bilgisi tamamlanmadan bu dosyalar otomatik eğitime sokulmamalıdır.

Üretici `grok-4.7`; altışarlı partiler; en fazla üç paralel istek; otomatik retry yok.
Prompt `prompt.txt` içindedir. Anahtarsız istek, yanıt ve kullanım kayıtları
saklanmıştır. Olası yarım istekler otomatik yeniden gönderilmez.

İlk farklı çıktı klasöründeki istek, orijinal yaş alanının `unknown` olması
nedeniyle reddedildi. Bu klasörde gerçek kaynak yaş alanı korunurken,
kullanıcının yetişkinlik doğrulaması ayrı alanlarla açıkça iletildi.
Bu, yaşın kaynak görüntüden doğrulandığı iddiası değildir.
