"""Database engine, session factory and FastAPI dependency.

Uses SQLAlchemy 2.0. Defaults to SQLite for local development; set
`DATABASE_URL` to a Postgres URL (Neon, Supabase, Vercel Postgres) for
deployment. Provider-specific URL forms are normalised in `config.py`.

Pooling is chosen for the runtime: a long-lived local server keeps a small
pool, while a serverless function uses `NullPool` and defers connection reuse
to the provider's own pooler (e.g. Neon's PgBouncer endpoint). Holding a
SQLAlchemy pool inside a function that may be frozen between invocations
produces stale sockets and "server closed the connection unexpectedly" errors.
"""
from __future__ import annotations

import os
import threading
from collections.abc import Generator

from sqlalchemy import create_engine, event
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from .config import settings

# Vercel, AWS Lambda and Google Cloud Functions all set one of these.
IS_SERVERLESS = bool(
    os.getenv("VERCEL") or os.getenv("AWS_LAMBDA_FUNCTION_NAME") or os.getenv("FUNCTION_TARGET")
)

# SQLite needs check_same_thread disabled for FastAPI's threadpool.
connect_args: dict = {"check_same_thread": False} if settings.is_sqlite else {}

if not settings.is_sqlite:
    # Fail fast instead of letting a request hang on an unreachable database.
    connect_args["connect_timeout"] = 10

engine_kwargs: dict = {"connect_args": connect_args, "future": True}
if IS_SERVERLESS and not settings.is_sqlite:
    engine_kwargs["poolclass"] = NullPool
else:
    engine_kwargs["pool_pre_ping"] = True

engine = create_engine(settings.database_url, **engine_kwargs)

if settings.is_sqlite:
    # WAL + a generous busy timeout let concurrent readers/writers coexist and
    # wait for locks instead of erroring ("database is locked") under bursty
    # writes like a persisted simulation.
    @event.listens_for(engine, "connect")
    def _sqlite_pragmas(dbapi_conn, _rec):  # pragma: no cover
        cur = dbapi_conn.cursor()
        cur.execute("PRAGMA journal_mode=WAL")
        cur.execute("PRAGMA busy_timeout=8000")
        cur.execute("PRAGMA synchronous=NORMAL")
        cur.close()

SessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False, expire_on_commit=False, class_=Session
)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a scoped database session.

    Bootstraps the schema (and first-run demo data) on the first request in a
    process, so a serverless cold start does not do that work up front.
    """
    from .bootstrap import ensure_ready  # imported late: bootstrap imports this module

    ensure_ready()
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


_init_lock = threading.Lock()
_initialised = False


def init_db(force: bool = False) -> None:
    """Create all tables. Idempotent, and runs at most once per process.

    `create_all` issues a round-trip per table to check existence, which is
    wasted work on every serverless cold start once the schema exists. The
    process-level guard keeps that cost to the first request in a container.
    """
    global _initialised
    if _initialised and not force:
        return
    with _init_lock:
        if _initialised and not force:
            return
        from . import models  # noqa: F401  (ensures all models are registered)
        from .models.base import Base

        Base.metadata.create_all(bind=engine)
        _initialised = True
