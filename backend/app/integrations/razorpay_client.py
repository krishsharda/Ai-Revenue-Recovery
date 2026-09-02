"""Razorpay TEST MODE client wrapper.

When test credentials are present, real Razorpay Test API calls are made (create
order, create payment link, fetch payment). When they are absent, callers fall
back to a clearly-labelled simulation layer. Webhook signatures are verified with
HMAC-SHA256 against RAZORPAY_WEBHOOK_SECRET.

Secrets are read only from settings and never logged.
"""
from __future__ import annotations

import hashlib
import hmac
from typing import Any, Dict, Optional

from ..config import settings
from ..logging_config import get_logger

logger = get_logger(__name__)


class RazorpayNotConfigured(RuntimeError):
    pass


class RazorpayError(RuntimeError):
    pass


def is_configured() -> bool:
    return settings.razorpay_configured


def _client():
    if not is_configured():
        raise RazorpayNotConfigured("Razorpay test credentials are not configured.")
    import razorpay  # imported lazily so the app runs without the dependency configured

    client = razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))
    client.set_app_details({"title": settings.app_name, "version": "0.1.0"})
    return client


def verify_webhook_signature(raw_body: bytes, signature: Optional[str]) -> bool:
    """Constant-time HMAC-SHA256 verification of the X-Razorpay-Signature header."""
    if not settings.razorpay_webhook_configured or not signature:
        return False
    expected = hmac.new(
        settings.razorpay_webhook_secret.encode("utf-8"), raw_body, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(expected, signature)


def create_order(amount_rupees: float, currency: str = "INR", notes: Optional[dict] = None) -> Dict[str, Any]:
    """Create a real Razorpay TEST order (amount in paise). Raises if not configured."""
    client = _client()
    try:
        order = client.order.create(
            {
                "amount": int(round(amount_rupees * 100)),
                "currency": currency,
                "payment_capture": 1,
                "notes": notes or {},
            }
        )
        logger.info("Created Razorpay TEST order %s", order.get("id"))
        return order
    except Exception as exc:  # razorpay raises various error types
        raise RazorpayError(f"create_order failed: {exc}") from exc


def create_payment_link(
    amount_rupees: float,
    customer_name: str,
    customer_email: Optional[str],
    customer_phone: Optional[str],
    description: str,
    currency: str = "INR",
) -> Dict[str, Any]:
    """Create a real Razorpay TEST payment link. Raises if not configured."""
    client = _client()
    payload: Dict[str, Any] = {
        "amount": int(round(amount_rupees * 100)),
        "currency": currency,
        "accept_partial": False,
        "description": description[:2048],
        "customer": {"name": customer_name},
        "notify": {"sms": False, "email": False},
        "reminder_enable": False,
    }
    if customer_email:
        payload["customer"]["email"] = customer_email
    if customer_phone:
        payload["customer"]["contact"] = customer_phone
    try:
        link = client.payment_link.create(payload)
        logger.info("Created Razorpay TEST payment link %s", link.get("id"))
        return link
    except Exception as exc:
        raise RazorpayError(f"create_payment_link failed: {exc}") from exc


def fetch_payment(payment_id: str) -> Dict[str, Any]:
    client = _client()
    try:
        return client.payment.fetch(payment_id)
    except Exception as exc:
        raise RazorpayError(f"fetch_payment failed: {exc}") from exc
