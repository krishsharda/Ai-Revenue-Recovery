"""Build full `AIDecisionInput` cases (with varied loss types) for simulation
and seeding. Clearly synthetic/demo data."""
from __future__ import annotations

import random
from typing import List

from ..ml.synthetic import generate_samples
from ..models.enums import FailureReason, RevenueLossType
from ..schemas.decision import AIDecisionInput

_LOSS_DISTRIBUTION = [
    (RevenueLossType.PAYMENT_FAILURE, 0.58),
    (RevenueLossType.CHECKOUT_ABANDONMENT, 0.20),
    (RevenueLossType.SUBSCRIPTION_FAILURE, 0.14),
    (RevenueLossType.OVERDUE_INVOICE, 0.08),
]


def _pick_loss(rng: random.Random) -> RevenueLossType:
    r = rng.random()
    cum = 0.0
    for loss, w in _LOSS_DISTRIBUTION:
        cum += w
        if r <= cum:
            return loss
    return RevenueLossType.PAYMENT_FAILURE


def generate_case_inputs(n: int, seed: int = 42) -> List[AIDecisionInput]:
    samples, _labels = generate_samples(n, seed=seed)
    rng = random.Random(seed + 7)
    inputs: List[AIDecisionInput] = []
    for s in samples:
        loss = _pick_loss(rng)
        failure_reason = s["failure_reason"]
        if loss == RevenueLossType.CHECKOUT_ABANDONMENT:
            failure_reason = FailureReason.USER_ABANDONMENT.value
        inputs.append(
            AIDecisionInput(
                transaction_amount=s["transaction_amount"],
                payment_method=s["payment_method"],
                failure_reason=failure_reason,
                loss_type=loss,
                previous_successful_payments=s["previous_successful_payments"],
                previous_failed_payments=s["previous_failed_payments"],
                historical_recovery_rate=s["historical_recovery_rate"],
                customer_value=s["customer_value"],
                time_since_payment_failure_minutes=int(s["time_since_payment_failure_minutes"]),
                previous_recovery_attempts=s["previous_recovery_attempts"],
            )
        )
    return inputs
