# Türkçe safe person caption alt kümesi

Kullanıcının isteğiyle seçilmiş 3.000 safe caption Türkçeye çevrildi:
2.000 train, 250 validation, 500 test ve 250 challenge.

Çeviri: yerel Qwen3.8 27B, Q4_K_M (4 bit), thinking kapalı, fiziksel GPU 5.
Çeviriler otomatik üretilmiştir; insan tarafından tüm satırlar incelenmemiştir.
Kullanıcı mevcut aşamada küçük çeviri hatalarını kabul ederek toplu çeviri istedi.
Otomatik terim kontrolleri semantik doğruluk garantisi değildir; işaretler
`translation_flags` alanında ve kalite raporundadır.

`text` Türkçe girdidir; `source_text_en` özgün İngilizce metindir.
Kaynak kimliği, dosya/satır, grup, split, 11 sıfırlık safe etiketi ve label mask
aynen korunmuştur. Safe etiketleri kullanıcının kaynak veri beyanından gelir.
`source_baseline_scores_en` yalnız İngilizce kaynağın eski skorlarıdır;
Türkçe ölçümü değildir. Türkçe token uzunlukları henüz guardrail tokenizer'ıyla ölçülmedi.

Kaynaklar ve bütün varyantları aynı split'te kalmalıdır. Grup ayrım kaydı:
`../person_guardrail_safe_v1/source_group_assignments.json`.
Çeviride oluşabilecek birebir metin tekrarları `quality_check.json` içinde
raporlanır; eğitimden önce varsa splitler arası metin çakışmaları giderilmelidir.

Bu alt küme yalnız safe örnekler içerir. Sexual pozitifler henüz eklenmedi,
guardrail eğitimi başlamadı. Tam fine-tune verisi değildir.
Önceki 141 query kaynaklı sexual aday train'e eklenmemelidir.

Kaynak/çeviri karşılaştırmaları ve tekrar başlatılabilir işlem kayıtları:
`../../results/translate_tr_3000_qwen38_20261031/`.
