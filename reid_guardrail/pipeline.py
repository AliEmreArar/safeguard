import asyncio
import os
from pathlib import Path

from .api import ApiFailure, GrokClient, redact
from .data import audit_sources, digest, normalized, read_sources, write_json
from .models import SyntheticRecord
from .planning import offline_candidate, plan_jobs, prompt_text
from .reports import export_review, report_run
from .storage import Ledger, run_lock
from .validation import RejectedCandidate, make_record


async def run(input_path, output_path, settings, dry_run=True, large_run=False, retry_errors=False, client=None):
    mode = "dry_run" if dry_run else "live"
    if not large_run and (sum(settings.quotas.values()) > 90 or settings.source_limit > 30):
        raise ValueError("Pilot sınırı 30 kaynak/90 iş. Büyük üretim için --large-run gerekli.")
    if not dry_run and not settings.model.strip():
        raise ValueError("Canlı çağrı için --model veya XAI_MODEL gerekli.")
    sources, file_hash = read_sources(input_path)
    audit, eligible = audit_sources(sources, file_hash)
    jobs, plan = plan_jobs(eligible, settings, mode)
    held_out = {normalized(s.caption) for s in sources if s.split != "train"}
    output_path = Path(output_path)
    with run_lock(output_path):
        ledger = Ledger(output_path)
        api = None
        try:
            ledger.bind(digest([file_hash, settings.model_dump(), mode, prompt_text(settings.prompt_version), [j['job_id'] for j in jobs]]))
            write_json(output_path / "data_audit.json", audit)
            write_json(output_path / "plan.json", {**plan, "job_ids": [j["job_id"] for j in jobs]})
            ledger.project()  # repair JSONL from durable successful results before resuming
            previous = {o["job_id"]: o for o in ledger.outcomes()}
            texts = {normalized(o["record"]["caption"]) for o in previous.values() if o["status"] == "success"}
            retryable = {"network_error", "http_error", "api_error", "empty_output", "invalid_schema", "incomplete_output"}
            pending = [j for j in jobs if j["job_id"] not in previous or
                       (retry_errors and previous[j["job_id"]]["status"] in retryable)]
            if pending and not dry_run:
                api = client or GrokClient(settings)
            semaphore = asyncio.Semaphore(settings.concurrency)

            async def perform(job):
                async with semaphore:
                    usage = {}
                    attempts = 0
                    try:
                        if dry_run:
                            candidate, model = offline_candidate(job), "offline-fixture-v1"
                        else:
                            candidate, usage, model, attempts = await api.generate(job)
                        record = make_record(job, candidate, model, settings.model, mode, held_out)
                        text = normalized(record.caption)
                        # Single event loop; no await between duplicate check and durable write.
                        if text in texts:
                            outcome = {"status": "duplicate", "detail": "exact_generated_duplicate"}
                        else:
                            texts.add(text)
                            outcome = {"status": "success", "record": record.model_dump()}
                    except ApiFailure as exc:
                        outcome = {"status": exc.category, "detail": redact(exc.detail, os.environ.get("XAI_API_KEY", ""))}
                        usage, attempts = exc.usage, exc.attempts
                    except RejectedCandidate as exc:
                        outcome = {"status": "validation_rejected", "detail": str(exc)}
                    outcome.update(job_id=job["job_id"], source_id=job["source"]["source_id"],
                                   concept=job["concept"], usage=usage, attempts=attempts)
                    ledger.put(outcome)

            # Bounded task creation as well as bounded concurrent network requests.
            for offset in range(0, len(pending), settings.concurrency):
                await asyncio.gather(*(perform(job) for job in pending[offset:offset + settings.concurrency]))
            ledger.project()
            outcomes = ledger.outcomes()
            records = [SyntheticRecord.model_validate(o["record"]).model_dump() for o in outcomes if o["status"] == "success"]
            export_review(records, output_path)
            report = report_run(records, outcomes, plan, output_path, mode, history=ledger.history())
            report["jobs_skipped_on_resume"] = len(jobs) - len(pending)
            write_json(output_path / "pilot_report.json", report)
            return report
        finally:
            try:
                ledger.project()
            finally:
                ledger.close()
                if api is not None and client is None:
                    await api.close()
