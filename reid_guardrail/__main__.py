import argparse
import asyncio
import json
import os
from pathlib import Path

from pydantic import ValidationError

from .data import audit_sources, read_evaluation, read_sources, write_json
from .models import Settings, SyntheticRecord
from .pipeline import run
from .reports import export_review


def main():
    parser = argparse.ArgumentParser(description="Türkçe ReID sentetik moderasyon pilotu")
    sub = parser.add_subparsers(dest="command", required=True)
    inspect = sub.add_parser("inspect", help="Yerel kaynak/sızıntı ve isteğe bağlı XLSX rapor denetimi")
    inspect.add_argument("--input", required=True)
    inspect.add_argument("--evaluation")
    inspect.add_argument("--out", default="reports")
    generate = sub.add_parser("generate", help="Varsayılan ağsız dry-run; --live ile API")
    generate.add_argument("--input", required=True)
    generate.add_argument("--out", default="runs/dry-run")
    generate.add_argument("--config")
    generate.add_argument("--model")
    group = generate.add_mutually_exclusive_group()
    group.add_argument("--live", action="store_true")
    group.add_argument("--dry-run", action="store_true")
    generate.add_argument("--sources", type=int)
    generate.add_argument("--quota", action="append", default=[], help="konsept=sayı; diğer kotalar korunur")
    generate.add_argument("--large-run", action="store_true")
    generate.add_argument("--retry-errors", action="store_true", help="Retleri ve tamamlananları tekrarlamaz")
    export = sub.add_parser("export-review")
    export.add_argument("--input", required=True)
    export.add_argument("--out", required=True)
    validate = sub.add_parser("validate", help="Kaydedilmiş adaylara ayrı yerel doğrulama")
    validate.add_argument("--input", required=True)
    validate.add_argument("--out", default="reports/validation.json")
    validate.add_argument("--source-file", help="Kaynak izlenebilirliği ve held-out çakışmalarını da denetler")
    args = parser.parse_args()
    try:
        if args.command == "inspect":
            sources, file_hash = read_sources(args.input)
            report, _ = audit_sources(sources, file_hash)
            if args.evaluation:
                report["separate_evaluation_report"] = read_evaluation(args.evaluation)
            write_json(Path(args.out) / "data_inspection.json", report)
            (Path(args.out) / "data_inspection.md").write_text(
                "# Veri incelemesi\n\n" + f"Toplam: {report['total']}; split: {report['splits']}.\n\n"
                + f"Train/test ortak farklı caption: {report['exact_train_test_shared_distinct_captions']}. "
                + f"Üretime uygun train: {report['eligible_train']}.\n\n{report['person_level_note']}\n\n"
                + "Etiketler model skorundan türetilmedi. Kaynak dosya değiştirilmedi.\n\n"
                + (json.dumps(report['separate_evaluation_report'], ensure_ascii=False, indent=2) if args.evaluation else "Yerel değerlendirme raporu verilmedi."), encoding="utf-8")
            print(json.dumps({k: report[k] for k in ("total", "splits", "eligible_train", "eligible_age_groups", "exact_train_test_shared_distinct_captions")}, ensure_ascii=False))
        elif args.command == "generate":
            raw = json.loads(Path(args.config).read_text(encoding="utf-8-sig")) if args.config else {}
            if args.live:
                from dotenv import load_dotenv
                load_dotenv(Path.cwd() / ".env", override=False)
                raw["model"] = args.model or raw.get("model") or os.environ.get("XAI_MODEL", "")
            elif args.model:
                raw["model"] = args.model
            if args.sources is not None:
                raw["source_limit"] = args.sources
            if args.quota:
                quotas = dict(raw.get("quotas", Settings().quotas))
                for entry in args.quota:
                    key, value = entry.split("=", 1)
                    quotas[key] = int(value)
                raw["quotas"] = quotas
            settings = Settings.model_validate(raw)
            report = asyncio.run(run(args.input, args.out, settings, dry_run=not args.live,
                                     large_run=args.large_run, retry_errors=args.retry_errors))
            print(json.dumps({k: report[k] for k in ("mode", "accepted_candidate_quotas", "remaining_candidate_quotas", "outcomes", "jobs_skipped_on_resume")}, ensure_ascii=False))
        else:
            records = []
            failures = []
            source_map = None
            eligible_ids = None
            held_out = set()
            if args.command == "validate" and args.source_file:
                from .data import normalized
                source_rows, sha = read_sources(args.source_file)
                _, eligible_rows = audit_sources(source_rows, sha)
                source_map = {s.source_id: s for s in source_rows}
                eligible_ids = {s.source_id for s in eligible_rows}
                held_out = {normalized(s.caption) for s in source_rows if s.split != "train"}
            for index, line in enumerate(Path(args.input).read_text(encoding="utf-8-sig").splitlines(), 1):
                if not line.strip():
                    continue
                try:
                    record = SyntheticRecord.model_validate_json(line)
                    from .data import age_info, normalized
                    from .models import POSITIVE
                    if record.concept in POSITIVE or record.suggested_decision == "block":
                        if age_info(record.source_caption)[0] != "adult" or age_info(record.caption)[0] != "adult":
                            raise ValueError("age")
                        if not record.age_evidence or normalized(record.age_evidence) not in normalized(record.caption):
                            raise ValueError("age_preservation")
                    if source_map is not None:
                        src = source_map.get(record.source_id)
                        if src is None or record.source_id not in eligible_ids:
                            raise ValueError("ineligible_source")
                        if src.caption != record.source_caption or src.metadata != record.source_metadata:
                            raise ValueError("source_traceability")
                        if normalized(record.caption) in held_out:
                            raise ValueError("held_out_overlap")
                    records.append(record.model_dump())
                except (ValidationError, ValueError):
                    failures.append({"line": index, "error": "schema_or_age_check_failed"})
            ids = [r["id"] for r in records]
            texts = [normalized(r["caption"]) for r in records]
            if args.command == "export-review":
                if failures:
                    raise ValueError("Şema/yaş hatası var; önce validate komutuyla inceleyin.")
                export_review(records, args.out, source_directory=Path(args.input).parent)
                print(f"İnceleme çıktısı: {args.out}; kayıt: {len(records)}")
            else:
                report = {"valid_schema_age_records": len(records), "failures": failures,
                          "source_traceability_checked": source_map is not None,
                          "duplicate_ids": len(ids) - len(set(ids)), "duplicate_captions": len(texts) - len(set(texts)),
                          "semantic_validation": "İnsan incelemesi bekliyor; bu kontrol güvenlik etiketinin doğruluğunu kanıtlamaz."}
                write_json(args.out, report)
                print(json.dumps(report, ensure_ascii=False))
                if failures or report["duplicate_ids"] or report["duplicate_captions"]:
                    return 1
    except ValidationError:
        # Pydantic errors may include raw inputs; do not echo them to the terminal.
        parser.exit(2, "Şema/yapılandırma geçersiz. Alan tiplerini ve config.example.json dosyasını kontrol edin.\n")
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        from .api import redact
        # Include only our own validation text; IO errors can contain user paths, not file contents.
        parser.exit(2, redact(str(exc), os.environ.get("XAI_API_KEY", "")) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
