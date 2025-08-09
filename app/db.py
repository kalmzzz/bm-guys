from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase, scoped_session
from .config import settings


class Base(DeclarativeBase):
    pass


def _build_engine_url() -> str:
    if settings.database_url:
        url = settings.database_url
        # Normalize to psycopg (psycopg3) driver if using postgres
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg://", 1)
        elif url.startswith("postgresql://") and "+" not in url:
            url = url.replace("postgresql://", "postgresql+psycopg://", 1)
        return url
    # Local SQLite fallback
    return "sqlite+pysqlite:///./app.db"


engine = create_engine(_build_engine_url(), echo=False, future=True)
SessionLocal = scoped_session(sessionmaker(bind=engine, autoflush=False, autocommit=False))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()