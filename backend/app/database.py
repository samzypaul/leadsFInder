"""SQLAlchemy engine, session factory, and Base."""
from __future__ import annotations

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings


class Base(DeclarativeBase):
    pass


def _normalize_db_url(url: str) -> str:
    """Make common Postgres URLs work with the psycopg (v3) driver.

    Hosts like Neon/Vercel/Heroku hand out `postgres://` or `postgresql://` URLs, which
    SQLAlchemy maps to the psycopg2 dialect. We ship psycopg v3, so rewrite the scheme to
    `postgresql+psycopg://` unless a driver is already specified.
    """
    if url.startswith("postgres://"):
        url = "postgresql://" + url[len("postgres://"):]
    if url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


DB_URL = _normalize_db_url(settings.database_url)
_is_sqlite = DB_URL.startswith("sqlite")
_connect_args = {"check_same_thread": False} if _is_sqlite else {}

engine = create_engine(
    DB_URL,
    connect_args=_connect_args,
    pool_pre_ping=True,
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def init_db() -> None:
    """Create tables and apply lightweight additive column migrations.

    For production use Alembic. This keeps the dev/demo experience zero-step: new columns
    added to models are ALTERed onto existing Postgres tables without dropping data.
    """
    from app import models  # noqa: F401  (ensure models are registered)

    Base.metadata.create_all(bind=engine)
    _ensure_columns()


def _ensure_columns() -> None:
    """Additively add columns that may be missing on a pre-existing Postgres schema."""
    if engine.dialect.name != "postgresql":
        return  # SQLite tables are always created fresh from the current models
    from sqlalchemy import text

    alters = [
        "ALTER TABLE leads ADD COLUMN IF NOT EXISTS target_service VARCHAR(255)",
        "ALTER TABLE scan_jobs ADD COLUMN IF NOT EXISTS service VARCHAR(255)",
        "ALTER TABLE scan_jobs ADD COLUMN IF NOT EXISTS hint_category VARCHAR(255)",
        "ALTER TABLE scan_jobs ADD COLUMN IF NOT EXISTS hint_city VARCHAR(128)",
    ]
    with engine.begin() as conn:
        for stmt in alters:
            try:
                conn.execute(text(stmt))
            except Exception:  # noqa: BLE001
                pass


def get_db() -> Iterator[Session]:
    """FastAPI dependency that yields a scoped session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
