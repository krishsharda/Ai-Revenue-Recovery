from __future__ import annotations

from typing import Optional

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class RecoveryDecision(Base, TimestampMixin):
    """A single AI recommendation for a case (there can be several over time)."""

    __tablename__ = "recovery_decisions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    recovery_case_id: Mapped[int] = mapped_column(
        ForeignKey("recovery_cases.id"), index=True
    )

    decision: Mapped[str] = mapped_column(String(32), nullable=False)  # RecoveryActionType
    channel: Mapped[Optional[str]] = mapped_column(String(24))
    risk_level: Mapped[Optional[str]] = mapped_column(String(16))
    recovery_probability: Mapped[float] = mapped_column(Float, default=0.0)
    expected_recovery_value: Mapped[float] = mapped_column(Float, default=0.0)
    confidence: Mapped[float] = mapped_column(Float, default=0.0)
    delay_minutes: Mapped[int] = mapped_column(Integer, default=0)
    max_attempts: Mapped[int] = mapped_column(Integer, default=1)
    reason: Mapped[Optional[str]] = mapped_column(Text)
    root_cause: Mapped[Optional[str]] = mapped_column(String(48))
    decided_by: Mapped[str] = mapped_column(String(32), default="heuristic")  # llm | heuristic
    model_version: Mapped[str] = mapped_column(String(48), default="v1")
    # JSON string of the explainability signals that supported this decision.
    rationale_signals: Mapped[Optional[str]] = mapped_column(Text)

    recovery_case: Mapped["RecoveryCase"] = relationship(back_populates="decisions")  # noqa: F821
