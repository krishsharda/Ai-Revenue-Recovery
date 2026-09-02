from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..ml import get_model
from ..policies import policy_config

router = APIRouter(tags=["system"])


@router.get("/health")
def health(db: Session = Depends(get_db)) -> dict:
    try:
        db.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    model = get_model()
    return {
        "status": "ok" if db_ok else "degraded",
        "app": settings.app_name,
        "environment": settings.environment,
        "database": "connected" if db_ok else "error",
        "database_engine": "sqlite" if settings.is_sqlite else "postgresql",
        "model": {"version": model.version, "trained_on": model.trained_on,
                  "train_accuracy": round(model.train_accuracy, 3)},
    }


@router.get("/config")
def config() -> dict:
    return {
        "mode": "Razorpay Test Mode",
        "app_name": settings.app_name,
        "environment": settings.environment,
        "features": {
            "razorpay_configured": settings.razorpay_configured,
            "razorpay_webhook_configured": settings.razorpay_webhook_configured,
            "llm_configured": settings.llm_configured,
            "llm_provider": settings.resolved_llm_provider if settings.llm_configured else None,
            "llm_model": settings.resolved_llm_model if settings.llm_configured else None,
            "email_configured": settings.resend_configured,
            "email_provider": "resend" if settings.resend_configured else None,
            "database_engine": "sqlite" if settings.is_sqlite else "postgresql",
        },
        "policy": policy_config(),
        "decision_engine": (
            f"{settings.resolved_llm_provider}+heuristic" if settings.llm_configured else "heuristic"
        ),
    }
