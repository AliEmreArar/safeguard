# Veri incelemesi

Toplam: 5999; split: {'train': 4800, 'test': 1199}.

Train/test ortak farklı caption: 8. Üretime uygun train: 4775.

Tam person_id yok; kişi düzeyinde sızıntı doğrulanamaz.

Etiketler model skorundan türetilmedi. Kaynak dosya değiştirilmedi.

{
  "file": "Guardrail Test - query_final_tr (modernbert-tr-guardrail).xlsx",
  "dataset": "query_final_tr.jsonl",
  "total_captions": 3250.0,
  "reported_ground_truth": "Hepsi SAFE",
  "overall_unsafe_threshold": 0.5,
  "overall_unsafe_at_threshold": 142.0,
  "sexual_content_adult_score_ge_0_5": 1330.0,
  "sexual_category_row": {
    "sheet": "Untitled",
    "row": 23,
    "values": [
      "SEXUAL_CONTENT_ADULT",
      141.0,
      1330.0,
      0.4356,
      1.0
    ]
  },
  "same_dataset_as_source_assumed": false,
  "note": "Özet değerler yerel XLSX'ten okundu; tam 3250 satırlık tahmin kümesi mevcut değil. Metrikler ayrı tutuldu."
}