import asyncio
import json
import socket
from pathlib import Path

import httpx
import pytest
from pydantic import ValidationError

from reid_guardrail.api import ApiFailure, GrokClient, parse_response, redact, request_body
from reid_guardrail.data import age_info, audit_sources, normalized, read_sources
from reid_guardrail.models import Candidate, Settings
from reid_guardrail.pipeline import run
from reid_guardrail.planning import offline_candidate, plan_jobs, user_payload
from reid_guardrail.storage import Ledger, run_lock
from reid_guardrail.validation import RejectedCandidate, make_record


@pytest.mark.parametrize("text,expected", [
    ("30 yaşında kişi", "adult"), ("20'li yaşlar, erkek", "adult"),
    ("30’lu yaşlarında kadın", "adult"), ("orta yaşlı kişi", "adult"),
    ("yetişkin kişi", "adult"), ("18 yaşında kişi", "adult"),
    ("kadın", "unknown"), ("erkek", "unknown"), ("genç", "unknown"),
    ("kız", "unknown"), ("oğlan", "unknown"),
    ("17 yaşındaki kişi", "minor_or_mixed"), ("10'lu yaşlarında", "minor_or_mixed"),
    ("yetişkin ve çocuk", "minor_or_mixed"), ("ergen, 30 yaşında", "minor_or_mixed"),
    ("yetişkin olmayan kişi", "minor_or_mixed"),
    ("yetişkin değil", "minor_or_mixed"), ("18 yaş altı", "minor_or_mixed"),
    ("yetişkin ve 17-year-old", "minor_or_mixed"),
    ("17-20 yaşlarında", "minor_or_mixed"),
])
def test_age(text, expected):
    assert age_info(text)[0] == expected


def data_file(tmp_path, rows=None, suffix=".json"):
    rows = rows or [
        {"caption": f"{30+i} yaşında kişi, koyu saç, mavi ceket", "split": "train", "labels": ["safe"]}
        for i in range(3)]
    path = tmp_path / ("source" + suffix)
    text = "\n".join(json.dumps(r, ensure_ascii=False) for r in rows) if suffix == ".jsonl" else json.dumps(rows, ensure_ascii=False)
    path.write_text(text, encoding="utf-8")
    return path


def small_settings(**kwargs):
    return Settings(source_limit=3, quotas={"normal_safe": 3, "hard_safe": 3, "objectification": 1,
                                          "sexual_intent": 1, "sexual_harassment": 1}, **kwargs)


def test_split_exclusion_identity_and_source_integrity(tmp_path):
    rows = [
        {"caption": "30 yaşında kişi", "split": "train", "labels": ["safe"]},
        {"caption": "30 yaşında kişi", "split": "test", "labels": ["safe"]},
        {"caption": "40 yaşında kişi", "split": "train", "labels": ["safe"], "person_id": "p1"},
        {"caption": "farklı caption", "split": "test", "labels": ["safe"], "person_id": "p1"},
        {"caption": "50 yaşında kişi", "split": "train", "labels": ["safe"], "filename": "a.jpg"},
    ]
    path = data_file(tmp_path, rows, ".jsonl")
    before = path.read_bytes()
    sources, sha = read_sources(path)
    report, eligible = audit_sources(sources, sha)
    assert report["exact_train_test_shared_distinct_captions"] == 1
    assert len(eligible) == 1 and eligible[0].metadata["filename"] == "a.jpg"
    assert path.read_bytes() == before
    assert all(s.split == "train" for s in eligible)
    assert not report["person_level_leakage_verifiable"]


def test_unknown_age_positive_shortfall_and_payload_no_test(tmp_path):
    rows = [{"caption": "genç kadın", "split": "train", "labels": ["safe"]},
            {"caption": "SECRET_TEST_TEXT", "split": "test", "labels": ["safe"]}]
    path = data_file(tmp_path, rows)
    sources, sha = read_sources(path)
    _, eligible = audit_sources(sources, sha)
    jobs, plan = plan_jobs(eligible, small_settings(), "dry_run")
    assert plan["planned_quotas"]["objectification"] == 0
    assert plan["quota_shortfalls_before_generation"]["objectification"] == 1
    for job in jobs:
        serialized = json.dumps(user_payload(job))
        assert "SECRET_TEST_TEXT" not in serialized and "source_id" not in serialized and "split" not in serialized


def test_schema_and_age_output_gate(tmp_path):
    with pytest.raises(ValidationError):
        Candidate(caption="x", decision="safe", task_relevance="relevant", transformation_type="paraphrase",
                  added_attributes=False, policy_rationale="test")
    sources, sha = read_sources(data_file(tmp_path))
    _, eligible = audit_sources(sources, sha)
    jobs, _ = plan_jobs(eligible, small_settings(), "dry_run")
    job = next(j for j in jobs if j["concept"] == "objectification")
    candidate = offline_candidate(job)
    candidate.caption = "kişiyi bul"
    with pytest.raises(RejectedCandidate):
        make_record(job, candidate, "fixture", "", "dry_run", set())
    candidate = offline_candidate(job)
    with pytest.raises(RejectedCandidate, match="held_out"):
        make_record(job, candidate, "fixture", "", "dry_run", {normalized(candidate.caption)})


def test_dry_run_no_network_resume_and_projection_recovery(tmp_path, monkeypatch):
    def no_network(*args, **kwargs):
        raise AssertionError("Network forbidden")
    # Block the HTTP transport; local event-loop sockets are unrelated to API access.
    monkeypatch.setattr(httpx.AsyncClient, "send", no_network)
    monkeypatch.delenv("XAI_API_KEY", raising=False)
    path = data_file(tmp_path)
    out = tmp_path / "run"
    report = asyncio.run(run(path, out, small_settings()))
    assert report["outcomes"] == {"success": 9}
    original = (out / "candidates.jsonl").read_bytes()
    with (out / "candidates.jsonl").open("ab") as f:
        f.write(b'{"torn":')
    resumed = asyncio.run(run(path, out, small_settings()))
    assert resumed["jobs_skipped_on_resume"] == 9
    assert (out / "candidates.jsonl").read_bytes() == original
    for line in original.decode().splitlines():
        r = json.loads(line)
        assert r["generator_model"] == "offline-fixture-v1" and r["review_status"] == "pending"
    with pytest.raises(ValueError, match="başka"):
        asyncio.run(run(path, out, small_settings(temperature=0.7)))


def test_exact_deduplication(tmp_path, monkeypatch):
    import reid_guardrail.pipeline as pipeline
    original = pipeline.offline_candidate
    def identical(job):
        result = original(job)
        result.caption = "30 yaşında kişi"
        return result
    monkeypatch.setattr(pipeline, "offline_candidate", identical)
    report = asyncio.run(run(data_file(tmp_path), tmp_path / "dedup", small_settings()))
    assert report["outcomes"]["success"] == 1
    assert report["outcomes"]["duplicate"] > 0


def response_data(candidate=None):
    if candidate is None:
        candidate = Candidate(caption="30 yaşında, mavi ceketli kişi", decision="allow", task_relevance="relevant",
                              transformation_type="paraphrase", added_attributes=False, policy_rationale="Tarafsız betimleme")
    return {"model": "configured-model", "status": "completed", "usage": {"input_tokens": 20, "output_tokens": 10, "total_tokens": 30},
            "output": [{"type": "message", "content": [{"type": "output_text", "text": json.dumps({"status": "ok", "candidate": candidate.model_dump(), "refusal_reason": None})}]}]}


@pytest.mark.parametrize("data,category", [
    ({"output": []}, "empty_output"),
    ({"status": "incomplete"}, "incomplete_output"),
    ({"output": [{"content": [{"type": "refusal", "refusal": "refused"}]}]}, "refusal"),
    ({"output": [{"content": [{"type": "output_text", "text": "not json"}]}]}, "invalid_schema"),
    ({"output": [{"content": [{"type": "output_text", "text": '{"status":"refused","candidate":null,"refusal_reason":"no"}'}]}]}, "refusal"),
])
def test_api_response_failures(data, category):
    with pytest.raises(ApiFailure) as exc:
        parse_response(data)
    assert exc.value.category == category


def test_mock_transport_refusal_no_retry_and_structured_payload(tmp_path, monkeypatch):
    monkeypatch.setenv("XAI_API_KEY", "test-key-not-real")
    sources, sha = read_sources(data_file(tmp_path))
    _, eligible = audit_sources(sources, sha)
    jobs, _ = plan_jobs(eligible, small_settings(), "live")
    calls = []
    def handler(request):
        body = json.loads(request.content)
        calls.append(body)
        assert request.url == "https://api.x.ai/v1/responses"
        assert body["store"] is False and body["text"]["format"]["strict"] is True
        return httpx.Response(200, json={"output": [{"content": [{"type": "refusal", "refusal": "test-key-not-real"}]}]})
    async def check():
        client = GrokClient(small_settings(model="configured-model"), transport=httpx.MockTransport(handler))
        try:
            with pytest.raises(ApiFailure) as exc:
                await client.generate(jobs[0])
            assert exc.value.category == "refusal" and "test-key-not-real" not in exc.value.detail
        finally:
            await client.close()
    asyncio.run(check())
    assert len(calls) == 1


def test_resume_never_replays_refusal(tmp_path):
    class Client:
        def __init__(self): self.calls = 0
        async def generate(self, job):
            self.calls += 1
            raise ApiFailure("refusal", "refused")
    fake = Client()
    path = data_file(tmp_path)
    out = tmp_path / "refusal"
    config = small_settings(model="configured-model")
    asyncio.run(run(path, out, config, dry_run=False, client=fake))
    assert fake.calls == 9
    asyncio.run(run(path, out, config, dry_run=False, retry_errors=True, client=fake))
    assert fake.calls == 9


def test_large_run_requires_explicit_switch(tmp_path):
    with pytest.raises(ValueError, match="large-run"):
        asyncio.run(run(data_file(tmp_path), tmp_path / "large", Settings(source_limit=31)))


def test_source_schema_not_silently_repaired(tmp_path):
    rows = [{"caption": 123, "split": "train", "labels": ["safe"]}]
    with pytest.raises(ValidationError):
        read_sources(data_file(tmp_path, rows))


def test_redaction():
    assert "SECRET" not in redact("Authorization: Bearer SECRET", "SECRET")
    assert "xai-abcdef" not in redact("xai-abcdef")


def test_retry_history_preserves_usage_and_completed_jobs(tmp_path):
    class Client:
        def __init__(self): self.calls = 0
        async def generate(self, job):
            self.calls += 1
            if self.calls == 1:
                raise ApiFailure("invalid_schema", "malformed", {"input_tokens": 20, "output_tokens": 5, "total_tokens": 25})
            return offline_candidate(job), {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15}, "mock-model", 1
    client = Client()
    path = data_file(tmp_path)
    out = tmp_path / "retry"
    config = small_settings(model="configured-model")
    first = asyncio.run(run(path, out, config, dry_run=False, client=client))
    assert first["outcomes"] == {"invalid_schema": 1, "success": 8}
    second = asyncio.run(run(path, out, config, dry_run=False, retry_errors=True, client=client))
    assert client.calls == 10 and second["outcomes"] == {"success": 9}
    assert second["tokens_reported_by_api"]["total_tokens"] == 25 + 9 * 15
    assert len((out / "errors.jsonl").read_text(encoding="utf-8").splitlines()) == 1


def test_mock_http_retry_is_bounded(tmp_path, monkeypatch):
    monkeypatch.setenv("XAI_API_KEY", "not-a-real-key")
    sources, sha = read_sources(data_file(tmp_path))
    _, eligible = audit_sources(sources, sha)
    settings = small_settings(model="configured-model", max_retries=2)
    jobs, _ = plan_jobs(eligible, settings, "live")
    calls = []
    delays = []
    def handler(request):
        calls.append(1)
        return httpx.Response(429)
    async def fake_sleep(delay): delays.append(delay)
    monkeypatch.setattr("reid_guardrail.api.asyncio.sleep", fake_sleep)
    async def check():
        client = GrokClient(settings, transport=httpx.MockTransport(handler))
        try:
            with pytest.raises(ApiFailure) as exc:
                await client.generate(jobs[0])
            assert exc.value.category == "http_error" and exc.value.attempts == 3
        finally:
            await client.close()
    asyncio.run(check())
    assert len(calls) == 3 and len(delays) == 2
