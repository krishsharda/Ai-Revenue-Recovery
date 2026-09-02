"""Expected-recovery-value comparison across candidate interventions.

For a case we estimate, per strategy:
    success_probability = ML recovery probability  ×  strategy affinity for the
                          root cause, blended with Recovery Memory history.
    expected_value      = transaction amount × success_probability

This makes the "why this action" transparent: we show the expected rupees
recovered by each strategy and highlight the one the AI chose. DO_NOTHING is
scored at a small natural-recovery rate (some customers pay on their own).
"""
from __future__ import annotations

from typing import List

from sqlalchemy.orm import Session

from ..models.enums import FailureReason, RecoveryActionType
from ..models.recovery_case import RecoveryCase
from ..schemas.recovery import InterventionOption
from . import memory_service

# Strategy affinity per root cause (multiplier on the ML recovery probability).
_AFFINITY = {
    FailureReason.BANK_DECLINE.value: {
        "RETRY_PAYMENT": 1.0, "PAYMENT_LINK": 0.9, "ALTERNATE_PAYMENT_METHOD": 0.92, "EMAIL": 0.55},
    FailureReason.PAYMENT_TIMEOUT.value: {
        "RETRY_PAYMENT": 1.05, "PAYMENT_LINK": 0.9, "ALTERNATE_PAYMENT_METHOD": 0.85, "EMAIL": 0.5},
    FailureReason.NETWORK_ERROR.value: {
        "RETRY_PAYMENT": 1.05, "PAYMENT_LINK": 0.9, "ALTERNATE_PAYMENT_METHOD": 0.85, "EMAIL": 0.5},
    FailureReason.UPI_FAILURE.value: {
        "RETRY_PAYMENT": 0.6, "PAYMENT_LINK": 1.0, "ALTERNATE_PAYMENT_METHOD": 0.88, "EMAIL": 0.5},
    FailureReason.INSUFFICIENT_FUNDS.value: {
        "RETRY_PAYMENT": 0.5, "PAYMENT_LINK": 0.75, "ALTERNATE_PAYMENT_METHOD": 0.7, "EMAIL": 0.55},
    FailureReason.CARD_EXPIRED.value: {
        "RETRY_PAYMENT": 0.12, "PAYMENT_LINK": 0.8, "ALTERNATE_PAYMENT_METHOD": 1.0, "EMAIL": 0.55},
    FailureReason.USER_ABANDONMENT.value: {
        "RETRY_PAYMENT": 0.4, "PAYMENT_LINK": 1.0, "ALTERNATE_PAYMENT_METHOD": 0.7, "EMAIL": 0.92},
    FailureReason.UNKNOWN.value: {
        "RETRY_PAYMENT": 0.7, "PAYMENT_LINK": 0.85, "ALTERNATE_PAYMENT_METHOD": 0.8, "EMAIL": 0.6},
}

_CANDIDATES = [
    (RecoveryActionType.RETRY_PAYMENT.value, "Retry Payment"),
    (RecoveryActionType.PAYMENT_LINK.value, "Payment Link"),
    (RecoveryActionType.ALTERNATE_PAYMENT_METHOD.value, "Alternate Method"),
    (RecoveryActionType.EMAIL.value, "Email Nudge"),
    (RecoveryActionType.DO_NOTHING.value, "Do Nothing"),
]

_NATURAL_RECOVERY = 0.04  # some customers complete payment unprompted
_DEFAULT_AFFINITY = 0.6


def _clamp(v: float) -> float:
    return max(0.0, min(0.98, v))


def compute_intervention_options(db: Session, case: RecoveryCase) -> List[InterventionOption]:
    amount = case.transaction.amount if case.transaction else 0.0
    base = case.recovery_probability or 0.0
    root_cause = case.root_cause or FailureReason.UNKNOWN.value
    loss_type = case.loss_type
    affinities = _AFFINITY.get(root_cause, _AFFINITY[FailureReason.UNKNOWN.value])

    options: List[InterventionOption] = []
    for action, label in _CANDIDATES:
        note = None
        if action == RecoveryActionType.DO_NOTHING.value:
            p = _NATURAL_RECOVERY
        else:
            # Anchor to THIS customer's calibrated odds × strategy fit for the root
            # cause. Historical memory is shown as context, not blended in (a
            # population average shouldn't inflate a below-average customer).
            p = _clamp(base * affinities.get(action, _DEFAULT_AFFINITY))
            mem = memory_service.get_stat(db, loss_type, root_cause, action)
            if mem and mem.attempts >= 2:
                note = f"Historical: {round(mem.success_rate * 100)}% · n={mem.attempts}"
        options.append(InterventionOption(
            action_type=action, label=label,
            success_probability=round(p, 4),
            expected_value=round(amount * p, 2),
            recommended=(action == case.recommended_action),
            note=note,
        ))

    options.sort(key=lambda o: o.expected_value, reverse=True)
    if options:
        options[0].is_best_value = True
    return options
