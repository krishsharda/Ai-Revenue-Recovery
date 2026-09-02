"""Train the recovery-probability model and write its parameters to JSON.

Offline / development only — this is the one place scikit-learn is needed.
It rewrites `app/ml/model_params.json`, which the runtime loads with plain
Python (no numpy / scipy / scikit-learn in the deployed bundle).

Usage (from backend/):
    pip install -r requirements-dev.txt
    python -m scripts.train_model
"""
from __future__ import annotations

from app.config import settings
from app.logging_config import configure_logging
from app.ml.model import PARAMS_PATH, RecoveryProbabilityModel


def main() -> None:
    configure_logging()
    model = RecoveryProbabilityModel().train(seed=settings.ml_random_seed)
    model.save(PARAMS_PATH)
    print(f"Trained on {model.trained_on} synthetic samples "
          f"(train accuracy={model.train_accuracy:.3f}); saved to {PARAMS_PATH}")


if __name__ == "__main__":
    main()
