from __future__ import annotations

import json

from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..integrations import razorpay_client
from ..logging_config import get_logger
from ..services import audit_service, webhook_service

logger = get_logger(__name__)
router = APIRouter(tags=["webhooks"])


@router.post("/webhooks/razorpay")
async def razorpay_webhook(
    request: Request,
    db: Session = Depends(get_db),
    x_razorpay_signature: str | None = Header(default=None),
) -> dict:
    raw_body = await request.body()

    verified = False
    if settings.razorpay_webhook_configured:
        verified = razorpay_client.verify_webhook_signature(raw_body, x_razorpay_signature)
        if not verified:
            audit_service.log(db, event="Webhook Rejected", actor="Razorpay",
                              result="INVALID_SIGNATURE", commit=True)
            raise HTTPException(status_code=400, detail="Invalid webhook signature")
    elif settings.is_public_deployment:
        # Fail closed. Without a secret every payload is forgeable, and these
        # events mark revenue as recovered — anyone could fake a capture.
        logger.error("Webhook rejected: RAZORPAY_WEBHOOK_SECRET is not configured.")
        audit_service.log(db, event="Webhook Rejected", actor="Razorpay",
                          result="UNVERIFIABLE", reason="Webhook secret not configured",
                          commit=True)
        raise HTTPException(
            status_code=503,
            detail="Webhook processing is disabled: RAZORPAY_WEBHOOK_SECRET is not configured.",
        )
    else:
        # Local development only: accept, but flag the event as unverified so
        # nothing downstream can mistake it for a genuine Razorpay call.
        logger.warning("Webhook signature NOT verified (RAZORPAY_WEBHOOK_SECRET unset).")

    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    event = payload.get("event", "")
    try:
        result = webhook_service.handle_event(db, event, payload, verified)
    except Exception as exc:  # never 500 the webhook source
        logger.exception("Webhook processing error")
        db.rollback()
        audit_service.log(db, event="Webhook Error", actor="Razorpay",
                          result="ERROR", reason=str(exc), commit=True)
        return {"handled": False, "error": "processing_error"}
    return result
