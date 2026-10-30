from pathlib import Path

import pytest

from reid_guardrail.excel_contrast import ContrastBundle, ContrastEnvelope, extract_sources, variant_record, user_controls
from reid_guardrail.models import Candidate


def candidate(caption, decision="allow"):
    return Candidate(caption=caption, decision=decision, task_relevance="relevant",
                     transformation_type="synthetic_attribute_variant", added_attributes=True, policy_rationale="test")


def test_real_excel_plan_is_ten_sources_and_two_adults():
    path = Path("Guardrail Test - query_final_tr (modernbert-tr-guardrail).xlsx")
    if not path.exists():
        pytest.skip("Yerel kullanıcı raporu yok")
    rows, audit = extract_sources(path, "merged_captions.json")
    assert len(rows) == 10 and audit["selected_adult_sources"] == 2
    assert all(r["source_split"] == "evaluation_report_unknown_split" for r in rows)
    assert rows[0]["filename"] == "27082_3.jpg"


def test_sexual_variants_cannot_add_source_age():
    source = {"caption": "koyu saçlı kadın", "source_id": "x", "filename": "x.jpg", "row": 1,
              "source_split": "evaluation_report_unknown_split"}
    with pytest.raises(ValueError, match="adult"):
        variant_record(source, "objectifying_variant", candidate("yetişkin kadın", "block"), "mock", "job")


def test_boundary_is_review_even_if_generator_says_block():
    source = {"caption": "yetişkin kadın", "source_id": "x", "filename": "x.jpg", "row": 1,
              "source_split": "evaluation_report_unknown_split"}
    record = variant_record(source, "borderline_variant", candidate("yetişkin kadın, ince belli", "block"), "mock", "job")
    assert record["suggested_decision"] == "review"
    assert record["generator_decision"] == "block" and record["review_status"] == "pending"


def test_null_adult_variants_are_supported_by_schema():
    bundle = ContrastBundle(safe_variant=candidate("daracık tayt giyen kişi"), borderline_variant=None, objectifying_variant=None)
    envelope = ContrastEnvelope(status="ok", candidate=bundle, refusal_reason=None)
    assert ContrastEnvelope.model_validate_json(envelope.model_dump_json()).candidate.objectifying_variant is None


def test_user_proposed_block_is_separate_from_policy_suggestion():
    path = Path("Guardrail Test - query_final_tr (modernbert-tr-guardrail).xlsx")
    if not path.exists():
        pytest.skip("Yerel kullanıcı raporu yok")
    rows, _ = extract_sources(path, "merged_captions.json")
    probes = user_controls(rows[0])
    assert len(probes) == 3
    assert all(p["user_proposed_decision"] == "block" for p in probes)
    assert [p["suggested_decision"] for p in probes] == ["allow", "allow", "review"]
    assert "daracık tayt" in probes[0]["caption"]
