import csv
import html
import json
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from statistics import mean

from .data import normalized, write_json
from .pricing import estimate_cost


def export_review(records, directory, source_directory=None):
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    findings_path = Path(source_directory or directory) / "semantic_review.json"
    findings = json.loads(findings_path.read_text(encoding="utf-8")) if findings_path.exists() else {}
    by_id = {item["id"]: item for item in findings.get("findings", [])}
    columns = ["id", "source_id", "source_split", "source_caption", "caption", "concept", "hard_concept",
               "target_decision", "generator_decision", "suggested_decision", "suggested_labels", "task_relevance",
               "transformation_type", "pair_id", "changed_spans", "age_evidence", "mode", "review_status",
               "validation_flags", "independent_recommended_decision", "independent_review_notes",
               "human_decision", "human_labels", "reviewer", "review_notes"]
    with (directory / "review.csv").open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for record in records:
            row = {k: record.get(k, "") for k in columns}
            finding = by_id.get(record["id"], {})
            row["independent_recommended_decision"] = finding.get("recommended_decision", "")
            row["independent_review_notes"] = finding.get("reason", "")
            for key, value in row.items():
                if isinstance(value, (list, dict)):
                    row[key] = json.dumps(value, ensure_ascii=False)
                elif isinstance(value, str) and value.lstrip().startswith(("=", "+", "-", "@")):
                    row[key] = "'" + value  # spreadsheet formula injection protection
            writer.writerow(row)
    body = []
    for r in records:
        e = lambda value: html.escape(str(value))
        finding = by_id.get(r["id"])
        review_note = ("<p><b>Bağımsız ön inceleme: REVIEW.</b> " + e(finding["reason"]) + "</p>") if finding else ""
        body.append(f"<article><h2>{e(r['concept'])} · {e(r['suggested_decision'])}</h2>"
                    f"<p class='meta'>{e(r['id'])} · {e(r['mode'])} · pending</p>"
                    f"<p><b>Kaynak:</b> {e(r['source_caption'])}</p>"
                    f"<p><b>Aday:</b> {e(r['caption'])}</p>"
                    f"<p>Hedef: {e(r['target_decision'])}; ReID uygunluğu: {e(r['task_relevance'])}; "
                    f"dönüşüm: {e(r['transformation_type'])}</p>"
                    f"<p>Çift: {e(r['pair_id'])}; yaş kanıtı: {e(r['age_evidence'])}</p>"
                    f"<p>{e(r['policy_rationale'])}</p><p>{e(', '.join(r['validation_flags']))}</p>{review_note}</article>")
    (directory / "review.html").write_text(
        "<!doctype html><html lang='tr'><meta charset='utf-8'><title>ReID aday incelemesi</title>"
        "<style>body{font:16px/1.6 system-ui;max-width:1100px;margin:40px auto;padding:20px;background:#f5f7fa}"
        "article{padding:20px;margin:20px 0;background:white;border:1px solid #dce1e8;border-radius:8px}"
        ".meta{font:12px monospace;overflow-wrap:anywhere}h2{font-size:19px}</style>"
        "<h1>Sentetik ReID moderasyon adayları</h1><p>Öneriler kesin etiket değildir. "
        "İnsan kararını review.csv içindeki human_* alanlarına yazın. Dry-run kayıtları ağsız fixture'dır.</p>"
        + "".join(body) + "</html>", encoding="utf-8")


def near_duplicates(records, threshold=0.88, max_comparisons=200000):
    pairs = []
    compared = 0
    truncated = False
    for i, a in enumerate(records):
        for b in records[i + 1:]:
            if compared >= max_comparisons:
                truncated = True
                break
            compared += 1
            score = SequenceMatcher(None, normalized(a["caption"]), normalized(b["caption"]), autojunk=False).ratio()
            if score >= threshold:
                pairs.append({"a": a["id"], "b": b["id"], "similarity": round(score, 4),
                              "same_source": a["source_id"] == b["source_id"],
                              "same_pair": bool(a["pair_id"] and a["pair_id"] == b["pair_id"])})
        if truncated:
            break
    return {"threshold": threshold, "comparisons": compared, "truncated": truncated, "pairs": pairs,
            "note": "Karakter benzerliği taraması; semantik tekrar veya kişi düzeyi sızıntı kanıtı değildir. Çiftler beklenen benzerlik yaratabilir."}


def report_run(records, outcomes, plan, directory, mode, history=None):
    directory = Path(directory)
    accepted = Counter(r["concept"] for r in records)
    matched = Counter(r["concept"] for r in records if r["suggested_decision"] == r["target_decision"])
    tokens = Counter()
    missing_usage = 0
    examples = defaultdict(list)
    lengths = defaultdict(list)
    for r in records:
        if len(examples[r["concept"]]) < 3:
            examples[r["concept"]].append({"caption": r["caption"], "decision": r["suggested_decision"], "id": r["id"]})
        lengths[r["suggested_decision"]].append(len(r["caption"]))
    for outcome in (history if history is not None else outcomes):
        usage = outcome.get("usage", {})
        if mode == "live" and not usage:
            missing_usage += 1
        for key in ("input_tokens", "output_tokens", "total_tokens"):
            tokens[key] += usage.get(key, 0)
    prices = estimate_cost(history if history is not None else outcomes,
                           records[0].get("requested_model") if records and mode == "live" else None)
    report = {"mode": mode, "live_api_called": mode == "live" and bool(outcomes),
              "offline_fixture_only": mode == "dry_run", **plan,
              "accepted_candidate_quotas": dict(accepted), "target_matching_suggestions": dict(matched),
              "remaining_candidate_quotas": {c: max(0, q - accepted[c]) for c, q in plan["requested_quotas"].items()},
              "remaining_target_matching_quotas": {c: max(0, q - matched[c]) for c, q in plan["requested_quotas"].items()},
              "outcomes": dict(Counter(o["status"] for o in outcomes)),
              "history_outcome_count": len(history if history is not None else outcomes),
              "tokens_reported_by_api": dict(tokens), "outcomes_without_usage": missing_usage,
              "cost_estimate_usd": prices["estimated_usd"],
              "cost_estimate_details": prices,
              "cost_note": prices.get("note", prices.get("reason")),
              "caption_length_chars": {d: {"count": len(v), "mean": round(mean(v), 1), "min": min(v), "max": max(v)} for d, v in lengths.items()},
              "examples_by_concept": dict(examples), "human_approved": 0,
              "training_target_vectors_created": False,
              "real_test_examples_generated": 0, "synthetic_test_examples_generated": 0,
              "quality_note": "Şema/yaş/split kontrolleri uygulandı. Bağımsız semantik doğruluk ve üslup dengesi insan incelemesi gerektirir; fixture başarısı canlı model kalitesini göstermez."}
    findings_path = directory / "semantic_review.json"
    if findings_path.exists():
        report["independent_semantic_review"] = json.loads(findings_path.read_text(encoding="utf-8"))
    write_json(directory / "pilot_report.json", report)
    write_json(directory / "near_duplicates.json", near_duplicates(records))
    lines = ["# Pilot raporu", "", f"Mod: {mode}. İnsan onaylı kayıt: 0. Eğitim yapılmadı.", "",
             "| Konsept | Hedef | Plan | Aday | Hedefle eşleşen öneri |", "|---|---:|---:|---:|---:|"]
    for c, q in plan["requested_quotas"].items():
        lines.append(f"| {c} | {q} | {plan['planned_quotas'][c]} | {accepted[c]} | {matched[c]} |")
    lines.extend(["", report["quality_note"], "", report["cost_note"]])
    if prices["estimated_usd"] is not None:
        lines.extend(["", f"Bildirilen token kullanımından tahmini maliyet: ${prices['estimated_usd']:.6f}. "
                      f"[Resmî fiyat kaynağı]({prices['source']}) ({prices['verified_on']})."])
    lines.extend(["", "## Konsept örnekleri"])
    if findings_path.exists():
        findings = report["independent_semantic_review"]
        lines.extend(["", f"Bağımsız ön incelemede {len(findings.get('findings', []))} aday için REVIEW önerildi. "
                      "Üretici kararları ayrı korunur; bu ön inceleme insan onayı değildir. Gerekçeler semantic_review.json ve review.csv/HTML içindedir."])
    for concept, examples_list in examples.items():
        lines.extend(["", f"### {concept}"])
        lines.extend(f"- {item['caption']} ({item['decision']}, pending)" for item in examples_list)
    (directory / "pilot_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report
