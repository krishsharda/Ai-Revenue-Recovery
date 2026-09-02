from __future__ import annotations

from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class RecoveryEvent(Base, TimestampMixin):
    """A timeline entry for a recovery case (drives the case-detail timeline)."""

    __tablename__ = "recovery_events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    recovery_case_id: Mapped[int] = mapped_column(
        ForeignKey("recovery_cases.id"), index=True
    )
    label: Mapped[str] = mapped_column(String(120), nullable=False)
    detail: Mapped[Optional[str]] = mapped_column(Text)
    actor: Mapped[str] = mapped_column(String(48), default="system")
    icon: Mapped[Optional[str]] = mapped_column(String(32))

    recovery_case: Mapped["RecoveryCase"] = relationship(back_populates="events")  # noqa: F821
