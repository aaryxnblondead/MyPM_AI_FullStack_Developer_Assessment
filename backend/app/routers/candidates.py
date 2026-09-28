from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app import models
from app.db import get_db
from app.schemas import CandidateChunks, CandidateDetail, ChunkItem, IngestRequest, IngestResponse
from app.services import ingest as ingest_svc

router = APIRouter(prefix="/api/candidates", tags=["candidates"])


@router.post("/ingest", response_model=IngestResponse)
def ingest(req: IngestRequest, db: Session = Depends(get_db)) -> IngestResponse:
    result = ingest_svc.ingest_candidate(
        db,
        name=req.candidate_name,
        target_role=req.target_role,
        resume_text=req.resume_text,
        company_name=req.company_name,
        job_title=req.job_title,
        job_description=req.job_description,
    )
    return IngestResponse(**result)


@router.get("/{candidate_id}", response_model=CandidateDetail)
def get_candidate(candidate_id: str, db: Session = Depends(get_db)) -> CandidateDetail:
    cand = db.get(models.Candidate, candidate_id)
    if cand is None:
        raise HTTPException(status_code=404, detail="Candidate not found.")
    count = db.query(models.ResumeChunk).filter_by(candidate_id=candidate_id).count()
    return CandidateDetail(
        id=cand.id,
        name=cand.name,
        target_role=cand.target_role,
        resume_structured=cand.resume_structured,
        chunk_count=count,
        injection_flagged=cand.injection_flagged,
    )


@router.get("/{candidate_id}/chunks", response_model=CandidateChunks)
def get_candidate_chunks(candidate_id: str, db: Session = Depends(get_db)) -> CandidateChunks:
    cand = db.get(models.Candidate, candidate_id)
    if cand is None:
        raise HTTPException(status_code=404, detail="Candidate not found.")
    rows = (
        db.query(models.ResumeChunk)
        .filter_by(candidate_id=candidate_id)
        .order_by(models.ResumeChunk.chunk_index)
        .all()
    )
    return CandidateChunks(
        candidate_id=cand.id,
        name=cand.name,
        resume_text=cand.resume_text,
        chunks=[
            ChunkItem(
                id=r.id,
                chunk_index=r.chunk_index,
                section_label=r.section_label,
                text=r.text,
                char_start=r.char_start,
                char_end=r.char_end,
            )
            for r in rows
        ],
    )
