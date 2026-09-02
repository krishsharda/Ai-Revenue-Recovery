from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..services import email_service
from .deps import require_admin

router = APIRouter(tags=["settings"])


@router.get("/settings")
def get_settings() -> dict:
    return {
        "email": {
            "connected": settings.resend_configured,
            "provider": "Resend" if settings.resend_configured else None,
            "environment": "Production Email API" if settings.resend_configured else None,
            # The From address is on every email the product sends, so it is not
            # a secret; the API key behind it is never exposed.
            "sender": settings.email_from if settings.resend_configured else None,
            "reply_to": settings.email_reply_to or None,
        },
        "razorpay": {
            "connected": settings.razorpay_configured,
            "mode": "Test Mode",
            "webhook_configured": settings.razorpay_webhook_configured,
        },
        "llm": {
            "connected": settings.llm_configured,
            "provider": settings.resolved_llm_provider if settings.llm_configured else None,
            "model": settings.resolved_llm_model if settings.llm_configured else None,
        },
    }


class TestEmailRequest(BaseModel):
    # EmailStr rejects malformed addresses at the API boundary, before anything
    # reaches the mail provider.
    to: EmailStr


@router.post("/settings/email/test", dependencies=[Depends(require_admin)])
def send_test_email(body: TestEmailRequest, db: Session = Depends(get_db)) -> dict:
    """Send a REAL test email via Resend to a manually entered recipient.

    Admin-guarded: this sends genuine mail from a verified sender domain, so an
    open endpoint would be an anonymous spam relay that burns sending
    reputation.
    """
    return email_service.send_test_email(db, str(body.to).strip())
