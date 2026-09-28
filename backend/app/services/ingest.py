from sqlalchemy.orm import Session

from app import models
from app.services import chunker, embedder, jd_parser, resume_extractor, skills_db, vectors
from app.services.guard import detect_injection


def ingest_candidate(
    db: Session,
    name: str,
    target_role: str,
    resume_text: str,
    company_name: str,
    job_title: str,
    job_description: str,
) -> dict:
    resume_flag, resume_notes = detect_injection(resume_text)
    jd_flag, jd_notes = detect_injection(job_description)
    flagged = resume_flag or jd_flag
    notes = "; ".join([n for n in [resume_notes, jd_notes] if n])

    structured = resume_extractor.extract_resume(resume_text)
    for skill in structured.get("skills", []):
        if isinstance(skill, dict) and "name" in skill:
            skill["known"] = skills_db.is_known(str(skill["name"]))
    skill_reference_hits = skills_db.find_in_text(resume_text)
    section_skills = skills_db.extract_skills_section(resume_text)
    present = {str(s.get("name", "")).strip().lower() for s in structured.get("skills", []) if isinstance(s, dict)}
    for item in section_skills:
        if item["name"].strip().lower() not in present:
            structured.setdefault("skills", []).append(
                {"name": item["name"], "source": item["source"], "known": skills_db.is_known(item["name"])}
            )
            present.add(item["name"].strip().lower())
    requirements = jd_parser.parse_jd(job_description)
    chunks = chunker.chunk_text(resume_text)
    embeddings = embedder.embed_documents([c["text"] for c in chunks])

    candidate = models.Candidate(
        name=name,
        target_role=target_role,
        resume_text=resume_text,
        resume_structured=structured,
        injection_flagged=flagged,
        injection_notes=notes,
    )
    db.add(candidate)
    db.flush()

    chunk_rows: list[models.ResumeChunk] = []
    for c in chunks:
        row = models.ResumeChunk(
            candidate_id=candidate.id,
            chunk_index=c["chunk_index"],
            section_label=c["section_label"],
            text=c["text"],
            char_start=c["char_start"],
            char_end=c["char_end"],
        )
        db.add(row)
        chunk_rows.append(row)
    db.flush()

    vectors.insert_vectors(db, [(r.id, v) for r, v in zip(chunk_rows, embeddings)])

    jd = models.JobDescription(
        company_name=company_name,
        job_title=job_title,
        jd_text=job_description,
        requirements_structured=requirements,
    )
    db.add(jd)
    db.flush()
    db.commit()
    db.refresh(candidate)
    db.refresh(jd)
    return {
        "candidate_id": candidate.id,
        "job_description_id": jd.id,
        "resume_structured": structured,
        "requirements": requirements,
        "chunk_count": len(chunk_rows),
        "injection_flagged": flagged,
        "skill_reference_hits": skill_reference_hits,
    }
