"""Synthetic case generator — demo data for training and simulation.

Clearly labelled DEMO data. A latent logistic process links case features to a
recovery outcome so that a LogisticRegression fit on this data learns sensible,
explainable coefficients (recoverable failures + reliable customers recover
more; retry fatigue + expired cards + abandonment recover less).

Pure Python (stdlib `random`) rather than numpy: the simulation endpoint calls
this at runtime, and numpy would otherwise be pulled into the serverless
bundle purely to draw random numbers. Seeded runs remain fully reproducible.
"""
from __future__ import annotations

import math
import random
from typing import Dict, List, Tuple

from ..models.enums import FailureReason, PaymentMethod

# Base recovery propensity per failure reason (log-odds contribution).
_REASON_WEIGHT: Dict[str, float] = {
    FailureReason.BANK_DECLINE.value: 0.8,
    FailureReason.PAYMENT_TIMEOUT.value: 1.0,
    FailureReason.NETWORK_ERROR.value: 1.1,
    FailureReason.UPI_FAILURE.value: 0.6,
    FailureReason.INSUFFICIENT_FUNDS.value: -0.3,
    FailureReason.CARD_EXPIRED.value: -1.2,
    FailureReason.USER_ABANDONMENT.value: -1.7,
    FailureReason.UNKNOWN.value: -0.6,
}

_METHOD_WEIGHT: Dict[str, float] = {
    PaymentMethod.UPI.value: 0.3,
    PaymentMethod.CARD.value: 0.1,
    PaymentMethod.NETBANKING.value: 0.0,
    PaymentMethod.WALLET.value: 0.2,
    PaymentMethod.EMI.value: -0.2,
}

_REASONS = list(_REASON_WEIGHT.keys())
_METHODS = list(_METHOD_WEIGHT.keys())

# Realistic distribution of failure reasons in the wild (order matches _REASONS).
_REASON_WEIGHTS = [0.22, 0.10, 0.08, 0.18, 0.16, 0.08, 0.14, 0.04]

_CUSTOMER_VALUES = ["low", "medium", "high"]
_CUSTOMER_VALUE_WEIGHTS = [0.35, 0.4, 0.25]


def _sigmoid(x: float) -> float:
    if x >= 0:
        return 1.0 / (1.0 + math.exp(-x))
    e = math.exp(x)
    return e / (1.0 + e)


def _poisson(rng: random.Random, lam: float) -> int:
    """Knuth's algorithm — exact, and fast enough for the small lambdas used here."""
    limit = math.exp(-lam)
    k = 0
    p = 1.0
    while True:
        p *= rng.random()
        if p <= limit:
            return k
        k += 1


def generate_samples(n: int, seed: int = 42) -> Tuple[List[dict], List[int]]:
    """Return (feature dicts, binary recovery labels)."""
    rng = random.Random(seed)
    samples: List[dict] = []
    labels: List[int] = []

    for _ in range(n):
        reason = rng.choices(_REASONS, weights=_REASON_WEIGHTS)[0]
        method = rng.choice(_METHODS)
        amount = rng.gammavariate(2.0, 3500.0) + 200.0
        prev_success = _poisson(rng, 6)
        prev_failed = _poisson(rng, 2)
        total = prev_success + prev_failed
        base_hist = (prev_success / total) if total else rng.uniform(0.2, 0.8)
        historical_recovery_rate = min(1.0, max(0.0, base_hist + rng.gauss(0, 0.12)))
        cust_val = rng.choices(_CUSTOMER_VALUES, weights=_CUSTOMER_VALUE_WEIGHTS)[0]
        minutes = abs(rng.gauss(120, 120))
        prev_attempts = rng.randrange(0, 3)

        sample = {
            "transaction_amount": round(amount, 2),
            "payment_method": method,
            "failure_reason": reason,
            "previous_successful_payments": prev_success,
            "previous_failed_payments": prev_failed,
            "historical_recovery_rate": round(historical_recovery_rate, 3),
            "customer_value": cust_val,
            "time_since_payment_failure_minutes": round(minutes, 1),
            "previous_recovery_attempts": prev_attempts,
        }

        # Latent log-odds of recovery.
        cust_ord = {"low": 0.0, "medium": 0.5, "high": 1.0}[cust_val]
        z = (
            -1.1
            + _REASON_WEIGHT[reason]
            + _METHOD_WEIGHT[method]
            + 2.6 * historical_recovery_rate
            + 1.7 * (prev_success / (total + 1))
            + 0.9 * cust_ord
            - 0.8 * prev_attempts
            - 0.5 * (minutes / 120.0)
            - 0.22 * math.log1p(amount / 5000.0)
            + rng.gauss(0, 0.5)
        )
        labels.append(int(rng.random() < _sigmoid(z)))
        samples.append(sample)

    return samples, labels
