from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app import models
from app.db import get_db
from app.schemas import (
    EvaluationCreate,
    EvaluationListItem,
    EvaluationPatch,
    EvaluationRecord,
    IngestRequest,
)
from app.services import ingest as ingest_svc
from app.services import pipeline

router = APIRouter(prefix="/api/evaluations", tags=["evaluations"])


def _to_record(e: models.Evaluation, db: Session) -> EvaluationRecord:
    cand = db.get(models.Candidate, e.candidate_id)
    jd = db.get(models.JobDescription, e.job_description_id)
    return EvaluationRecord(
        id=e.id,
        candidate_id=e.candidate_id,
        job_description_id=e.job_description_id,
        candidate_name=cand.name if cand else "",
        company_name=jd.company_name if jd else "",
        job_title=jd.job_title if jd else "",
        fit_category=e.fit_category,
        fit_score=e.fit_score,
        per_requirement=e.per_requirement,
        explanation=e.explanation,
        explanation_edited=e.explanation_edited,
        outreach_subject=e.outreach_subject,
        outreach_body=e.outreach_body,
        outreach_body_edited=e.outreach_body_edited,
        injection_flagged=e.injection_flagged,
        injection_notes=e.injection_notes,
        created_at=e.created_at,
    )


@router.post("", response_model=EvaluationRecord, status_code=status.HTTP_201_CREATED)
def create_evaluation(payload: EvaluationCreate, db: Session = Depends(get_db)) -> EvaluationRecord:
    if payload.candidate_id and payload.job_description_id:
        record = pipeline.run_evaluation(db, payload.candidate_id, payload.job_description_id)
        return _to_record(record, db)
    ing = ingest_svc.ingest_candidate(
        db,
        name=payload.candidate_name,
        target_role=payload.target_role,
        resume_text=payload.resume_text,
        company_name=payload.company_name,
        job_title=payload.job_title,
        job_description=payload.job_description,
    )
    record = pipeline.run_evaluation(db, ing["candidate_id"], ing["job_description_id"])
    return _to_record(record, db)


@router.get("", response_model=list[EvaluationListItem])
def list_evaluations(limit: int = 20, offset: int = 0, db: Session = Depends(get_db)) -> list[EvaluationListItem]:
    limit = max(1, min(limit, 100))
    rows = (
        db.query(models.Evaluation).order_by(models.Evaluation.created_at.desc()).offset(offset).limit(limit).all()
    )
    out: list[EvaluationListItem] = []
    for e in rows:
        cand = db.get(models.Candidate, e.candidate_id)
        jd = db.get(models.JobDescription, e.job_description_id)
        out.append(
            EvaluationListItem(
                id=e.id,
                candidate_name=cand.name if cand else "",
                company_name=jd.company_name if jd else "",
                job_title=jd.job_title if jd else "",
                fit_category=e.fit_category,
                fit_score=e.fit_score,
                created_at=e.created_at,
            )
        )
    return out


@router.get("/{evaluation_id}", response_model=EvaluationRecord)
def get_evaluation(evaluation_id: str, db: Session = Depends(get_db)) -> EvaluationRecord:
    e = db.get(models.Evaluation, evaluation_id)
    if e is None:
        raise HTTPException(status_code=404, detail="Evaluation not found.")
    return _to_record(e, db)


@router.patch("/{evaluation_id}", response_model=EvaluationRecord)
def patch_evaluation(evaluation_id: str, payload: EvaluationPatch, db: Session = Depends(get_db)) -> EvaluationRecord:
    e = db.get(models.Evaluation, evaluation_id)
    if e is None:
        raise HTTPException(status_code=404, detail="Evaluation not found.")
    if payload.explanation_edited is not None:
        if len(payload.explanation_edited) > 5000:
            raise HTTPException(status_code=422, detail="Edited explanation is too long.")
        e.explanation_edited = payload.explanation_edited
    if payload.outreach_body_edited is not None:
        if len(payload.outreach_body_edited) > 5000:
            raise HTTPException(status_code=422, detail="Edited outreach is too long.")
        e.outreach_body_edited = payload.outreach_body_edited
    db.commit()
    db.refresh(e)
    return _to_record(e, db)


@router.post("/{evaluation_id}/outreach/regenerate", response_model=EvaluationRecord)
def regenerate_outreach(evaluation_id: str, db: Session = Depends(get_db)) -> EvaluationRecord:
    from app.services import outreach as outreach_svc

    e = db.get(models.Evaluation, evaluation_id)
    if e is None:
        raise HTTPException(status_code=404, detail="Evaluation not found.")
    cand = db.get(models.Candidate, e.candidate_id)
    jd = db.get(models.JobDescription, e.job_description_id)
    if cand is None or jd is None:
        raise HTTPException(status_code=404, detail="Candidate or job not found.")
    mail = outreach_svc.build_outreach(
        cand.name, jd.company_name, jd.job_title, e.per_requirement or []
    )
    e.outreach_subject = mail["subject"]
    e.outreach_body = mail["body"]
    db.commit()
    db.refresh(e)
    return _to_record(e, db)
