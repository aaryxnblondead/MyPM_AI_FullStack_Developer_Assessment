from sqlalchemy.orm import Session

from app import models
from app.config import settings
from app.services import evaluator, explanation, outreach, scoring
from app.services.guard import detect_injection


def run_evaluation(db: Session, candidate_id: str, jd_id: str) -> models.Evaluation:
    cand = db.get(models.Candidate, candidate_id)
    jd = db.get(models.JobDescription, jd_id)
    if cand is None or jd is None:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Candidate or job not found.")
    inj_text = f"{cand.resume_text}\n{jd.jd_text}"
    flagged, notes = detect_injection(inj_text)

    ev = evaluator.evaluate_candidate(db, candidate_id, jd_id)
    requirements = ev["requirements"]
    results = ev["results"]
    score = scoring.score_requirements(requirements, results)
    expl = explanation.build_explanation(results)
    mail = outreach.build_outreach(cand.name, jd.company_name, jd.job_title, results)
    flags = outreach.post_check_email(mail["body"], requirements, results)

    record = models.Evaluation(
        candidate_id=candidate_id,
        job_description_id=jd_id,
        fit_category=score["fit_category"],
        fit_score=score["fit_score"],
        per_requirement=results,
        explanation=expl,
        outreach_subject=mail["subject"],
        outreach_body=mail["body"],
        injection_flagged=flagged or cand.injection_flagged,
        injection_notes="; ".join([n for n in [notes, cand.injection_notes] if n]),
        llm_model=settings.llm_model,
        embedding_model=settings.embedding_model,
        prompt_version=settings.prompt_version,
        raw_llm_output={"judge": ev["raw"], "outreach_flags": flags, "score": score},
        status="complete",
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record
