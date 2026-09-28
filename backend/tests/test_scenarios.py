import json
import textwrap
from pathlib import Path
from sqlalchemy import text

import pytest

from app import models
from app.services import ingest as ingest_svc
from app.services import pipeline
from app.services.evaluator import evaluate_candidate
from app.services.explanation import build_explanation
from app.services.outreach import build_outreach, post_check_email

FIXTURES = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> dict:
    return json.loads((FIXTURES / name).read_text())


def test_standard_riya_shah_mocked(monkeypatch, tmp_path):
    """Standard scenario: Riya's resume vs JD. Mocked LLM."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    fixture = load_fixture("riya_shah.json")

    monkeypatch.setattr(
        "app.services.embedder.embed_query",
        lambda _t: [1.0, 0.0, 0.0, 0.0],
    )
    monkeypatch.setattr(
        "app.services.embedder.embed_documents",
        lambda texts: [[1.0, 0.0, 0.0, 0.0] for _ in texts],
    )
    monkeypatch.setattr(
        "app.services.resume_extractor.extract_resume",
        lambda _t: {
            "skills": [{"name": "HubSpot", "source": "used HubSpot"}, {"name": "Customer Success", "source": "customer success experience"}],
            "education": [],
            "total_years_experience": 5,
            "roles": [{"title": "Customer Success Manager", "company": "Previous Co", "start": "2019", "end": "2024", "bullets": ["Managed 25 client accounts", "Used HubSpot", "Improved retention by 12%"], "source": "five years of B2B SaaS customer success experience"}],
            "metrics": [{"statement": "Improved customer retention by 12%", "source": "improved customer retention by 12 percent"}],
        },
    )
    monkeypatch.setattr(
        "app.services.jd_parser.parse_jd",
        lambda _t: [
            {"id": "r1", "text": "Five years of experience", "category": "experience", "must_have": True},
            {"id": "r2", "text": "Salesforce", "category": "tool", "must_have": True},
            {"id": "r3", "text": "Enterprise renewals", "category": "skill", "must_have": True},
            {"id": "r4", "text": "Experience supporting US customers", "category": "domain", "must_have": True},
        ],
    )
    monkeypatch.setattr(
        "app.services.evaluator.judge_one",
        lambda req, chunks: {
            "requirement_id": req["id"],
            "verdict": "met" if req["id"] == "r1" else "no_evidence",
            "evidence": [{"chunk_id": chunks[0].id, "quote": "five years of B2B SaaS customer success experience"}] if req["id"] == "r1" else [],
            "reasoning": "Mocked",
        },
    )
    monkeypatch.setattr("app.services.explanation.build_explanation", lambda _r: "Riya Shah matches the experience requirement but lacks Salesforce, enterprise renewals, and US customer experience.")
    monkeypatch.setattr(
        "app.services.outreach.build_outreach",
        lambda _n, _c, _j, _r: {"subject": "Opportunity at Acme Corp", "body": "Hi Riya, Your HubSpot and client management experience caught our attention. We'd love to chat."},
    )

    db_file = tmp_path / "scenario.db"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    from app.db import Base
    from sqlalchemy import event
    @event.listens_for(engine, "connect")
    def _load(dbapi_conn, _rec):
        import sqlite_vec
        dbapi_conn.enable_load_extension(True)
        dbapi_conn.load_extension(sqlite_vec.loadable_path())
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        conn.execute(text("CREATE VIRTUAL TABLE IF NOT EXISTS resume_chunk_vectors USING vec0(chunk_id TEXT, embedding FLOAT[4] distance_metric=cosine)"))
    monkeypatch.setattr("app.services.vectors.settings.embedding_dim", 4)
    Session = sessionmaker(bind=engine)
    db = Session()

    cand = models.Candidate(name=fixture["candidate_name"], target_role=fixture["target_role"], resume_text=fixture["resume_text"])
    db.add(cand)
    db.flush()
    chunk = models.ResumeChunk(candidate_id=cand.id, chunk_index=0, section_label="general", text=fixture["resume_text"], char_start=0, char_end=len(fixture["resume_text"]))
    db.add(chunk)
    db.flush()
    db.execute(text("INSERT INTO resume_chunk_vectors(chunk_id, embedding) VALUES (:c, '[1,0,0,0]')"), {"c": chunk.id})
    jd = models.JobDescription(company_name=fixture["company_name"], job_title=fixture["job_title"], jd_text=fixture["job_description"], requirements_structured=[
        {"id": "r1", "text": "Five years of experience", "category": "experience", "must_have": True},
        {"id": "r2", "text": "Salesforce", "category": "tool", "must_have": True},
        {"id": "r3", "text": "Enterprise renewals", "category": "skill", "must_have": True},
        {"id": "r4", "text": "Experience supporting US customers", "category": "domain", "must_have": True},
    ])
    db.add(jd)
    db.commit()

    result = pipeline.run_evaluation(db, cand.id, jd.id)

    assert result.fit_category in ("Moderate Fit", "Weak Fit")
    assert result.per_requirement is not None
    by_id = {r["requirement_id"]: r for r in result.per_requirement}
    assert by_id["r1"]["verdict"] == "met"
    assert by_id["r2"]["verdict"] == "no_evidence"
    assert by_id["r2"]["display"] == "No evidence found in resume"
    assert by_id["r3"]["verdict"] == "no_evidence"
    assert by_id["r4"]["verdict"] == "no_evidence"
    assert "Salesforce" not in (result.outreach_body or "")
    assert "renewals" not in (result.outreach_body or "")
    assert "US customer" not in (result.outreach_body or "")
    assert "HubSpot" in (result.outreach_body or "")


def test_injection_prompt_mocked(monkeypatch, tmp_path):
    """Injection scenario: resume contains instruction. Should be flagged and not inflate score."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    fixture = load_fixture("riya_shah_injection.json")

    monkeypatch.setattr(
        "app.services.embedder.embed_query",
        lambda _t: [1.0, 0.0, 0.0, 0.0],
    )
    monkeypatch.setattr(
        "app.services.embedder.embed_documents",
        lambda texts: [[1.0, 0.0, 0.0, 0.0] for _ in texts],
    )
    monkeypatch.setattr(
        "app.services.resume_extractor.extract_resume",
        lambda _t: {"skills": [], "education": [], "total_years_experience": 5, "roles": [], "metrics": []},
    )
    monkeypatch.setattr(
        "app.services.jd_parser.parse_jd",
        lambda _t: [{"id": "r1", "text": "Salesforce", "category": "tool", "must_have": True}],
    )
    monkeypatch.setattr(
        "app.services.evaluator.judge_one",
        lambda req, chunks: {
            "requirement_id": req["id"],
            "verdict": "no_evidence",
            "evidence": [],
            "reasoning": "Mocked",
        },
    )
    monkeypatch.setattr("app.services.explanation.build_explanation", lambda _r: "No evidence found for required skills.")
    monkeypatch.setattr(
        "app.services.outreach.build_outreach",
        lambda _n, _c, _j, _r: {"subject": "Hi", "body": "Short note."},
    )

    db_file = tmp_path / "scenario_inj.db"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    from app.db import Base
    from sqlalchemy import event
    @event.listens_for(engine, "connect")
    def _load(dbapi_conn, _rec):
        import sqlite_vec
        dbapi_conn.enable_load_extension(True)
        dbapi_conn.load_extension(sqlite_vec.loadable_path())
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        conn.execute(text("CREATE VIRTUAL TABLE IF NOT EXISTS resume_chunk_vectors USING vec0(chunk_id TEXT, embedding FLOAT[4] distance_metric=cosine)"))
    monkeypatch.setattr("app.services.vectors.settings.embedding_dim", 4)
    Session = sessionmaker(bind=engine)
    db = Session()

    cand = models.Candidate(name=fixture["candidate_name"], target_role=fixture["target_role"], resume_text=fixture["resume_text"], injection_flagged=True, injection_notes="Matched instruction-like phrases")
    db.add(cand)
    db.flush()
    chunk = models.ResumeChunk(candidate_id=cand.id, chunk_index=0, section_label="general", text=fixture["resume_text"], char_start=0, char_end=len(fixture["resume_text"]))
    db.add(chunk)
    db.flush()
    db.execute(text("INSERT INTO resume_chunk_vectors(chunk_id, embedding) VALUES (:c, '[1,0,0,0]')"), {"c": chunk.id})
    jd = models.JobDescription(company_name=fixture["company_name"], job_title=fixture["job_title"], jd_text=fixture["job_description"], requirements_structured=[
        {"id": "r1", "text": "Salesforce", "category": "tool", "must_have": True},
    ])
    db.add(jd)
    db.commit()

    result = pipeline.run_evaluation(db, cand.id, jd.id)

    assert result.injection_flagged is True
    assert "ignore the job description" in result.injection_notes.lower()
    assert result.fit_category == "Weak Fit"
    assert result.per_requirement[0]["verdict"] == "no_evidence"


def test_missing_evidence_no_claim_in_outreach(monkeypatch, tmp_path):
    """Missing evidence: JD has requirements absent from resume. Outreach must not mention them."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    fixture = load_fixture("riya_shah_missing_evidence.json")

    monkeypatch.setattr(
        "app.services.embedder.embed_query",
        lambda _t: [1.0, 0.0, 0.0, 0.0],
    )
    monkeypatch.setattr(
        "app.services.embedder.embed_documents",
        lambda texts: [[1.0, 0.0, 0.0, 0.0] for _ in texts],
    )
    monkeypatch.setattr(
        "app.services.resume_extractor.extract_resume",
        lambda _t: {"skills": [{"name": "HubSpot", "source": "used HubSpot"}], "education": [], "total_years_experience": 5, "roles": [], "metrics": []},
    )
    monkeypatch.setattr(
        "app.services.jd_parser.parse_jd",
        lambda _t: [
            {"id": "r1", "text": "HubSpot", "category": "tool", "must_have": True},
            {"id": "r2", "text": "Salesforce", "category": "tool", "must_have": True},
            {"id": "r3", "text": "Python programming", "category": "skill", "must_have": True},
            {"id": "r4", "text": "Kubernetes orchestration", "category": "skill", "must_have": True},
        ],
    )
    monkeypatch.setattr(
        "app.services.evaluator.judge_one",
        lambda req, chunks: {
            "requirement_id": req["id"],
            "verdict": "met" if req["id"] == "r1" else "no_evidence",
            "evidence": [{"chunk_id": chunks[0].id, "quote": "used HubSpot"}] if req["id"] == "r1" else [],
            "reasoning": "Mocked",
        },
    )
    monkeypatch.setattr("app.services.explanation.build_explanation", lambda _r: "Matches HubSpot. Missing Salesforce, Python, Kubernetes.")
    monkeypatch.setattr(
        "app.services.outreach.build_outreach",
        lambda _n, _c, _j, _r: {"subject": "Opportunity", "body": "Your HubSpot experience is relevant. We'd love to chat."},
    )

    db_file = tmp_path / "scenario_miss.db"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    from app.db import Base
    from sqlalchemy import event
    @event.listens_for(engine, "connect")
    def _load(dbapi_conn, _rec):
        import sqlite_vec
        dbapi_conn.enable_load_extension(True)
        dbapi_conn.load_extension(sqlite_vec.loadable_path())
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        conn.execute(text("CREATE VIRTUAL TABLE IF NOT EXISTS resume_chunk_vectors USING vec0(chunk_id TEXT, embedding FLOAT[4] distance_metric=cosine)"))
    monkeypatch.setattr("app.services.vectors.settings.embedding_dim", 4)
    Session = sessionmaker(bind=engine)
    db = Session()

    cand = models.Candidate(name=fixture["candidate_name"], target_role=fixture["target_role"], resume_text=fixture["resume_text"])
    db.add(cand)
    db.flush()
    chunk = models.ResumeChunk(candidate_id=cand.id, chunk_index=0, section_label="general", text=fixture["resume_text"], char_start=0, char_end=len(fixture["resume_text"]))
    db.add(chunk)
    db.flush()
    db.execute(text("INSERT INTO resume_chunk_vectors(chunk_id, embedding) VALUES (:c, '[1,0,0,0]')"), {"c": chunk.id})
    jd = models.JobDescription(company_name=fixture["company_name"], job_title=fixture["job_title"], jd_text=fixture["job_description"], requirements_structured=[
        {"id": "r1", "text": "HubSpot", "category": "tool", "must_have": True},
        {"id": "r2", "text": "Salesforce", "category": "tool", "must_have": True},
        {"id": "r3", "text": "Python programming", "category": "skill", "must_have": True},
        {"id": "r4", "text": "Kubernetes orchestration", "category": "skill", "must_have": True},
    ])
    db.add(jd)
    db.commit()

    result = pipeline.run_evaluation(db, cand.id, jd.id)

    assert result.per_requirement is not None
    by_id = {r["requirement_id"]: r for r in result.per_requirement}
    assert by_id["r1"]["verdict"] == "met"
    assert by_id["r2"]["verdict"] == "no_evidence"
    assert by_id["r3"]["verdict"] == "no_evidence"
    assert by_id["r4"]["verdict"] == "no_evidence"

    body = result.outreach_body or ""
    assert "Salesforce" not in body
    assert "Python" not in body
    assert "Kubernetes" not in body
    assert "HubSpot" in body


def test_bad_inputs_rejected():
    """Bad inputs should return 422 with clear errors."""
    from fastapi.testclient import TestClient
    from app.main import app

    client = TestClient(app, raise_server_exceptions=False)

    empty = {"candidate_name": "", "target_role": "x", "resume_text": "x", "company_name": "x", "job_title": "x", "job_description": "x"}
    r = client.post("/api/evaluations", json=empty)
    assert r.status_code == 422

    long_resume = {"candidate_name": "Test", "target_role": "Role", "resume_text": "A" * 35000, "company_name": "Co", "job_title": "Title", "job_description": "Need Python"}
    r = client.post("/api/evaluations", json=long_resume)
    assert r.status_code == 422

    long_jd = {"candidate_name": "Test", "target_role": "Role", "resume_text": "Has Python", "company_name": "Co", "job_title": "Title", "job_description": "B" * 20000}
    r = client.post("/api/evaluations", json=long_jd)
    assert r.status_code == 422


def test_persistence_reopen_edit(monkeypatch, tmp_path):
    """Create, reopen, edit explanation and email, reopen again."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    fixture = load_fixture("riya_shah.json")

    monkeypatch.setattr("app.services.embedder.embed_query", lambda _t: [1.0, 0.0, 0.0, 0.0])
    monkeypatch.setattr("app.services.embedder.embed_documents", lambda texts: [[1.0, 0.0, 0.0, 0.0] for _ in texts])
    monkeypatch.setattr("app.services.resume_extractor.extract_resume", lambda _t: {"skills": [], "education": [], "total_years_experience": 5, "roles": [], "metrics": []})
    monkeypatch.setattr("app.services.jd_parser.parse_jd", lambda _t: [{"id": "r1", "text": "HubSpot", "category": "tool", "must_have": True}])
    monkeypatch.setattr("app.services.evaluator.judge_one", lambda req, chunks: {"requirement_id": req["id"], "verdict": "met", "evidence": [{"chunk_id": chunks[0].id, "quote": "used HubSpot"}], "reasoning": "Mocked"})
    monkeypatch.setattr("app.services.explanation.build_explanation", lambda _r: "Original explanation.")
    monkeypatch.setattr("app.services.outreach.build_outreach", lambda _n, _c, _j, _r: {"subject": "Hi", "body": "Original body."})

    db_file = tmp_path / "persist.db"
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    from app.db import Base
    from sqlalchemy import event
    @event.listens_for(engine, "connect")
    def _load(dbapi_conn, _rec):
        import sqlite_vec
        dbapi_conn.enable_load_extension(True)
        dbapi_conn.load_extension(sqlite_vec.loadable_path())
    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        conn.execute(text("CREATE VIRTUAL TABLE IF NOT EXISTS resume_chunk_vectors USING vec0(chunk_id TEXT, embedding FLOAT[4] distance_metric=cosine)"))
    monkeypatch.setattr("app.services.vectors.settings.embedding_dim", 4)
    Session = sessionmaker(bind=engine)
    db = Session()

    cand = models.Candidate(name=fixture["candidate_name"], target_role=fixture["target_role"], resume_text=fixture["resume_text"])
    db.add(cand)
    db.flush()
    chunk = models.ResumeChunk(candidate_id=cand.id, chunk_index=0, section_label="general", text=fixture["resume_text"], char_start=0, char_end=len(fixture["resume_text"]))
    db.add(chunk)
    db.flush()
    db.execute(text("INSERT INTO resume_chunk_vectors(chunk_id, embedding) VALUES (:c, '[1,0,0,0]')"), {"c": chunk.id})
    jd = models.JobDescription(company_name=fixture["company_name"], job_title=fixture["job_title"], jd_text=fixture["job_description"], requirements_structured=[{"id": "r1", "text": "HubSpot", "category": "tool", "must_have": True}])
    db.add(jd)
    db.commit()

    rec1 = pipeline.run_evaluation(db, cand.id, jd.id)
    assert rec1.explanation == "Original explanation."
    assert rec1.outreach_body == "Original body."

    rec1.explanation_edited = "Edited explanation."
    rec1.outreach_body_edited = "Edited body."
    db.commit()
    db.refresh(rec1)

    rec2 = db.get(models.Evaluation, rec1.id)
    assert rec2.explanation_edited == "Edited explanation."
    assert rec2.outreach_body_edited == "Edited body."


if __name__ == "__main__":
    pytest.main([__file__, "-v"])