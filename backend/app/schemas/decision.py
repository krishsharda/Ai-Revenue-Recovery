"""Strict schemas for the AI decision boundary.

The LLM produces `AIDecision` as JSON. It is validated here BEFORE the guardrail
engine ever sees it. This is the enforcement point for
"AI decides. Rules control. System executes." — the model's free-form output
can never bypass this typed contract.
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

from ..models.enums import (
    CustomerValue,
    FailureReason,
    PaymentMethod,
    RecoveryActionType,
    RecoveryChannel,
    RevenueLossType,
    RiskLevel,
)


class AIDecisionInput(BaseModel):
    """Structured features handed to the decision engine (LLM or heuristic)."""

    transaction_amount: float
    currency: str = "INR"
    payment_method: PaymentMethod = PaymentMethod.CARD
    failure_reason: FailureReason = FailureReason.UNKNOWN
    loss_type: RevenueLossType = RevenueLossType.PAYMENT_FAILURE
    previous_successful_payments: int = 0
    previous_failed_payments: int = 0
    historical_recovery_rate: float = 0.0
    customer_value: CustomerValue = CustomerValue.MEDIUM
    time_since_payment_failure_minutes: int = 0
    previous_recovery_attempts: int = 0
    previous_messages_sent: int = 0
    model_recovery_probability: float = Field(
        0.0, description="Probability from the ML model, provided to the LLM as evidence."
    )
    # Best historical action for this (loss_type, root_cause) from recovery memory.
    memory_best_action: Optional[str] = None
    memory_best_action_rate: Optional[float] = None


class AIDecision(BaseModel):
    """The validated recommendation. Never executed directly — only after guardrails."""

    risk_level: RiskLevel
    recovery_probability: float = Field(ge=0.0, le=1.0)
    root_cause_code: FailureReason = FailureReason.UNKNOWN
    root_cause: str = Field(min_length=1, max_length=200)
    recommended_action: RecoveryActionType
    channel: RecoveryChannel = RecoveryChannel.NONE
    delay_minutes: int = Field(default=0, ge=0, le=1440)
    max_attempts: int = Field(default=1, ge=1, le=5)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    reason: str = Field(min_length=1, max_length=600)
    signals: List[str] = Field(default_factory=list)
    decided_by: str = "heuristic"  # llm | heuristic | heuristic_fallback
    fallback_reason: Optional[str] = None  # set when decided_by == heuristic_fallback

    @field_validator("signals")
    @classmethod
    def _cap_signals(cls, v: List[str]) -> List[str]:
        # Keep the explainability list tidy; never fabricate beyond what fits.
        return [s.strip() for s in v if s and s.strip()][:8]

    @field_validator("recovery_probability", "confidence", mode="before")
    @classmethod
    def _clamp(cls, v):
        try:
            f = float(v)
        except (TypeError, ValueError):
            return 0.0
        return max(0.0, min(1.0, f))
