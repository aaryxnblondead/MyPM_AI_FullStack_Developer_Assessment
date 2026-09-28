from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings

DB_PATH = Path(settings.database_url.replace("sqlite:///", ""))
if not DB_PATH.is_absolute():
    DB_PATH = Path(__file__).resolve().parent.parent / DB_PATH
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

connect_args = {"check_same_thread": False}
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


@event.listens_for(Engine, "connect")
def _load_vec_extension(dbapi_conn, _record) -> None:
    try:
        import sqlite_vec

        dbapi_conn.enable_load_extension(True)
        dbapi_conn.load_extension(sqlite_vec.loadable_path())
    except Exception:
        pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
