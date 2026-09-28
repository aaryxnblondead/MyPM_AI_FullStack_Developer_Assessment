from typing import Any

from pydantic import BaseModel, field_validator


class HealthResponse(BaseModel):
    status: str


def _clean(v: str, limit: int) -> str:
    t = v.strip()
    if not t:
        raise ValueError("must not be empty")
    if len(t) > limit:
        raise ValueError(f"must be at most {limit} chars")
    return t


class IngestRequest(BaseModel):
    candidate_id: str | None = None
    job_description_id: str | None = None
    candidate_name: str
    target_role: str
    resume_text: str
    company_name: str
    job_title: str
    job_description: str

    @field_validator("candidate_name")
    @classmethod
    def _name(cls, v: str) -> str:
        return _clean(v, 200)

    @field_validator("target_role")
    @classmethod
    def _role(cls, v: str) -> str:
        return _clean(v, 200)

    @field_validator("resume_text")
    @classmethod
    def _resume(cls, v: str) -> str:
        return _clean(v, 30000)

    @field_validator("company_name")
    @classmethod
    def _company(cls, v: str) -> str:
        return _clean(v, 200)

    @field_validator("job_title")
    @classmethod
    def _title(cls, v: str) -> str:
        return _clean(v, 200)

    @field_validator("job_description")
    @classmethod
    def _jd(cls, v: str) -> str:
        return _clean(v, 15000)

    @field_validator("candidate_id", "job_description_id", mode="before")
    @classmethod
    def _optional_str(cls, v: str | None) -> str | None:
        if v is None or v == "":
            return None
        return v.strip()


class IngestResponse(BaseModel):
    candidate_id: str
    job_description_id: str
    resume_structured: dict[str, Any]
    requirements: list[dict[str, Any]]
    chunk_count: int
    injection_flagged: bool
    skill_reference_hits: list[dict[str, Any]] = []


class CandidateDetail(BaseModel):
    id: str
    name: str
    target_role: str
    resume_structured: dict[str, Any] | None = None
    chunk_count: int
    injection_flagged: bool


class CandidateListItem(BaseModel):
    id: str
    name: str
    target_role: str
    resume_structured: dict[str, Any] | None = None
    chunk_count: int = 0
    injection_flagged: bool = False
    created_at: Any = None


class ChunkItem(BaseModel):
    id: str
    chunk_index: int
    section_label: str
    text: str
    char_start: int
    char_end: int


class CandidateChunks(BaseModel):
    candidate_id: str
    name: str
    resume_text: str
    chunks: list[ChunkItem]


class EvaluationCreate(IngestRequest):
    pass


class EvaluationRecord(BaseModel):
    id: str
    candidate_id: str
    job_description_id: str
    candidate_name: str = ""
    company_name: str = ""
    job_title: str = ""
    fit_category: str | None = None
    fit_score: float | None = None
    per_requirement: list[dict[str, Any]] | None = None
    explanation: str | None = None
    explanation_edited: str | None = None
    outreach_subject: str | None = None
    outreach_subject_edited: str | None = None
    outreach_body: str | None = None
    outreach_body_edited: str | None = None
    injection_flagged: bool = False
    injection_notes: str = ""
    created_at: Any = None


class EvaluationListItem(BaseModel):
    id: str
    candidate_name: str = ""
    company_name: str = ""
    job_title: str = ""
    fit_category: str | None = None
    fit_score: float | None = None
    created_at: Any = None


class EvaluationPatch(BaseModel):
    explanation_edited: str | None = None
    outreach_subject_edited: str | None = None
    outreach_body_edited: str | None = None
