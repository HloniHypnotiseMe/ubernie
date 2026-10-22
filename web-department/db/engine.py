#!/usr/bin/env python3
"""Database engine configuration.

SQLite is a development/test fallback only. Production must explicitly provide
a PostgreSQL DATABASE_URL so a missing secret cannot silently create a local DB.
"""
from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool

ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
_POSTGRES_PREFIXES = ("postgresql://", "postgresql+psycopg://", "postgresql+psycopg2://")

if ENVIRONMENT == "production":
    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL must be configured in production; SQLite fallback is development-only"
        )
    if not DATABASE_URL.startswith(_POSTGRES_PREFIXES):
        raise RuntimeError(
            "Production DATABASE_URL must use PostgreSQL; SQLite and other database engines are unsupported"
        )

_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DB_FILE = _PROJECT_ROOT / "data" / "web-department.db"
_DB_FILE.parent.mkdir(parents=True, exist_ok=True)

DEFAULT_URL = f"sqlite:///{_DB_FILE.as_posix()}"
if not DATABASE_URL:
    DATABASE_URL = DEFAULT_URL

_is_sqlite = DATABASE_URL.startswith("sqlite")

if _is_sqlite:
    engine = create_engine(
        DATABASE_URL,
        echo=os.getenv("SQL_ECHO", "0") == "1",
        future=True,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    @event.listens_for(engine, "connect")
    def _pragma(dbapi_conn, _):
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA foreign_keys=OFF")  # legacy development/test compatibility
        cur.close()
else:
    engine = create_engine(DATABASE_URL, echo=os.getenv("SQL_ECHO", "0") == "1", future=True)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
)


def get_session() -> Session:
    return SessionLocal()


def init_db() -> None:
    from db import models  # noqa
    from db.models import Base
    Base.metadata.create_all(bind=engine)


def db_path() -> str:
    """Return the actual SQLite DB file path (legacy helper)."""
    return str(_DB_FILE)
