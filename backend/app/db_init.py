"""Explicit DB init: relational tables plus sqlite-vec virtual table."""
import re

from sqlalchemy import text

from app.config import settings
from app.db import Base, engine


def vec_ddl(dim: int) -> str:
    return (
        "CREATE VIRTUAL TABLE IF NOT EXISTS resume_chunk_vectors "
        f"USING vec0(chunk_id TEXT, embedding FLOAT[{dim}] distance_metric=cosine)"
    )


def existing_vec_dim(conn) -> int | None:
    row = conn.exec_driver_sql(
        "SELECT sql FROM sqlite_master WHERE name='resume_chunk_vectors'"
    ).fetchone()
    if not row or not row[0]:
        return None
    m = re.search(r"FLOAT\[(\d+)\]", str(row[0]))
    return int(m.group(1)) if m else None


def init_db() -> None:
    from app import models  # noqa: F401  register tables

    Base.metadata.create_all(bind=engine)
    with engine.begin() as conn:
        cols = [r[1] for r in conn.exec_driver_sql("PRAGMA table_info(evaluations)").fetchall()]
        if "outreach_subject_edited" not in cols:
            conn.exec_driver_sql("ALTER TABLE evaluations ADD COLUMN outreach_subject_edited VARCHAR(300)")
        current = existing_vec_dim(conn)
        if current is not None and current != settings.embedding_dim:
            conn.exec_driver_sql("DROP TABLE resume_chunk_vectors")
            print(f"rebuilt vec table: dim {current} -> {settings.embedding_dim} (old vectors cleared)")
        conn.execute(text(vec_ddl(settings.embedding_dim)))


if __name__ == "__main__":
    init_db()
    print("db init ok")
