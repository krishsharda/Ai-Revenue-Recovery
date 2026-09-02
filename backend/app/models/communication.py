from __future__ import annotations

from typing import Optional

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class CommunicationRecord(Base, TimestampMixin):
    """A real customer communication attempt (currently email via Resend).

    Delivery is tracked separately from revenue recovery: a SENT email does NOT
    mean the payment was recovered — only a Razorpay capture webhook does that.
    """

    __tablename__ = "communication_records"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    recovery_case_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("recovery_cases.id"), index=True, nullable=True
    )
    customer_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("customers.id"), index=True, nullable=True
    )

    channel: Mapped[str] = mapped_column(String(24), default="EMAIL")
    provider: Mapped[str] = mapped_column(String(32), default="resend")
    recipient: Mapped[Optional[str]] = mapped_column(String(255))
    subject: Mapped[Optional[str]] = mapped_column(String(300))
    status: Mapped[str] = mapped_column(String(16), default="PENDING", index=True)
    provider_message_id: Mapped[Optional[str]] = mapped_column(String(128))
    payment_link: Mapped[Optional[str]] = mapped_column(String(300))
    failure_reason: Mapped[Optional[str]] = mapped_column(Text)
    sent_at: Mapped[Optional[str]] = mapped_column(String(40))
