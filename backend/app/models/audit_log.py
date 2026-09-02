from __future__ import annotations

from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class AuditLog(Base, TimestampMixin):
    """Immutable-ish record of every important system decision/action.

    Powers the Audit Trail page and provides trust/compliance/debugging value.
    """

    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    recovery_case_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("recovery_cases.id"), index=True, nullable=True
    )
    actor: Mapped[str] = mapped_column(String(48), default="system", index=True)
    event: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    action: Mapped[Optional[str]] = mapped_column(String(64))
    result: Mapped[Optional[str]] = mapped_column(String(64))
    reason: Mapped[Optional[str]] = mapped_column(Text)
    # JSON strings kept as text for portability across SQLite/Postgres.
    input_data: Mapped[Optional[str]] = mapped_column(Text)
    decision_data: Mapped[Optional[str]] = mapped_column(Text)
