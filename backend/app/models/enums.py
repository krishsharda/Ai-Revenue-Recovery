"""Shared enumerations. Stored as strings in the database for portability."""
from __future__ import annotations

from enum import Enum


class StrEnum(str, Enum):
    def __str__(self) -> str:  # pragma: no cover - cosmetic
        return self.value


class RevenueLossType(StrEnum):
    """The four categories of revenue loss the platform recovers."""

    PAYMENT_FAILURE = "PAYMENT_FAILURE"
    CHECKOUT_ABANDONMENT = "CHECKOUT_ABANDONMENT"
    SUBSCRIPTION_FAILURE = "SUBSCRIPTION_FAILURE"
    OVERDUE_INVOICE = "OVERDUE_INVOICE"


class TransactionStatus(StrEnum):
    CREATED = "CREATED"
    ATTEMPTED = "ATTEMPTED"
    FAILED = "FAILED"
    ABANDONED = "ABANDONED"
    CAPTURED = "CAPTURED"
    REFUNDED = "REFUNDED"


class FailureReason(StrEnum):
    BANK_DECLINE = "BANK_DECLINE"
    INSUFFICIENT_FUNDS = "INSUFFICIENT_FUNDS"
    PAYMENT_TIMEOUT = "PAYMENT_TIMEOUT"
    NETWORK_ERROR = "NETWORK_ERROR"
    CARD_EXPIRED = "CARD_EXPIRED"
    UPI_FAILURE = "UPI_FAILURE"
    USER_ABANDONMENT = "USER_ABANDONMENT"
    UNKNOWN = "UNKNOWN"


class PaymentMethod(StrEnum):
    CARD = "card"
    UPI = "upi"
    NETBANKING = "netbanking"
    WALLET = "wallet"
    EMI = "emi"


class RiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class CustomerValue(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RecoveryActionType(StrEnum):
    RETRY_PAYMENT = "RETRY_PAYMENT"
    PAYMENT_LINK = "PAYMENT_LINK"
    ALTERNATE_PAYMENT_METHOD = "ALTERNATE_PAYMENT_METHOD"
    EMAIL = "EMAIL"
    WHATSAPP = "WHATSAPP"
    HUMAN_ESCALATION = "HUMAN_ESCALATION"
    DO_NOTHING = "DO_NOTHING"
    SCHEDULE_RETRY = "SCHEDULE_RETRY"


class RecoveryChannel(StrEnum):
    PAYMENT_RETRY = "PAYMENT_RETRY"
    PAYMENT_LINK = "PAYMENT_LINK"
    EMAIL = "EMAIL"
    WHATSAPP = "WHATSAPP"
    HUMAN = "HUMAN"
    NONE = "NONE"


class CaseStatus(StrEnum):
    OPEN = "OPEN"
    ANALYZING = "ANALYZING"
    RECOMMENDED = "RECOMMENDED"
    IN_RECOVERY = "IN_RECOVERY"
    RECOVERED = "RECOVERED"
    FAILED = "FAILED"
    ABANDONED = "ABANDONED"
    DO_NOTHING = "DO_NOTHING"
    CLOSED = "CLOSED"


class Priority(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"


class ActionStatus(StrEnum):
    PENDING = "PENDING"
    EXECUTED = "EXECUTED"
    BLOCKED = "BLOCKED"
    SUCCEEDED = "SUCCEEDED"
    FAILED = "FAILED"
    SIMULATED = "SIMULATED"


class ExecutionMode(StrEnum):
    """Distinguishes a real Razorpay test-mode call from a simulated action."""

    REAL_RAZORPAY_TEST = "REAL_RAZORPAY_TEST"
    REAL_RESEND_EMAIL = "REAL_RESEND_EMAIL"
    SIMULATED = "SIMULATED"


# Reason phrases that count as "recoverable" versus terminal, used by heuristics.
RECOVERABLE_FAILURES = {
    FailureReason.BANK_DECLINE,
    FailureReason.PAYMENT_TIMEOUT,
    FailureReason.NETWORK_ERROR,
    FailureReason.UPI_FAILURE,
    FailureReason.INSUFFICIENT_FUNDS,
}
