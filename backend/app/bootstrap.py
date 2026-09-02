"""One-time application bootstrap: schema creation and first-run demo seeding.

Runs at most once per process. A long-lived local server triggers it from the
lifespan handler; a serverless function triggers it lazily on the first request
that touches the database, because a cold start should not pay for work the
container may never need.

On Postgres the whole check-and-seed is wrapped in a transaction-level advisory
lock. Several functions can cold-start concurrently on the first deploy, and
without the lock each could observe an empty database and seed it, producing
duplicated demo data.
"""
from __future__ import annotations

import threading

from sqlalchemy import func, select, text

from .database import SessionLocal, engine, init_db
from .logging_config import get_logger

logger = get_logger(__name__)

# Arbitrary but stable key identifying this app's bootstrap lock.
_ADVISORY_LOCK_KEY = 8412557301994

_lock = threading.Lock()
_done = False


def _seed_if_empty(db) -> None:
    from .models.customer import Customer

    count = db.execute(select(func.count()).select_from(Customer)).scalar_one()
    if count:
        return
    logger.info("Empty database detected — seeding demo data.")
    from .seed import seed

    seed(db)


def ensure_ready() -> None:
    """Create tables and seed demo data if needed. Safe to call on every request."""
    global _done
    if _done:
        return
    with _lock:
        if _done:
            return

        init_db()

        try:
            with SessionLocal() as db:
                if engine.dialect.name == "postgresql":
                    # Transaction-scoped: released automatically on commit/rollback.
                    db.execute(
                        text("SELECT pg_advisory_xact_lock(:k)"), {"k": _ADVISORY_LOCK_KEY}
                    )
                    _seed_if_empty(db)
                    db.commit()
                else:
                    _seed_if_empty(db)
                    db.commit()
        except Exception:
            # A failed seed must not permanently break the app: the schema is
            # already in place, so requests can still be served (and retried).
            logger.exception("Demo seeding failed; continuing without it.")

        _done = True
