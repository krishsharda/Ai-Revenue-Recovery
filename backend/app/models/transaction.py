from __future__ import annotations

from typing import List, Optional

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class Transaction(Base, TimestampMixin):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), index=True)

    razorpay_payment_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    razorpay_order_id: Mapped[Optional[str]] = mapped_column(String(64), index=True)
    razorpay_payment_link_id: Mapped[Optional[str]] = mapped_column(String(64))

    amount: Mapped[float] = mapped_column(Float, nullable=False)  # in rupees
    currency: Mapped[str] = mapped_column(String(8), default="INR")
    payment_method: Mapped[str] = mapped_column(String(24), default="card")
    status: Mapped[str] = mapped_column(String(24), default="FAILED", index=True)
    failure_reason: Mapped[Optional[str]] = mapped_column(String(32))
    loss_type: Mapped[str] = mapped_column(String(32), default="PAYMENT_FAILURE", index=True)
    is_synthetic: Mapped[bool] = mapped_column(default=False, index=True)

    customer: Mapped["Customer"] = relationship(back_populates="transactions")  # noqa: F821
    attempts: Mapped[List["PaymentAttempt"]] = relationship(  # noqa: F821
        back_populates="transaction", cascade="all, delete-orphan"
    )
    recovery_case: Mapped[Optional["RecoveryCase"]] = relationship(  # noqa: F821
        back_populates="transaction", uselist=False, cascade="all, delete-orphan"
    )


class PaymentAttempt(Base, TimestampMixin):
    __tablename__ = "payment_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    transaction_id: Mapped[int] = mapped_column(ForeignKey("transactions.id"), index=True)
    attempt_number: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[str] = mapped_column(String(24), default="FAILED")
    failure_reason: Mapped[Optional[str]] = mapped_column(String(32))
    razorpay_payment_id: Mapped[Optional[str]] = mapped_column(String(64))

    transaction: Mapped["Transaction"] = relationship(back_populates="attempts")
