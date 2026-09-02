"""Real recovery-email service (Resend).

Orchestrates validation → send → record → audit. Never mocks or fakes delivery:
if Resend is not configured or the recipient is invalid, the attempt is recorded
as BLOCKED; if Resend rejects it, it is recorded as FAILED. An email being SENT
never marks revenue as recovered — only a Razorpay capture webhook does that.
"""
from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.orm import Session

from ..integrations import resend_client
from ..logging_config import get_logger
from ..models.communication import CommunicationRecord
from . import audit_service, email_templates

logger = get_logger(__name__)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

PENDING, SENT, FAILED, BLOCKED = "PENDING", "SENT", "FAILED", "BLOCKED"


def valid_email(addr: Optional[str]) -> bool:
    return bool(addr and _EMAIL_RE.match(addr.strip()))


def mask_email(addr: Optional[str]) -> str:
    if not addr or "@" not in addr:
        return "—"
    local, domain = addr.split("@", 1)
    head = local[0] if local else "*"
    return f"{head}{'*' * max(1, len(local) - 1)}@{domain}"


def _record(db: Session, *, case_id, customer_id, recipient, subject, status,
            provider_message_id=None, payment_link=None, failure_reason=None,
            sent_at=None) -> CommunicationRecord:
    rec = CommunicationRecord(
        recovery_case_id=case_id, customer_id=customer_id, channel="EMAIL",
        provider="resend", recipient=recipient, subject=subject, status=status,
        provider_message_id=provider_message_id, payment_link=payment_link,
        failure_reason=failure_reason, sent_at=sent_at,
    )
    db.add(rec)
    db.flush()
    return rec


def send_recovery_email(
    db: Session,
    *,
    recovery_case_id: Optional[int],
    customer_id: Optional[int],
    to_email: Optional[str],
    customer_name: str,
    amount: float,
    currency: str,
    subject: str,
    body: str,
    payment_link: Optional[str] = None,
) -> CommunicationRecord:
    amount_display = f"{currency} {amount:,.0f}"

    # 1. Validate recipient.
    if not valid_email(to_email):
        rec = _record(db, case_id=recovery_case_id, customer_id=customer_id, recipient=to_email,
                      subject=subject, status=BLOCKED, failure_reason="No valid recipient email.")
        _audit(db, recovery_case_id, "Email Blocked", "BLOCKED", "No valid recipient email address.")
        return rec

    # 2. Provider must be configured — we never fake a send.
    if not resend_client.is_configured():
        rec = _record(db, case_id=recovery_case_id, customer_id=customer_id, recipient=to_email,
                      subject=subject, status=BLOCKED,
                      failure_reason="Email provider (Resend) not configured.", payment_link=payment_link)
        _audit(db, recovery_case_id, "Email Blocked", "BLOCKED",
               "Resend not configured — set RESEND_API_KEY and EMAIL_FROM.")
        return rec

    html = email_templates.render_html(customer_name=customer_name, amount_display=amount_display,
                                       body=body, payment_link=payment_link)
    text = email_templates.render_text(customer_name=customer_name, amount_display=amount_display,
                                       body=body, payment_link=payment_link)

    _audit(db, recovery_case_id, "Email Service", "resend", f"Dispatching to {mask_email(to_email)}")

    # 3. Send. Record only PENDING->SENT after the provider accepts it.
    try:
        message_id = resend_client.send(to_email, subject, html, text)
    except resend_client.ResendError as exc:
        rec = _record(db, case_id=recovery_case_id, customer_id=customer_id, recipient=to_email,
                      subject=subject, status=FAILED, failure_reason=str(exc)[:400],
                      payment_link=payment_link)
        _audit(db, recovery_case_id, "Email", "FAILED", str(exc)[:400])
        logger.warning("Recovery email FAILED: %s", exc)
        return rec

    rec = _record(db, case_id=recovery_case_id, customer_id=customer_id, recipient=to_email,
                  subject=subject, status=SENT, provider_message_id=message_id,
                  payment_link=payment_link, sent_at=datetime.now(timezone.utc).isoformat())
    _audit(db, recovery_case_id, "Email", "ACCEPTED", f"Provider id: {message_id}")
    return rec


def send_test_email(db: Session, to_email: str) -> dict:
    """Settings 'Send Test Email' — a real send to a manually entered recipient."""
    if not valid_email(to_email):
        return {"ok": False, "status": BLOCKED, "error": "Invalid recipient email."}
    if not resend_client.is_configured():
        return {"ok": False, "status": BLOCKED, "error": "Resend not configured."}
    html = email_templates.render_html(customer_name="there", amount_display="—",
                                       body="This is a test email from AI Revenue Recovery confirming "
                                            "your Resend configuration works.", payment_link=None)
    text = email_templates.render_text(customer_name="there", amount_display="—",
                                       body="This is a test email confirming Resend works.", payment_link=None)
    try:
        mid = resend_client.send(to_email, "AI Revenue Recovery — test email", html, text)
    except resend_client.ResendError as exc:
        _record(db, case_id=None, customer_id=None, recipient=to_email,
                subject="test email", status=FAILED, failure_reason=str(exc)[:400])
        db.commit()
        return {"ok": False, "status": FAILED, "error": str(exc)[:300]}
    _record(db, case_id=None, customer_id=None, recipient=to_email, subject="test email",
            status=SENT, provider_message_id=mid,
            sent_at=datetime.now(timezone.utc).isoformat())
    db.commit()
    return {"ok": True, "status": SENT, "provider_message_id": mid, "recipient": mask_email(to_email)}


def _audit(db, case_id, event, result, reason):
    audit_service.log(db, event=event, actor="Email Service", result=result,
                      reason=reason, recovery_case_id=case_id)
