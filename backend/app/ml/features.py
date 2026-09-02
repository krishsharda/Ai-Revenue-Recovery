"""Feature engineering for the recovery-probability model.

Deterministic, explainable encoding. The same builder is used at training time
(on synthetic data) and inference time (on live cases), guaranteeing parity.

Pure Python by design: inference runs in a serverless function where numpy /
scipy / scikit-learn would blow past the bundle size limit and slow cold
starts. Training (offline, `scripts/train_model.py`) feeds these plain lists
straight to scikit-learn, which accepts them unchanged.
"""
from __future__ import annotations

import math
from typing import Dict, List

from ..models.enums import FailureReason, PaymentMethod

PAYMENT_METHODS: List[str] = [m.value for m in PaymentMethod]
FAILURE_REASONS: List[str] = [f.value for f in FailureReason]

CUSTOMER_VALUE_ORDINAL: Dict[str, float] = {"low": 0.0, "medium": 0.5, "high": 1.0}

FEATURE_NAMES: List[str] = (
    ["log_amount", "historical_recovery_rate", "success_rate",
     "prev_failed", "prev_success", "customer_value_ord",
     "time_since_failure_hours", "prev_recovery_attempts"]
    + [f"method_{m}" for m in PAYMENT_METHODS]
    + [f"reason_{r}" for r in FAILURE_REASONS]
)


def _get(d, key, default=None):
    if isinstance(d, dict):
        return d.get(key, default)
    return getattr(d, key, default)


def build_feature_dict(sample) -> Dict[str, float]:
    """Return the named feature vector for one case as a dict (for explainability)."""
    amount = float(_get(sample, "transaction_amount", _get(sample, "amount", 0.0)) or 0.0)
    prev_success = int(_get(sample, "previous_successful_payments", 0) or 0)
    prev_failed = int(_get(sample, "previous_failed_payments", 0) or 0)
    total = prev_success + prev_failed
    success_rate = (prev_success / total) if total > 0 else 0.0

    method = str(_get(sample, "payment_method", "card") or "card").lower()
    reason = str(_get(sample, "failure_reason", "UNKNOWN") or "UNKNOWN")
    cust_val = str(_get(sample, "customer_value", "medium") or "medium").lower()
    minutes = float(_get(sample, "time_since_payment_failure_minutes", 0) or 0)

    feats: Dict[str, float] = {
        "log_amount": math.log1p(max(0.0, amount)),
        "historical_recovery_rate": float(_get(sample, "historical_recovery_rate", 0.0) or 0.0),
        "success_rate": success_rate,
        "prev_failed": float(prev_failed),
        "prev_success": float(prev_success),
        "customer_value_ord": CUSTOMER_VALUE_ORDINAL.get(cust_val, 0.5),
        "time_since_failure_hours": minutes / 60.0,
        "prev_recovery_attempts": float(_get(sample, "previous_recovery_attempts", 0) or 0),
    }
    for m in PAYMENT_METHODS:
        feats[f"method_{m}"] = 1.0 if method == m else 0.0
    for r in FAILURE_REASONS:
        feats[f"reason_{r}"] = 1.0 if reason == r else 0.0
    return feats


def build_vector(sample) -> List[float]:
    d = build_feature_dict(sample)
    return [d[name] for name in FEATURE_NAMES]


def build_matrix(samples) -> List[List[float]]:
    return [build_vector(s) for s in samples]
