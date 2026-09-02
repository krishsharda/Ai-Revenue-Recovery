"""Seed the database with demo data.

Usage (from backend/):  python -m scripts.seed
"""
from __future__ import annotations

from app.database import SessionLocal, init_db
from app.logging_config import configure_logging
from app.seed import seed


def main() -> None:
    configure_logging()
    init_db()
    with SessionLocal() as db:
        result = seed(db, clear=True, run_pipeline=True)
    print(f"Seeded: {result}")


if __name__ == "__main__":
    main()
