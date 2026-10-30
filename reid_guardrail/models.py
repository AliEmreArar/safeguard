from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

Decision = Literal["allow", "block", "review"]
Concept = Literal["normal_safe", "hard_safe", "objectification", "sexual_intent", "sexual_harassment"]
Transformation = Literal["paraphrase", "synthetic_attribute_variant", "minimal_pair", "natural_query"]
POSITIVE = {"objectification", "sexual_intent", "sexual_harassment"}


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)


class Candidate(StrictModel):
    caption: str = Field(min_length=1, max_length=2000)
    decision: Decision
    task_relevance: Literal["relevant", "partial", "irrelevant", "uncertain"]
    transformation_type: Transformation
    added_attributes: bool
    policy_rationale: str = Field(min_length=1, max_length=700)


class Envelope(StrictModel):
    status: Literal["ok", "refused"]
    candidate: Candidate | None
    refusal_reason: str | None


class Span(StrictModel):
    source_start: int
    source_end: int
    generated_start: int
    generated_end: int
    before: str
    after: str


class SyntheticRecord(StrictModel):
    id: str
    source_id: str
    source_split: Literal["train"]
    source_caption: str
    source_metadata: dict
    caption: str = Field(min_length=1, max_length=2000)
    suggested_labels: list[str]
    suggested_decision: Decision
    generator_decision: Decision
    target_decision: Decision
    concept: Concept
    hard_concept: str | None
    transformation_type: Transformation
    pair_id: str | None
    changed_spans: list[Span]
    synthetic: Literal[True]
    generator_model: str
    requested_model: str
    prompt_version: str
    review_status: Literal["pending"]
    content_safety: Decision
    task_relevance: Literal["relevant", "partial", "irrelevant", "uncertain"]
    policy_rationale: str
    validation_flags: list[str]
    age_evidence: str | None
    split: Literal["train"]
    mode: Literal["dry_run", "live"]


class Settings(StrictModel):
    source_limit: int = Field(default=30, ge=1, le=100000)
    quotas: dict[str, int] = Field(default_factory=lambda: {
        "normal_safe": 30, "hard_safe": 30, "objectification": 10,
        "sexual_intent": 10, "sexual_harassment": 10})
    model: str = ""
    concurrency: int = Field(default=2, ge=1, le=16)
    timeout_seconds: float = Field(default=90, gt=0, le=600)
    max_retries: int = Field(default=2, ge=0, le=5)
    temperature: float = Field(default=0.8, ge=0, le=1)
    max_output_tokens: int = Field(default=900, ge=100, le=4096)
    seed: int = 42
    prompt_version: Literal["v1"] = "v1"
