from sqlalchemy import text
from sqlalchemy.orm import Session

from app.config import settings
from app.services.embedder import embed_documents, embed_query


def insert_vectors(db: Session, pairs: list[tuple[str, list[float]]]) -> None:
    for chunk_id, vec in pairs:
        if len(vec) != settings.embedding_dim:
            raise ValueError("Vector dim mismatch")
        vec_str = "[" + ",".join(repr(float(x)) for x in vec) + "]"
        db.execute(
            text("INSERT INTO resume_chunk_vectors(chunk_id, embedding) VALUES (:cid, :vec)"),
            {"cid": chunk_id, "vec": vec_str},
        )


def nearest_chunks(db: Session, query_vec: list[float], limit: int = 5) -> list[tuple[str, float]]:
    vec_str = "[" + ",".join(repr(float(x)) for x in query_vec) + "]"
    rows = db.execute(
        text(
            "SELECT chunk_id, distance FROM resume_chunk_vectors "
            "WHERE embedding MATCH :vec ORDER BY distance LIMIT :lim"
        ),
        {"vec": vec_str, "lim": limit},
    ).fetchall()
    return [(r[0], float(r[1])) for r in rows]


def query_text(db: Session, query: str, limit: int = 5) -> list[tuple[str, float]]:
    return nearest_chunks(db, embed_query(query), limit)


def nearest_chunks_for_candidate(
    db: Session, candidate_id: str, query_vec: list[float], limit: int
) -> list[tuple[str, float]]:
    from app import models

    allowed = {
        r.id
        for r in db.query(models.ResumeChunk).filter_by(candidate_id=candidate_id).all()
    }
    if not allowed:
        return []
    over = max(limit * 5 + 10, 20)
    rows = nearest_chunks(db, query_vec, over)
    out = [(cid, d) for cid, d in rows if cid in allowed]
    return out[:limit]
