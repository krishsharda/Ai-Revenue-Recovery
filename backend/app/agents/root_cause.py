"""Root-cause analysis layer.

Maps raw failure signals (and Razorpay error codes) into a canonical root cause
plus a human-readable description used across the UI and audit trail.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..models.enums import FailureReason, RevenueLossType


@dataclass(frozen=True)
class RootCause:
    code: FailureReason
    summary: str
    detail: str


_DESCRIPTIONS = {
    FailureReason.BANK_DECLINE: (
        "Temporary bank decline",
        "The issuing bank declined the transaction. These are frequently transient "
        "and recover on retry or via an alternate instrument.",
    ),
    FailureReason.INSUFFICIENT_FUNDS: (
        "Insufficient funds",
        "The account lacked sufficient balance. Recovery usually improves after a "
        "short delay or by offering an alternate payment method.",
    ),
    FailureReason.PAYMENT_TIMEOUT: (
        "Payment gateway timeout",
        "The payment did not complete within the gateway window. Often transient.",
    ),
    FailureReason.NETWORK_ERROR: (
        "Network interruption",
        "A network error interrupted the payment. Typically transient and retryable.",
    ),
    FailureReason.CARD_EXPIRED: (
        "Card expired",
        "The card is expired. A retry cannot succeed; a new instrument is required.",
    ),
    FailureReason.UPI_FAILURE: (
        "UPI failure",
        "The UPI transaction failed. A payment link or alternate rail often recovers it.",
    ),
    FailureReason.USER_ABANDONMENT: (
        "Checkout abandonment",
        "The customer showed intent but did not complete payment. A gentle, "
        "personalized nudge with a ready-to-pay link tends to work best.",
    ),
    FailureReason.UNKNOWN: (
        "Undetermined cause",
        "The failure cause could not be determined from available data.",
    ),
}

# Razorpay error code / description hints -> canonical failure reason.
_RAZORPAY_HINTS = {
    "BAD_REQUEST_ERROR": FailureReason.UNKNOWN,
    "GATEWAY_ERROR": FailureReason.NETWORK_ERROR,
    "insufficient": FailureReason.INSUFFICIENT_FUNDS,
    "declined": FailureReason.BANK_DECLINE,
    "expired": FailureReason.CARD_EXPIRED,
    "timeout": FailureReason.PAYMENT_TIMEOUT,
    "timed out": FailureReason.PAYMENT_TIMEOUT,
    "upi": FailureReason.UPI_FAILURE,
    "vpa": FailureReason.UPI_FAILURE,
    "cancelled": FailureReason.USER_ABANDONMENT,
    "customer_cancel": FailureReason.USER_ABANDONMENT,
    "network": FailureReason.NETWORK_ERROR,
}


def analyze(
    failure_reason: Optional[str], loss_type: str = RevenueLossType.PAYMENT_FAILURE.value
) -> RootCause:
    reason = _coerce(failure_reason)
    if loss_type == RevenueLossType.CHECKOUT_ABANDONMENT.value and reason in (
        FailureReason.UNKNOWN,
        FailureReason.PAYMENT_TIMEOUT,
    ):
        reason = FailureReason.USER_ABANDONMENT
    summary, detail = _DESCRIPTIONS[reason]
    return RootCause(code=reason, summary=summary, detail=detail)


def from_razorpay(error_code: Optional[str], error_description: Optional[str]) -> FailureReason:
    """Infer a canonical failure reason from Razorpay error fields."""
    haystack = f"{error_code or ''} {error_description or ''}".lower()
    for hint, reason in _RAZORPAY_HINTS.items():
        if hint.lower() in haystack:
            return reason
    return FailureReason.UNKNOWN


def _coerce(failure_reason: Optional[str]) -> FailureReason:
    if not failure_reason:
        return FailureReason.UNKNOWN
    try:
        return FailureReason(failure_reason)
    except ValueError:
        # Accept lowercase / free-text and fall back to razorpay-style hints.
        return from_razorpay(None, failure_reason)
