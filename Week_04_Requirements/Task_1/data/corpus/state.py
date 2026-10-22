from typing import Literal, TypedDict

from pydantic import BaseModel, ConfigDict, Field, StrictBool


class StrictSchema(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Candidate(StrictSchema):
    category: str = Field(min_length=1)
    raw_text: str = Field(min_length=1)
    evidence_quote: str = Field(min_length=1, description="Exact supporting source excerpt")
    kind: Literal["requirement", "preference", "proposed_solution", "gap"]
    priority_hint: str = Field(description="Explicit priority in source, or 'unspecified'")


class Extraction(StrictSchema):
    requirements: list[Candidate]


class Requirement(StrictSchema):
    id: str = Field(pattern=r"^REQ-\d{3,}$")
    name: str = Field(min_length=1)
    description: str = Field(min_length=1)
    priority: Literal["High", "Medium", "Low"]
    priority_reason: str = Field(min_length=1)
    sources: list[str] = Field(min_length=1)
    candidate_ids: list[str]


class RejectedRequirement(StrictSchema):
    id: str = Field(pattern=r"^BL-\d{3,}$")
    name: str = Field(min_length=1)
    rejected_statement: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    sources: list[str] = Field(min_length=1)
    candidate_ids: list[str] = Field(min_length=1)


class RequirementsDocument(StrictSchema):
    title: str = Field(min_length=1)
    scope: str = Field(min_length=1)
    requirements: list[Requirement] = Field(min_length=1)
    blacklist: list[RejectedRequirement]
    open_questions: list[str]


class Review(StrictSchema):
    approved: StrictBool
    issues: list[str]


class AgentState(TypedDict, total=False):
    input_dir: str
    exclude_patterns: list[str]
    max_rounds: int
    raw_documents: list[dict]
    extracted_requirements: list[dict]
    structured_document: dict
    final_requirements_doc: str
    validator_feedback: list[str]
    validation_passed: bool
    loop_count: int
    document_unchanged: bool
    stop_reason: str
    validation_history: list[dict]
