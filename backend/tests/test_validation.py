import pytest
from fastapi import HTTPException

from app.services import jd_parser, resume_extractor


def test_resume_validation_rejects_bad_shape():
    with pytest.raises(Exception):
        resume_extractor.validate_resume({"skills": "not-a-list"})


def test_resume_repair_path(monkeypatch):
    calls = {"n": 0}

    def fake_generate(_s, _u, _sch):
        calls["n"] += 1
        if calls["n"] == 1:
            return {"skills": "bad"}
        return {
            "skills": [{"name": "HubSpot", "source": "used HubSpot"}],
            "education": [],
            "total_years_experience": 5,
            "roles": [],
            "metrics": [],
        }

    monkeypatch.setattr("app.services.llm.generate_json", fake_generate)
    out = resume_extractor.extract_resume("used HubSpot for five years")
    assert out["skills"][0]["name"] == "HubSpot"
    assert calls["n"] == 2


def test_resume_double_fail_raises_502(monkeypatch):
    monkeypatch.setattr("app.services.llm.generate_json", lambda *_a: {"skills": "bad"})
    with pytest.raises(HTTPException) as e:
        resume_extractor.extract_resume("x")
    assert e.value.status_code == 502


def test_jd_repair_path(monkeypatch):
    calls = {"n": 0}

    def fake_generate(_s, _u, _sch):
        calls["n"] += 1
        if calls["n"] == 1:
            return {"requirements": [{"text": "missing id"}]}
        return {"requirements": [{"id": "r1", "text": "Know Salesforce", "category": "tool", "must_have": True}]}

    monkeypatch.setattr("app.services.llm.generate_json", fake_generate)
    out = jd_parser.parse_jd("Need Salesforce")
    assert out[0]["id"] == "r1"
