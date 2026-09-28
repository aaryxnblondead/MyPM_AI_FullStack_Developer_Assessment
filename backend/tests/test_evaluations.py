from fastapi.testclient import TestClient

from app import models
from app.db import Base, get_db
from app.main import app


def _override_client(tmp_path, name: str):
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker

    db_file = tmp_path / name
    engine = create_engine(f"sqlite:///{db_file}", connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=engine)
    session = sessionmaker(bind=engine)

    def override():
        db = session()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override
    return TestClient(app, raise_server_exceptions=False), session


def test_get_missing_returns_404(tmp_path, monkeypatch):
    c, _ = _override_client(tmp_path, "e.db")
    try:
        assert c.get("/api/evaluations/nope").status_code == 404
        assert c.get("/api/candidates/nope").status_code == 404
    finally:
        app.dependency_overrides.clear()


def test_chunks_endpoint_returns_offsets(tmp_path, monkeypatch):
    c, session = _override_client(tmp_path, "e3.db")
    try:
        db = session()
        cand = models.Candidate(name="Riya Shah", target_role="CSM", resume_text="Used HubSpot daily.")
        db.add(cand)
        db.flush()
        db.add(models.ResumeChunk(
            candidate_id=cand.id, chunk_index=0, section_label="general",
            text="Used HubSpot daily.", char_start=0, char_end=18,
        ))
        db.commit()
        cid = cand.id
        db.close()
        r = c.get(f"/api/candidates/{cid}/chunks")
        assert r.status_code == 200
        body = r.json()
        assert body["resume_text"] == "Used HubSpot daily."
        assert body["chunks"][0]["char_start"] == 0
        assert body["chunks"][0]["char_end"] == 18
    finally:
        app.dependency_overrides.clear()


def test_patch_validates_length(tmp_path, monkeypatch):
    c, session = _override_client(tmp_path, "e2.db")
    try:
        db = session()
        cand = models.Candidate(name="A", target_role="R", resume_text="t")
        db.add(cand)
        db.flush()
        jd = models.JobDescription(company_name="C", job_title="J", jd_text="d")
        db.add(jd)
        db.flush()
        ev = models.Evaluation(candidate_id=cand.id, job_description_id=jd.id, fit_category="Weak Fit")
        db.add(ev)
        db.commit()
        eid = ev.id
        db.close()
        r = c.patch(f"/api/evaluations/{eid}", json={"explanation_edited": "x" * 5001})
        assert r.status_code == 422
        r2 = c.patch(f"/api/evaluations/{eid}", json={"explanation_edited": "Edited note."})
        assert r2.status_code == 200
        assert r2.json()["explanation_edited"] == "Edited note."
    finally:
        app.dependency_overrides.clear()


def test_candidates_list_returns_newest_first(tmp_path, monkeypatch):
    c, session = _override_client(tmp_path, "cands.db")
    try:
        db = session()
        db.add(models.Candidate(name="Asha Rao", target_role="CSM", resume_text="HubSpot work.", resume_structured={"skills": [{"name": "HubSpot", "source": "HubSpot work.", "known": True}]}))
        db.add(models.Candidate(name="Dev Patel", target_role="AE", resume_text="Salesforce work.", resume_structured={"skills": []}))
        db.commit()
        db.close()
        r = c.get("/api/candidates?limit=50&offset=0")
        assert r.status_code == 200
        body = r.json()
        assert len(body) == 2
        assert body[0]["name"] == "Dev Patel"
        first_struct = body[1]["resume_structured"]
        assert first_struct["skills"][0]["name"] == "HubSpot"
    finally:
        app.dependency_overrides.clear()
