# Görsel caption biçimi denemesi

Önceki `person-caption-pilot` deneyindeki “seks teklifi”, “haz nesnesidir” ve
“olarak sunulur” cümleleri hedef kişi-caption biçimi için uygun bulunmadı.
Yüksek cinsel skor almaları bu biçim sorununu düzeltmez.

Bu yeni deney iki Grok isteği / sekiz çift içerir. İlk prompt görünür eylemi
esas aldı, fakat kıyafeti fazla azalttı. İkinci prompt kısa kişi betimlemesini,
somut üst giysiyi ve yalnız eylemin adını korudu. Cinsel eylemler grafik
detay olmadan, sınıflandırma amaçlı olgusal biçimde anıldı.

## Kendime sorduğum sorular ve sonuç

- Fotoğraf altında okunabilecek bir kişi tarifi mi? İkinci turun ilk pozitif
  örneği bu yapıya uygun; niyet ve konuşma uydurmuyor.
- Cinsel etiket giysiden mi geliyor? Hayır; dekolte/mini etek/straplez/tayt
  güvenli örneklerde de var. Pozitiflerde gerekçe açıkça anılan cinsel eylem.
- Gerçek görüntüden üretilmiş mi? Hayır. Tüm ortam, giysi ve eylemler sentetik;
  gerçek kaynak görüntü görülmedi. Görsele sadakat doğrulanmış sayılmaz.
- Bütün çıktılar iyi mi? Hayır. İkinci turun çiftli eylem örnekleri
  “durur; ... birliktelik yaşar” şeklinde belirsiz ve mekanik kalıyor.
  Üçüncü güvenli örnekte “kapalı gözle yürür” görsel tutarlılık sorunu var.
- Kişi re-identification dağılımına uyuyor mu? Kısmen. Cinsel eylem içeren
  iç mekân sahneleri sıradan sokak kişisi caption'larından farklı bir
  dağılımdır. Bu nedenle yalnız bu örneklerle veri kümesi ölçeklenmemeli.
- Çeşitlilik yeterli mi? Hayır. İki eylem kalıbı tekrar ediyor. Bu hâliyle
  eğitim kümesi değil, biçim ve etiket politikasını sınayan küçük denemedir.

`selected_pair.txt` ikinci turun ilk çiftini değiştirmeden gösterir.
`review.html` ve `captions.txt` bütün denemeleri içerir; bunların tamamı
başarılı caption olarak önerilmez. Tüm kayıtlar insan incelemesi bekler.

Güvenli metni sırf beden/kıyafet kelimeleri yüzünden sexual diye etiketlemek
amaçla çelişir. Eylem de içermeyen cinselleştirilmiş bir dil alt grubu ayrıca
ele alınacaksa, hangi ifadelerin tarafsız beden tarifinden ayrıldığı açık bir
etiket yönergesinde tanımlanmalıdır. Önceki soyut “haz nesnesi” ekleri bunun
yerine geçmez.

Model eğitilmedi. İki başarılı API isteği yapıldı; otomatik retry yok.
Promptlar, yanıtlar, kullanım ve doğrulama kayıtları tur klasörlerinde korundu.
