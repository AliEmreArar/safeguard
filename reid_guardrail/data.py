import hashlib
import json
import re
from collections import Counter
from pathlib import Path

from .models import StrictModel
from pydantic import Field


class Source(StrictModel):
    caption: str = Field(min_length=1)
    split: str
    labels: list[str]
    source_id: str
    metadata: dict


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


def folded(text):
    return text.translate(str.maketrans("İI’‘", "ii''")).lower().translate(str.maketrans("çğıöşü", "cgiosu"))


def normalized(text):
    return " ".join(folded(text).split())


def age_info(text):
    """Conservative veto: any child/teen cue defeats adult evidence, even mixed sources."""
    t = folded(text)
    if re.search(r"\b(cocuk\w*|ergen\w*|bebek\w*|resit\s+(?:olmayan|degil)|yetiskin\s+(?:olmayan|degil)|lise\w*|teen\w*|minor\w*|child\w*)\b", t):
        return "minor_or_mixed", None
    if re.search(r"\b(?:18\s+yas\w*\s+(?:alti|kucuk)|under\s*18|[0-9]+\s*[-–]\s*1[0-7]\s+yas)", t):
        return "minor_or_mixed", None
    if re.search(r"\b(?:[0-9]|1[0-7])\s*[-–]\s*year\s*[-–]\s*old\b", t):
        return "minor_or_mixed", None
    ranges = re.finditer(r"\b(\d{1,3})\s*(?:[-–]|ile)\s*(\d{1,3})\s+yas", t)
    if any(min(int(m[1]), int(m[2])) < 18 for m in ranges):
        return "minor_or_mixed", None
    ages = list(re.finditer(r"\b(\d{1,3})\s*(?:yas|y[ıi]l|years?\s*old)", t))
    decades = list(re.finditer(r"\b(\d{2})\s*'?\s*(?:li|lu|lı|lü)\s+yas", t))
    if any(int(m[1]) < 18 for m in ages) or any(int(m[1]) < 20 for m in decades):
        return "minor_or_mixed", None
    patterns = [r"\byetiskin\b", r"\borta\s+yasli\b", r"\byasli\b",
                r"\b(?:[2-9]0)\s*'?\s*(?:li|lu)\s+yas\w*", r"\b(?:1[89]|[2-9]\d)\s+yas\w*"]
    for p in patterns:
        m = re.search(p, t)
        if m:
            return "adult", text[m.start():m.end()]
    return "unknown", None


def read_sources(path):
    path = Path(path)
    content = path.read_bytes()
    file_hash = hashlib.sha256(content).hexdigest()
    if path.suffix.lower() == ".jsonl":
        raw = [json.loads(line) for line in content.decode("utf-8-sig").splitlines() if line.strip()]
    else:
        raw = json.loads(content.decode("utf-8-sig"))
    if not isinstance(raw, list):
        raise ValueError("Girdi JSON listesi veya JSONL olmalı; otomatik dönüştürülmedi.")
    sources = []
    for i, row in enumerate(raw):
        if not isinstance(row, dict) or not {"caption", "split", "labels"} <= row.keys():
            raise ValueError(f"Kaynak kayıt {i + 1}: caption/split/labels alanları gerekli.")
        source = Source(caption=row["caption"], split=row["split"], labels=row["labels"],
                        source_id=f"file:{file_hash}:row:{i + 1}",
                        metadata={k: v for k, v in row.items() if k not in {"caption", "split", "labels"}})
        if not source.caption.strip() or source.split not in {"train", "test", "validation", "val"}:
            raise ValueError(f"Kaynak kayıt {i + 1}: boş caption veya bilinmeyen split.")
        sources.append(source)
    return sources, file_hash


def audit_sources(sources, file_hash):
    train = [s for s in sources if s.split == "train"]
    held = [s for s in sources if s.split != "train"]
    test = [s for s in sources if s.split == "test"]
    exact = {s.caption for s in train} & {s.caption for s in test}
    held_normal = {normalized(s.caption) for s in held}
    identity_keys = ("person_id", "image_id", "filename")
    held_ids = {k: {digest(s.metadata[k]) for s in held if s.metadata.get(k) is not None} for k in identity_keys}
    excluded, eligible = [], []
    seen = set()
    for s in train:
        reasons = []
        if normalized(s.caption) in held_normal:
            reasons.append("held_out_text_overlap")
        for k in identity_keys:
            if s.metadata.get(k) is not None and digest(s.metadata[k]) in held_ids[k]:
                reasons.append(f"held_out_{k}_overlap")
        if normalized(s.caption) in seen:
            reasons.append("duplicate_train_text")
        if s.labels != ["safe"]:
            reasons.append("source_not_confirmed_safe")
        if reasons:
            excluded.append({"source_id": s.source_id, "reasons": reasons})
        else:
            eligible.append(s)
            seen.add(normalized(s.caption))
    person_complete = all(s.metadata.get("person_id") is not None for s in sources)
    report = {
        "file_sha256": file_hash, "total": len(sources),
        "splits": dict(Counter(s.split for s in sources)),
        "labels": dict(Counter(json.dumps(s.labels) for s in sources)),
        "fields": sorted({k for s in sources for k in s.metadata} | {"caption", "split", "labels"}),
        "exact_train_test_shared_distinct_captions": len(exact),
        "exact_shared_captions": sorted(exact), "excluded_train": excluded,
        "eligible_train": len(eligible),
        "eligible_age_groups": dict(Counter(age_info(s.caption)[0] for s in eligible)),
        "person_level_leakage_verifiable": person_complete,
        "person_level_note": "Tam person_id yok; kişi düzeyinde sızıntı doğrulanamaz." if not person_complete else "person_id çakışmaları dışlandı.",
        "source_id_note": "Dosya SHA256 ve 1 tabanlı kayıt konumu; person_id değildir.",
        "input_unchanged": True,
    }
    return report, eligible


def read_evaluation(path):
    from openpyxl import load_workbook
    wb = load_workbook(path, read_only=True, data_only=True)
    cells = []
    for sheet in wb:
        cells.extend({"sheet": sheet.title, "row": i, "values": list(row)}
                     for i, row in enumerate(sheet.values, 1) if any(v is not None for v in row))
    wb.close()
    def metric(label):
        return next((r["values"][1] for r in cells if r["values"][0] == label and len(r["values"]) > 1), None)
    sexual = next((r for r in cells if r["values"][0] == "SEXUAL_CONTENT_ADULT"), None)
    return {"file": str(path), "dataset": metric("Veri"), "total_captions": metric("Toplam caption"),
            "reported_ground_truth": metric("Gerçek etiket"),
            "overall_unsafe_threshold": metric("Eşik (unsafe skoru)"),
            "overall_unsafe_at_threshold": metric("UNSAFE tahmin (false positive)"),
            "sexual_content_adult_score_ge_0_5": sexual["values"][2] if sexual and len(sexual["values"]) > 2 else None,
            "sexual_category_row": sexual, "same_dataset_as_source_assumed": False,
            "note": "Özet değerler yerel XLSX'ten okundu; tam 3250 satırlık tahmin kümesi mevcut değil. Metrikler ayrı tutuldu."}


def write_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
