# Güncel Türkçe guardrail — caption'lardan yaş işareti kaldırıldı

**3144 safe + 500 sexual adayı = 3644 kayıt.**
Kullanıcının isteğiyle “yetişkin” sözcüğü bütün aktif caption/metin alanlarından
kaldırıldı. Özne olarak tek başına kullanıldığı yerlerde “kişi” bırakıldı.
Noktalama ve ilk harfler düzeltildi. Diğer yaş sıfatları değiştirilmedi.
Yetişkinlik doğrulaması kaynak metadata'sında korunur; modele yalnız `text` verilir.
Metadata'yı girdiye birleştirme.

Sözcük kaldırılınca aynı kaynak grubunda eşdeğer hale gelen
323 safe kayıt birleştirildi. Eski kimlik bağlantıları
`record_id_aliases.json` ile korunur. 500 çiftin tamamı aynı grup/split'te kalır.
Önceden var olan iki farklı kaynak grubunun train içi metin tekrarı korunmuştur;
splitler arası metin veya grup çakışması yoktur. Gerçek kişi kimliği doğrulanmadı.

`pairs_500.jsonl`, `safe_counterparts_500.jsonl`, `sexual_candidates_500.jsonl`,
`new_359.jsonl` ve `paired_view_1000.jsonl` temizlenmiş görünümlerdir.
Çift görünümündeki 1.000 satır tam split dosyalarında zaten vardır; tekrar ekleme.
500 sexual etiket önceki gibi inceleme bekleyen önerilerdir. Etiket/maskeler
değiştirilmedi; maskeli BCE gereği sürer. Query kaynakları train'e alınmadı;
önceden görülmüş query adayları bağımsız nihai test değildir.

Önceki sürüm arşiv/provenans kaynağıdır; bu sürüm aktif eğitim girdisi taslağıdır.
Eğitim başlatılmadı. `dataset_manifest.json` sayımları ve kontrolleri içerir.

İnceleme: `review.html`, `pairs_500.txt`, `pairs_500.csv`.
