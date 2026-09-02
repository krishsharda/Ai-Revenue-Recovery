"""Resend transactional-email transport (REST via httpx — no SDK dependency).

Only sends when RESEND_API_KEY + EMAIL_FROM are configured. The API key is read
from settings and never logged.
"""
from __future__ import annotations

from typing import Optional

import httpx

from ..config import settings
from ..logging_config import get_logger

logger = get_logger(__name__)

RESEND_URL = "https://api.resend.com/emails"


class ResendError(RuntimeError):
    pass


class ResendNotConfigured(RuntimeError):
    pass


def is_configured() -> bool:
    return settings.resend_configured


def send(to_email: str, subject: str, html: str, text: str) -> str:
    """Send an email via Resend. Returns the provider message id, or raises."""
    if not settings.resend_configured:
        raise ResendNotConfigured("RESEND_API_KEY / EMAIL_FROM not configured.")

    payload = {
        "from": settings.email_from,
        "to": [to_email],
        "subject": subject,
        "html": html,
        "text": text,
    }
    if settings.email_reply_to:
        payload["reply_to"] = settings.email_reply_to

    try:
        resp = httpx.post(
            RESEND_URL,
            headers={
                "Authorization": f"Bearer {settings.resend_api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=20.0,
        )
    except Exception as exc:  # network/DNS/timeout
        raise ResendError(f"Resend request failed: {exc}") from exc

    if resp.status_code >= 400:
        detail = _safe_error(resp)
        raise ResendError(f"Resend API error {resp.status_code}: {detail}")

    data = resp.json()
    message_id: Optional[str] = data.get("id")
    if not message_id:
        raise ResendError("Resend accepted the request but returned no message id.")
    logger.info("Resend accepted email (id=%s)", message_id)
    return message_id


def _safe_error(resp: httpx.Response) -> str:
    try:
        body = resp.json()
        return str(body.get("message") or body.get("name") or body)[:200]
    except Exception:
        return resp.text[:200]
