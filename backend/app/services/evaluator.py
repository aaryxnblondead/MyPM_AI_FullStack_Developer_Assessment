import re
from typing import Any

from fastapi import HTTPException
from pydantic import BaseModel, field_validator
from sqlalchemy.orm import Session

from app import models
from app.config import settings
from app.prompts.judge import JUDGE_SCHEMA, JUDGE_SYSTEM, judge_batch_user
from app.services import embedder, isolation, vectors
from app.services.llm import generate_json
from app.services.scoring import NO_EVIDENCE_TEXT


class Evidence(BaseModel):
    chunk_id: str
    quote: str


class JudgeItem(BaseModel):
    requirement_id: str
    verdict: str
    evidence: list[Evidence] = []
    reasoning: str = ""

    @field_validator("verdict")
    @classmethod
    def _verdict(cls, v: str) -> str:
        if v not in ("met", "partial", "no_evidence"):
            raise ValueError("bad verdict")
        return v


def norm(s: str) -> str:
    return re.sub(r"\s+", " ", s.strip().lower())


STOPWORDS = frozenset(
    "the,a,an,and,or,for,with,from,that,this,have,has,had,will,shall,should,must,need,needs,"
    "required,requirement,requirements,experience,experienced,years,year,including,include,"
    "candidate,lists,list,skill,skills,ability,strong,plus,role,job,work,using,use,used,production,"
    "project,core,explicitly,there,mention,provided,only,into,backend,frontend".split(",")
)

KEYWORD_MIN_LEN = 4
KEYWORD_EXTRA = 4


def _keywords(text: str) -> set[str]:
    tokens = re.findall(r"[a-z0-9]+", text.lower())
    out: set[str] = set()
    for t in tokens:
        if len(t) < KEYWORD_MIN_LEN:
            continue
        if t in STOPWORDS:
            continue
        out.add(t)
    return out


def retrieve_chunks(db: Session, candidate_id: str, requirement_text: str) -> list[models.ResumeChunk]:
    qvec = embedder.embed_query(requirement_text)
    hits = vectors.nearest_chunks_for_candidate(db, candidate_id, qvec, settings.retrieval_k)
    ids = [cid for cid, _ in hits]
    rows = db.query(models.ResumeChunk).filter(models.ResumeChunk.id.in_(ids)).all() if ids else []
    order = {cid: i for i, (cid, _) in enumerate(hits)}
    rows.sort(key=lambda r: order.get(r.id, 999))
    # Keyword fallback: vector search is semantic and can miss an exact
    # skill mention (e.g. PostgreSQL) buried mid-chunk. Union in chunks that
    # literally contain distinctive requirement terms so the judge sees them.
    try:
        keys = _keywords(requirement_text)
        if keys:
            seen = {r.id for r in rows}
            all_rows = db.query(models.ResumeChunk).filter_by(candidate_id=candidate_id).all()
            scored: list[tuple[int, models.ResumeChunk]] = []
            for c in all_rows:
                if c.id in seen:
                    continue
                hay = norm(c.text or "")
                n = sum(1 for k in keys if k in hay)
                if n:
                    scored.append((n, c))
            scored.sort(key=lambda p: (-p[0], p[1].chunk_index))
            for _, c in scored[:KEYWORD_EXTRA]:
                rows.append(c)
                seen.add(c.id)
    except Exception:
        pass
    return rows


def verify_item(raw: dict[str, Any], retrieved: dict[str, models.ResumeChunk]) -> dict[str, Any]:
    item = JudgeItem.model_validate(raw)
    kept: list[dict[str, str]] = []
    for ev in item.evidence:
        chunk = retrieved.get(ev.chunk_id)
        if chunk is None:
            continue
        if ev.quote and norm(ev.quote) in norm(chunk.text):
            kept.append({"chunk_id": ev.chunk_id, "quote": ev.quote})
    verdict = item.verdict
    reasoning = item.reasoning
    if verdict in ("met", "partial") and not kept:
        verdict = "no_evidence"
        # Original reasoning described presence but no quote survived
        # verification — keeping it renders "No evidence" + "candidate lists
        # X" in the UI. Replace with a neutral note.
        reasoning = "No verifiable quote found in the retrieved resume chunks."
    if verdict == "no_evidence":
        kept = []
    return {
        "requirement_id": item.requirement_id,
        "verdict": verdict,
        "evidence": kept,
        "reasoning": reasoning,
    }


def judge_all(requirements: list[dict[str, Any]], chunks_per_req: list[list[models.ResumeChunk]]) -> list[dict[str, Any]]:
    nonce = isolation.new_nonce()
    sections = []
    for req, chunks in zip(requirements, chunks_per_req):
        block = "\n".join(isolation.wrap_chunk(c.id, c.text, nonce) for c in chunks)
        sections.append((str(req["id"]), str(req["text"]), block))
    user = judge_batch_user(sections)
    try:
        first = generate_json(JUDGE_SYSTEM, user, JUDGE_SCHEMA, temperature=settings.judge_temperature)
        return _pick_results(first, requirements)
    except HTTPException:
        raise
    except Exception:
        pass
    second = generate_json(JUDGE_SYSTEM, user, JUDGE_SCHEMA, temperature=settings.judge_temperature)
    return _pick_results(second, requirements, strict=True)


def _pick_results(payload: dict[str, Any], requirements: list[dict[str, Any]], strict: bool = False) -> list[dict[str, Any]]:
    items = payload.get("results", []) if isinstance(payload, dict) else []
    out = []
    for req in requirements:
        raw = next((i for i in items if str(i.get("requirement_id")) == str(req["id"])), None)
        if raw is None:
            if strict:
                raise HTTPException(status_code=502, detail="Judge skipped a requirement. Try again.")
            raise ValueError("empty judge result")
        out.append(JudgeItem.model_validate(raw).model_dump())
    return out


def evaluate_candidate(db: Session, candidate_id: str, jd_id: str) -> dict[str, Any]:
    cand = db.get(models.Candidate, candidate_id)
    jd = db.get(models.JobDescription, jd_id)
    if cand is None or jd is None:
        raise HTTPException(status_code=404, detail="Candidate or job not found.")
    requirements: list[dict[str, Any]] = jd.requirements_structured or []
    if not requirements:
        raise HTTPException(status_code=422, detail="Job has no parsed requirements.")
    chunks_per_req = [retrieve_chunks(db, candidate_id, str(req["text"])) for req in requirements]
    try:
        raw_all = judge_all(requirements, chunks_per_req)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail="Judge output failed validation. Try again.") from e
    verified: list[dict[str, Any]] = []
    for req, chunks, raw in zip(requirements, chunks_per_req, raw_all):
        retrieved = {c.id: c for c in chunks}
        verified.append(verify_item(raw, retrieved))
    for v in verified:
        if v["verdict"] == "no_evidence":
            v["display"] = NO_EVIDENCE_TEXT
    return {"requirements": requirements, "results": verified, "raw": raw_all}
