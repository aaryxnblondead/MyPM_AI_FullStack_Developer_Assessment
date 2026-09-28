from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from app import models
from app.db import Base
from app.services import pipeline


def _session(tmp_path, monkeypatch, engine_factory):
    import sqlalchemy

    db_file = tmp_path / "p.db"
    engine = engine_factory(f"sqlite:///{db_file}")

    @sqlalchemy.event.listens_for(engine, "connect")
    def _load(dbapi_conn, _rec):
        import sqlite_vec

        dbapi_conn.enable_load_extension(True)
        dbapi_conn.load_extension(sqlite_vec.loadable_path())

    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        conn.execute(
            text("CREATE VIRTUAL TABLE IF NOT EXISTS resume_chunk_vectors USING vec0(chunk_id TEXT, embedding FLOAT[4] distance_metric=cosine)")
        )
    monkeypatch.setattr("app.services.vectors.settings.embedding_dim", 4)
    return sessionmaker(bind=engine)()


def test_pipeline_persists_record(monkeypatch, tmp_path):
    from sqlalchemy import create_engine as _ce

    monkeypatch.setattr(
        "app.services.embedder.embed_query", lambda _t: [1.0, 0.0, 0.0, 0.0]
    )
    monkeypatch.setattr(
        "app.services.embedder.embed_documents",
        lambda texts: [[1.0, 0.0, 0.0, 0.0] for _ in texts],
    )
    monkeypatch.setattr(
        "app.services.evaluator.retrieve_chunks",
        lambda db, cid, req: db.query(models.ResumeChunk).filter_by(candidate_id=cid).all()[:4],
    )
    monkeypatch.setattr(
        "app.services.evaluator.judge_one",
        lambda req, chunks: {
            "requirement_id": req["id"],
            "verdict": "met" if req["id"] == "r1" else "no_evidence",
            "evidence": [{"chunk_id": chunks[0].id, "quote": chunks[0].text}] if req["id"] == "r1" else [],
            "reasoning": "mocked",
        },
    )
    monkeypatch.setattr("app.services.explanation.build_explanation", lambda _r: "Mocked summary.")
    monkeypatch.setattr(
        "app.services.outreach.build_outreach",
        lambda _n, _c, _j, _r: {"subject": "Hi", "body": "Short note under limit."},
    )
    db = _session(tmp_path, monkeypatch, _ce)
    cand = models.Candidate(name="Riya Shah", target_role="CSM", resume_text="Used HubSpot.")
    db.add(cand)
    db.flush()
    chunk = models.ResumeChunk(
        candidate_id=cand.id, chunk_index=0, section_label="general",
        text="Used HubSpot.", char_start=0, char_end=12,
    )
    db.add(chunk)
    db.flush()
    db.execute(
        text("INSERT INTO resume_chunk_vectors(chunk_id, embedding) VALUES (:c, '[1,0,0,0]')"),
        {"c": chunk.id},
    )
    jd = models.JobDescription(
        company_name="Acme", job_title="CSM", jd_text="Need HubSpot and Salesforce.",
        requirements_structured=[
            {"id": "r1", "text": "Used HubSpot", "category": "tool", "must_have": True},
            {"id": "r2", "text": "Know Salesforce", "category": "tool", "must_have": True},
        ],
    )
    db.add(jd)
    db.commit()

    record = pipeline.run_evaluation(db, cand.id, jd.id)
    assert record.fit_category in ("Strong Fit", "Moderate Fit", "Weak Fit")
    assert record.per_requirement is not None
    by_id = {r["requirement_id"]: r for r in record.per_requirement}
    assert by_id["r1"]["verdict"] == "met"
    assert by_id["r2"]["verdict"] == "no_evidence"
    assert record.explanation == "Mocked summary."
    assert record.outreach_subject == "Hi"
