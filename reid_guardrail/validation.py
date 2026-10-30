from difflib import SequenceMatcher

from .data import age_info, normalized
from .models import POSITIVE, Span, SyntheticRecord


def spans(before, after):
    return [Span(source_start=i, source_end=j, generated_start=a, generated_end=b,
                 before=before[i:j], after=after[a:b])
            for tag, i, j, a, b in SequenceMatcher(None, before, after, autojunk=False).get_opcodes()
            if tag != "equal"]


class RejectedCandidate(ValueError):
    pass


def make_record(job, candidate, model, requested_model, mode, held_out):
    source = job["source"]
    flags = []
    age, evidence = age_info(source["caption"])
    if source["split"] != "train":
        raise RejectedCandidate("non_train_source")
    if not candidate.caption.strip():
        raise RejectedCandidate("empty_caption")
    if normalized(candidate.caption) in held_out:
        raise RejectedCandidate("generated_held_out_exact_overlap")
    if job["concept"] in POSITIVE or candidate.decision == "block":
        if age != "adult" or age_info(candidate.caption)[0] != "adult":
            raise RejectedCandidate("adult_evidence_missing_or_minor_cue")
        # Exact source evidence must survive; no new age may be invented as a substitute.
        if normalized(evidence) not in normalized(candidate.caption):
            raise RejectedCandidate("source_age_evidence_not_preserved")
    decision = candidate.decision
    if decision != job["target_decision"]:
        flags.append("target_decision_mismatch")
        decision = "review"
    if "seksi" in normalized(candidate.caption).split() and candidate.decision == "allow":
        flags.append("borderline_evaluation_requires_context")
        decision = "review"
    transform = candidate.transformation_type
    if candidate.added_attributes:
        transform = "synthetic_attribute_variant"
    if transform == "minimal_pair" and not job["pair_id"]:
        flags.append("unpaired_minimal_pair_claim")
        decision = "review"
    flags.append("semantic_policy_and_attribute_preservation_need_human_review")
    if mode == "dry_run":
        flags.append("offline_fixture_not_live_generation")
    # These are application suggestions, never ModernBERT class indices or final labels.
    labels = ["safe"] if decision == "allow" else (["adult_sexual_content"] if decision == "block" else ["needs_review"])
    return SyntheticRecord(
        id=job["job_id"], source_id=source["source_id"], source_split="train",
        source_caption=source["caption"], source_metadata=source["metadata"],
        caption=candidate.caption, suggested_labels=labels, suggested_decision=decision,
        generator_decision=candidate.decision, target_decision=job["target_decision"],
        concept=job["concept"], hard_concept=job["hard_concept"], transformation_type=transform,
        pair_id=job["pair_id"], changed_spans=spans(source["caption"], candidate.caption),
        synthetic=True, generator_model=model, requested_model=requested_model,
        prompt_version=job["prompt_version"], review_status="pending", content_safety=decision,
        task_relevance=candidate.task_relevance, policy_rationale=candidate.policy_rationale,
        validation_flags=flags, age_evidence=evidence, split="train", mode=mode)
