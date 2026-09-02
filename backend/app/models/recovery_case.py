from __future__ import annotations

from typing import List, Optional

from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class RecoveryCase(Base, TimestampMixin):
    __tablename__ = "recovery_cases"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transaction_id: Mapped[int] = mapped_column(
        ForeignKey("transactions.id"), unique=True, index=True
    )

    loss_type: Mapped[str] = mapped_column(String(32), default="PAYMENT_FAILURE", index=True)
    risk_level: Mapped[str] = mapped_column(String(16), default="MEDIUM", index=True)
    recovery_probability: Mapped[float] = mapped_column(Float, default=0.0)
    expected_recovery_value: Mapped[float] = mapped_column(Float, default=0.0)
    root_cause: Mapped[Optional[str]] = mapped_column(String(48))
    root_cause_detail: Mapped[Optional[str]] = mapped_column(Text)
    recommended_action: Mapped[Optional[str]] = mapped_column(String(32), index=True)
    recommended_channel: Mapped[Optional[str]] = mapped_column(String(24))
    status: Mapped[str] = mapped_column(String(24), default="OPEN", index=True)
    priority: Mapped[str] = mapped_column(String(16), default="MEDIUM", index=True)

    # Amount actually recovered (0 until a successful capture is measured).
    recovered_amount: Mapped[float] = mapped_column(Float, default=0.0)

    transaction: Mapped["Transaction"] = relationship(back_populates="recovery_case")  # noqa: F821
    decisions: Mapped[List["RecoveryDecision"]] = relationship(  # noqa: F821
        back_populates="recovery_case", cascade="all, delete-orphan", order_by="RecoveryDecision.id"
    )
    actions: Mapped[List["RecoveryAction"]] = relationship(  # noqa: F821
        back_populates="recovery_case", cascade="all, delete-orphan", order_by="RecoveryAction.id"
    )
    events: Mapped[List["RecoveryEvent"]] = relationship(  # noqa: F821
        back_populates="recovery_case", cascade="all, delete-orphan", order_by="RecoveryEvent.id"
    )

    @property
    def is_terminal(self) -> bool:
        return self.status in {"RECOVERED", "FAILED", "ABANDONED", "CLOSED", "DO_NOTHING"}
