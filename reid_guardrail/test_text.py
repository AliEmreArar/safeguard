"""Interactive, local-only guardrail inference."""
import argparse
import math
from pathlib import Path
import time


DEFAULT_MODEL = Path(__file__).resolve().parent.parent / "models/modernbert-tr-guardrail"


def main():
    parser = argparse.ArgumentParser(description="Girdiğiniz metni yerel guardrail modeliyle test edin.")
    parser.add_argument("--text", help="Tek bir metni test edip çık")
    parser.add_argument("--threshold", type=float, default=0.5, help="Karar eşiği (varsayılan: 0.5)")
    parser.add_argument("--model-path", type=Path, default=DEFAULT_MODEL)
    args = parser.parse_args()
    if not math.isfinite(args.threshold) or not 0 < args.threshold < 1:
        parser.error("Eşik 0 ile 1 arasında olmalı.")
    if args.text is not None and not args.text.strip():
        parser.error("Metin boş olamaz.")
    if not (args.model_path / "model.safetensors").is_file():
        parser.error("Model bulunamadı. Önce python -m reid_guardrail.download_guardrail çalıştırın.")

    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer

    print("Yerel model yükleniyor...", flush=True)
    torch.set_num_threads(4)
    tokenizer = AutoTokenizer.from_pretrained(args.model_path, local_files_only=True, trust_remote_code=False)
    model = AutoModelForSequenceClassification.from_pretrained(
        args.model_path, local_files_only=True, trust_remote_code=False, attn_implementation="eager"
    ).eval()
    labels = model.config.id2label
    if model.config.problem_type != "multi_label_classification" or "unsafe" not in labels.values():
        parser.error("Modelin çok etiketli şeması / unsafe etiketi beklenen yapıda değil.")

    def evaluate(text):
        inputs = tokenizer(text, return_tensors="pt", truncation=False)
        token_count = inputs["input_ids"].shape[1]
        if token_count > model.config.max_position_embeddings:
            print(f"Metin çok uzun: {token_count} token; sınır {model.config.max_position_embeddings}. Metni kısaltın.")
            return False
        start = time.perf_counter()
        with torch.inference_mode():
            values = torch.sigmoid(model(**inputs).logits)[0].tolist()
        scores = {labels[i]: value for i, value in enumerate(values)}
        decision = "UNSAFE (güvensiz)" if scores["unsafe"] >= args.threshold else "SAFE (güvenli)"
        print(f"\nModel kararı: {decision} | Eşik: {args.threshold:g}")
        print(f"Genel unsafe skoru: {scores['unsafe']:.6f}")
        print("\nKategori skorları (sigmoid, 0–1):")
        for label, value in sorted(scores.items(), key=lambda item: item[1], reverse=True):
            if label != "unsafe":
                marker = "  [eşik üstü]" if value >= args.threshold else ""
                print(f"  {label:<28} {value:.6f}{marker}")
        print(f"\nToken: {token_count} | Süre: {time.perf_counter() - start:.2f} sn\n")
        return True

    print("Genel karar yalnızca unsafe skoruna dayanır; kategori skorları ayrı okunur.")
    print("Skorlar model tahminidir; kesin doğruluk veya kalibre edilmiş olasılık anlamına gelmez.")
    if args.text is not None:
        return 0 if evaluate(args.text) else 1
    print("\nMetninizi tek satırda yazıp Enter'a basın. Çıkış: /exit veya Ctrl+C.")
    print("Metinler dosyaya kaydedilmez; işlem yerelde çalışır.\n")
    try:
        while True:
            text = input("Metin > ").strip()
            if text.lower() in {"/exit", "/quit"}:
                break
            if text:
                evaluate(text)
    except (EOFError, KeyboardInterrupt):
        print()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
