from __future__ import annotations

from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class RecoveryAction(Base, TimestampMixin):
    """An executed (or blocked/simulated) recovery action."""

    __tablename__ = "recovery_actions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    recovery_case_id: Mapped[int] = mapped_column(
        ForeignKey("recovery_cases.id"), index=True
    )

    action_type: Mapped[str] = mapped_column(String(32), nullable=False)
    channel: Mapped[Optional[str]] = mapped_column(String(24))
    status: Mapped[str] = mapped_column(String(24), default="PENDING")
    execution_mode: Mapped[str] = mapped_column(String(32), default="SIMULATED")
    attempt_number: Mapped[int] = mapped_column(Integer, default=1)
    result: Mapped[Optional[str]] = mapped_column(Text)
    # e.g. Razorpay payment-link id / url when a link is generated.
    external_reference: Mapped[Optional[str]] = mapped_column(String(256))
    executed_at: Mapped[Optional[str]] = mapped_column(String(40))

    recovery_case: Mapped["RecoveryCase"] = relationship(back_populates="actions")  # noqa: F821
