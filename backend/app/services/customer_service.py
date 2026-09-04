"""Feature/context assembly for the decision pipeline + customer aggregates."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..models.customer import Customer
from ..models.enums import (
    CustomerValue,
    FailureReason,
    PaymentMethod,
    RecoveryActionType,
    RevenueLossType,
)
from ..models.recovery_action import RecoveryAction
from ..models.recovery_case import RecoveryCase
from ..models.transaction import Transaction
from ..schemas.decision import AIDecisionInput
from . import memory_service

_MESSAGE_ACTIONS = {
    RecoveryActionType.EMAIL.value,
    RecoveryActionType.WHATSAPP.value,
}
_RETRY_ACTIONS = {
    RecoveryActionType.RETRY_PAYMENT.value,
    RecoveryActionType.SCHEDULE_RETRY.value,
}
_MODEL_TIME_HORIZON_MINUTES = 12 * 60


def minutes_since(dt: datetime) -> int:
    if dt is None:
        return 0
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    delta = datetime.now(timezone.utc) - dt
    elapsed = max(0, int(delta.total_seconds() // 60))
    # The model is trained on a short active-recovery horizon. Without this
    # cap, old demo/live cases drift far outside its training distribution and
    # the logistic model can produce meaningless near-zero probabilities.
    return min(elapsed, _MODEL_TIME_HORIZON_MINUTES)


def action_counts(db: Session, case_id: int) -> tuple[int, int]:
    """Return (retries_used, messages_used) for a case from its executed actions."""
    rows = db.execute(
        select(RecoveryAction.action_type, func.count()).where(
            RecoveryAction.recovery_case_id == case_id,
            RecoveryAction.status.in_(["EXECUTED", "SIMULATED", "SUCCEEDED"]),
        ).group_by(RecoveryAction.action_type)
    ).all()
    retries = sum(c for a, c in rows if a in _RETRY_ACTIONS)
    messages = sum(c for a, c in rows if a in _MESSAGE_ACTIONS)
    return retries, messages


def _coerce_enum(enum_cls, value, default):
    try:
        return enum_cls(value)
    except (ValueError, TypeError):
        return default


def build_decision_input(
    db: Session, customer: Customer, txn: Transaction, case: RecoveryCase
) -> AIDecisionInput:
    from ..ml import get_model

    retries_used, messages_used = action_counts(db, case.id)
    root_cause = case.root_cause or txn.failure_reason

    mem_action, mem_rate = memory_service.best_action(
        db, txn.loss_type, root_cause or FailureReason.UNKNOWN.value
    )

    partial = AIDecisionInput(
        transaction_amount=txn.amount,
        currency=txn.currency,
        payment_method=_coerce_enum(PaymentMethod, txn.payment_method, PaymentMethod.CARD),
        failure_reason=_coerce_enum(FailureReason, txn.failure_reason, FailureReason.UNKNOWN),
        loss_type=_coerce_enum(RevenueLossType, txn.loss_type, RevenueLossType.PAYMENT_FAILURE),
        previous_successful_payments=customer.successful_transactions,
        previous_failed_payments=customer.failed_transactions,
        historical_recovery_rate=customer.historical_recovery_rate,
        customer_value=_coerce_enum(CustomerValue, customer.customer_value, CustomerValue.MEDIUM),
        time_since_payment_failure_minutes=minutes_since(txn.created_at),
        previous_recovery_attempts=retries_used,
        previous_messages_sent=messages_used,
        memory_best_action=mem_action,
        memory_best_action_rate=mem_rate,
    )
    partial.model_recovery_probability = get_model().predict_proba(partial)
    return partial


def recompute_aggregates(db: Session, customer: Customer) -> None:
    """Recompute a customer's transactional aggregates from their transactions."""
    txns = customer.transactions
    total = len(txns)
    success = sum(1 for t in txns if t.status == "CAPTURED")
    failed = sum(1 for t in txns if t.status in ("FAILED", "ABANDONED"))
    amounts = [t.amount for t in txns] or [0.0]
    customer.total_transactions = total
    customer.successful_transactions = success
    customer.failed_transactions = failed
    customer.average_payment_amount = round(sum(amounts) / len(amounts), 2)
    db.flush()
