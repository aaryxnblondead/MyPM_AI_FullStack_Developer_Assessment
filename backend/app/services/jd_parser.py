from typing import Any

from fastapi import HTTPException
from pydantic import BaseModel


class Requirement(BaseModel):
    id: str
    text: str
    category: str = "general"
    must_have: bool = True


class RequirementsDoc(BaseModel):
    requirements: list[Requirement]


def validate_requirements(data: dict[str, Any]) -> list[dict[str, Any]]:
    doc = RequirementsDoc.model_validate(data)
    return [r.model_dump() for r in doc.requirements]


def parse_jd(jd_text: str) -> list[dict[str, Any]]:
    from app.prompts.jd_parse import JD_SCHEMA, JD_SYSTEM, jd_user
    from app.services.llm import generate_json

    first = generate_json(JD_SYSTEM, jd_user(jd_text), JD_SCHEMA)
    try:
        return validate_requirements(first)
    except Exception:
        pass
    repair = JD_SYSTEM + " Fix the JSON so it matches the schema exactly."
    second = generate_json(repair, jd_user(jd_text), JD_SCHEMA)
    try:
        return validate_requirements(second)
    except Exception as e:
        raise HTTPException(status_code=502, detail="Job parsing failed validation. Try again.") from e
