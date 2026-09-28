import uuid
from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


def new_id() -> str:
    return uuid.uuid4().hex


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Candidate(Base):
    __tablename__ = "candidates"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(200))
    target_role: Mapped[str] = mapped_column(String(200))
    resume_text: Mapped[str] = mapped_column(Text)
    resume_structured: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    injection_flagged: Mapped[bool] = mapped_column(Boolean, default=False)
    injection_notes: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class ResumeChunk(Base):
    __tablename__ = "resume_chunks"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    candidate_id: Mapped[str] = mapped_column(String(32), ForeignKey("candidates.id"), index=True)
    chunk_index: Mapped[int] = mapped_column(Integer)
    section_label: Mapped[str] = mapped_column(String(80), default="general")
    text: Mapped[str] = mapped_column(Text)
    char_start: Mapped[int] = mapped_column(Integer)
    char_end: Mapped[int] = mapped_column(Integer)


class JobDescription(Base):
    __tablename__ = "job_descriptions"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    company_name: Mapped[str] = mapped_column(String(200))
    job_title: Mapped[str] = mapped_column(String(200))
    jd_text: Mapped[str] = mapped_column(Text)
    requirements_structured: Mapped[list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)


class Evaluation(Base):
    __tablename__ = "evaluations"

    id: Mapped[str] = mapped_column(String(32), primary_key=True, default=new_id)
    candidate_id: Mapped[str] = mapped_column(String(32), ForeignKey("candidates.id"), index=True)
    job_description_id: Mapped[str] = mapped_column(String(32), ForeignKey("job_descriptions.id"), index=True)
    fit_category: Mapped[str | None] = mapped_column(String(40), nullable=True)
    fit_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    per_requirement: Mapped[list | None] = mapped_column(JSON, nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    explanation_edited: Mapped[str | None] = mapped_column(Text, nullable=True)
    outreach_subject: Mapped[str | None] = mapped_column(String(300), nullable=True)
    outreach_subject_edited: Mapped[str | None] = mapped_column(String(300), nullable=True)
    outreach_body: Mapped[str | None] = mapped_column(Text, nullable=True)
    outreach_body_edited: Mapped[str | None] = mapped_column(Text, nullable=True)
    injection_flagged: Mapped[bool] = mapped_column(Boolean, default=False)
    injection_notes: Mapped[str] = mapped_column(Text, default="")
    llm_model: Mapped[str] = mapped_column(String(120), default="")
    embedding_model: Mapped[str] = mapped_column(String(120), default="")
    prompt_version: Mapped[str] = mapped_column(String(20), default="v1")
    raw_llm_output: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    status: Mapped[str] = mapped_column(String(40), default="complete")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
