from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db, init_db
from ..seed import seed as seed_db
from .deps import require_admin

# Both routes destroy existing data, so they are admin-guarded: anonymous
# callers must not be able to wipe a deployed instance.
router = APIRouter(tags=["admin"], dependencies=[Depends(require_admin)])


@router.post("/admin/seed")
def reseed(db: Session = Depends(get_db)) -> dict:
    """Regenerate the demo dataset (clears existing rows first)."""
    init_db()
    result = seed_db(db, clear=True, run_pipeline=True)
    return {"status": "seeded", **result}


@router.post("/admin/reset")
def reset(db: Session = Depends(get_db)) -> dict:
    """Clear all data without reseeding."""
    from ..seed.seed_data import _clear

    _clear(db)  # commits internally
    return {"status": "reset"}
