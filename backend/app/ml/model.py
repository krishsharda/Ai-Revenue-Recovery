"""Explainable recovery-probability model (standardised logistic regression).

The model outputs a calibrated probability plus per-feature contributions so the
UI can show *why* a probability was predicted — without ever inventing facts.

Inference is pure Python against parameters stored in `model_params.json`
(mean/scale from the StandardScaler, plus the LogisticRegression coefficients).
That keeps scikit-learn, scipy and numpy out of the deployed runtime: the
serverless bundle stays small and cold starts stay fast. Training still uses
scikit-learn, but only offline via `scripts/train_model.py`, which imports it
lazily and rewrites the JSON.
"""
from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from typing import Dict, List, Sequence

from ..logging_config import get_logger
from .features import FEATURE_NAMES, build_feature_dict, build_matrix, build_vector

logger = get_logger(__name__)

MODEL_VERSION = "logreg-v1"

# Parameters ship inside the package so inference works on a read-only
# filesystem (serverless) with no training step and no external download.
PARAMS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "model_params.json")


@dataclass
class Explanation:
    probability: float
    top_positive: List[Dict[str, float]]
    top_negative: List[Dict[str, float]]


def _sigmoid(z: float) -> float:
    # Branch to avoid math.exp overflow on large-magnitude logits.
    if z >= 0:
        return 1.0 / (1.0 + math.exp(-z))
    e = math.exp(z)
    return e / (1.0 + e)


class RecoveryProbabilityModel:
    """Standardise → linear combination → sigmoid, in plain Python."""

    def __init__(
        self,
        *,
        mean: Sequence[float] | None = None,
        scale: Sequence[float] | None = None,
        coef: Sequence[float] | None = None,
        intercept: float = 0.0,
        version: str = MODEL_VERSION,
        trained_on: int = 0,
        train_accuracy: float = 0.0,
    ) -> None:
        self.mean = list(mean or [])
        # Guard against zero-variance features producing a division by zero.
        self.scale = [s if s > 1e-12 else 1.0 for s in (scale or [])]
        self.coef = list(coef or [])
        self.intercept = float(intercept)
        self.version = version
        self.trained_on = trained_on
        self.train_accuracy = train_accuracy

    @property
    def is_fitted(self) -> bool:
        return bool(self.coef) and len(self.coef) == len(FEATURE_NAMES)

    # -- inference -----------------------------------------------------------
    def _scaled(self, sample) -> List[float]:
        x = build_vector(sample)
        return [(x[i] - self.mean[i]) / self.scale[i] for i in range(len(x))]

    def predict_proba(self, sample) -> float:
        z = self.intercept
        for xi, ci in zip(self._scaled(sample), self.coef):
            z += xi * ci
        return round(max(0.0, min(1.0, _sigmoid(z))), 4)

    def explain(self, sample, top_k: int = 4) -> Explanation:
        """Return per-feature signed contributions for this specific case."""
        x = build_vector(sample)
        x_scaled = self._scaled(sample)
        contributions = [x_scaled[i] * self.coef[i] for i in range(len(self.coef))]

        named = [
            {"feature": FEATURE_NAMES[i], "contribution": round(contributions[i], 4),
             "value": round(x[i], 4)}
            for i in range(len(FEATURE_NAMES))
            if abs(contributions[i]) > 1e-6
        ]
        pos = sorted([c for c in named if c["contribution"] > 0],
                     key=lambda c: c["contribution"], reverse=True)[:top_k]
        neg = sorted([c for c in named if c["contribution"] < 0],
                     key=lambda c: c["contribution"])[:top_k]
        return Explanation(
            probability=self.predict_proba(sample), top_positive=pos, top_negative=neg
        )

    # -- training (offline only; scikit-learn imported lazily) ---------------
    def train(self, n_samples: int = 4000, seed: int = 42) -> "RecoveryProbabilityModel":
        """Fit on synthetic data and absorb the parameters. Requires scikit-learn."""
        from sklearn.linear_model import LogisticRegression  # noqa: PLC0415
        from sklearn.pipeline import Pipeline  # noqa: PLC0415
        from sklearn.preprocessing import StandardScaler  # noqa: PLC0415

        from .synthetic import generate_samples  # noqa: PLC0415

        samples, labels = generate_samples(n_samples, seed=seed)
        X = build_matrix(samples)
        pipe = Pipeline(
            steps=[
                ("scaler", StandardScaler()),
                ("clf", LogisticRegression(max_iter=1000, C=1.0)),
            ]
        )
        pipe.fit(X, labels)

        scaler = pipe.named_steps["scaler"]
        clf = pipe.named_steps["clf"]
        self.mean = [float(v) for v in scaler.mean_]
        self.scale = [max(float(v) ** 0.5, 1e-12) for v in scaler.var_]
        self.coef = [float(v) for v in clf.coef_[0]]
        self.intercept = float(clf.intercept_[0])
        self.trained_on = n_samples
        self.train_accuracy = float(pipe.score(X, labels))
        logger.info(
            "Trained recovery model on %d synthetic samples (train acc=%.3f)",
            n_samples,
            self.train_accuracy,
        )
        return self

    # -- persistence ---------------------------------------------------------
    def save(self, path: str = PARAMS_PATH) -> None:
        payload = {
            "version": self.version,
            "trained_on": self.trained_on,
            "train_accuracy": self.train_accuracy,
            "feature_names": FEATURE_NAMES,
            "mean": self.mean,
            "scale": self.scale,
            "coef": self.coef,
            "intercept": self.intercept,
        }
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
            f.write("\n")
        logger.info("Saved recovery model parameters to %s", path)

    @classmethod
    def load(cls, path: str = PARAMS_PATH) -> "RecoveryProbabilityModel":
        with open(path, encoding="utf-8") as f:
            data = json.load(f)

        names = data.get("feature_names", [])
        if names and names != FEATURE_NAMES:
            raise ValueError(
                "model_params.json was trained on a different feature set "
                f"({len(names)} features) than the current code expects "
                f"({len(FEATURE_NAMES)}). Re-run scripts/train_model.py."
            )
        return cls(
            mean=data["mean"],
            scale=data["scale"],
            coef=data["coef"],
            intercept=data["intercept"],
            version=data.get("version", MODEL_VERSION),
            trained_on=data.get("trained_on", 0),
            train_accuracy=data.get("train_accuracy", 0.0),
        )


def human_readable_signals(sample, explanation: Explanation) -> List[str]:
    """Translate the strongest feature contributions into plain-language bullets.

    Only reflects real feature values — never fabricates supporting facts.
    """
    feats = build_feature_dict(sample)
    signals: List[str] = []

    def prev_success() -> int:
        return int(feats.get("prev_success", 0))

    if feats.get("historical_recovery_rate", 0) >= 0.6:
        signals.append(
            f"Strong historical recovery rate ({feats['historical_recovery_rate']*100:.0f}%)"
        )
    if prev_success() >= 5:
        signals.append(f"{prev_success()} previous successful payments")
    if feats.get("customer_value_ord", 0) >= 1.0:
        signals.append("High-value customer")
    if feats.get("success_rate", 0) >= 0.7:
        signals.append(f"Reliable payer ({feats['success_rate']*100:.0f}% success rate)")
    if feats.get("prev_recovery_attempts", 0) >= 2:
        signals.append("Multiple prior recovery attempts already made (fatigue)")
    if feats.get("reason_USER_ABANDONMENT", 0) == 1.0:
        signals.append("Checkout abandoned — weaker payment intent")
    if feats.get("reason_CARD_EXPIRED", 0) == 1.0:
        signals.append("Card expired — needs a new payment instrument")
    return signals[:6]
