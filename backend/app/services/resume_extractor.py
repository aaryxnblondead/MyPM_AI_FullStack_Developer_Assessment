from typing import Any

from fastapi import HTTPException
from pydantic import BaseModel, Field


class SkillItem(BaseModel):
    name: str
    source: str


class EduItem(BaseModel):
    detail: str
    source: str


class RoleItem(BaseModel):
    title: str
    company: str = ""
    start: str | None = None
    end: str | None = None
    bullets: list[str] = Field(default_factory=list)
    source: str = ""


class MetricItem(BaseModel):
    statement: str
    source: str


class ResumeStructured(BaseModel):
    skills: list[SkillItem] = Field(default_factory=list)
    education: list[EduItem] = Field(default_factory=list)
    total_years_experience: float | None = None
    roles: list[RoleItem] = Field(default_factory=list)
    metrics: list[MetricItem] = Field(default_factory=list)


def validate_resume(data: dict[str, Any]) -> dict[str, Any]:
    return ResumeStructured.model_validate(data).model_dump()


def extract_resume(resume_text: str) -> dict[str, Any]:
    from app.prompts.resume_extract import RESUME_SCHEMA, RESUME_SYSTEM, resume_user
    from app.services.llm import generate_json

    first = generate_json(RESUME_SYSTEM, resume_user(resume_text), RESUME_SCHEMA)
    try:
        return validate_resume(first)
    except Exception:
        pass
    repair_system = RESUME_SYSTEM + " Fix the JSON so it matches the schema exactly."
    second = generate_json(repair_system, resume_user(resume_text), RESUME_SCHEMA)
    try:
        return validate_resume(second)
    except Exception as e:
        raise HTTPException(status_code=502, detail="Resume extraction failed validation. Try again.") from e
