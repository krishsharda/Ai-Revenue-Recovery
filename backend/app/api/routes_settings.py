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
    # The browser holds no admin token, so it cannot satisfy `require_admin`.
    # Rather than let the UI offer a button that can only 401, report up front
    # whether an unauthenticated caller is allowed to send — true exactly when
    # ADMIN_TOKEN is unset and this process is not publicly reachable, i.e.
    # local development.
    test_allowed = not settings.admin_token and not settings.is_public_deployment
    if test_allowed:
        test_blocked_reason = None
    elif settings.admin_token:
        test_blocked_reason = (
            "Test email requires the server's ADMIN_TOKEN as an X-Admin-Token header. "
            "Send it with curl, or run the app locally where it is not required."
        )
    else:
        test_blocked_reason = (
            "Test email is disabled on this deployment because ADMIN_TOKEN is not set."
        )

    return {
        "email": {
            "connected": settings.resend_configured,
            "provider": "Resend" if settings.resend_configured else None,
            "environment": "Production Email API" if settings.resend_configured else None,
            # The From address is on every email the product sends, so it is not
            # a secret; the API key behind it is never exposed.
            "sender": settings.email_from if settings.resend_configured else None,
            "reply_to": settings.email_reply_to or None,
            "test_allowed": test_allowed,
            "test_blocked_reason": test_blocked_reason,
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
