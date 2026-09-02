"""ML package: process-wide singleton for the recovery-probability model."""
from __future__ import annotations

from ..logging_config import get_logger
from .model import PARAMS_PATH, RecoveryProbabilityModel

logger = get_logger(__name__)

_model: RecoveryProbabilityModel | None = None


def get_model() -> RecoveryProbabilityModel:
    """Return the shared model, loading packaged parameters on first use.

    Parameters are committed alongside the code, so this never trains, never
    writes to disk and never needs scikit-learn at runtime — it works on the
    read-only filesystem of a serverless function. Re-train offline with
    `python -m scripts.train_model`.
    """
    global _model
    if _model is None:
        _model = RecoveryProbabilityModel.load(PARAMS_PATH)
        logger.info(
            "Loaded recovery model (v=%s, train acc=%.3f, n=%d).",
            _model.version,
            _model.train_accuracy,
            _model.trained_on,
        )
    return _model


def reset_model() -> None:
    global _model
    _model = None
