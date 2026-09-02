from __future__ import annotations

from typing import List

from sqlalchemy import Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base, TimestampMixin


class Customer(Base, TimestampMixin):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    email: Mapped[str | None] = mapped_column(String(255), index=True)
    phone: Mapped[str | None] = mapped_column(String(32))

    # Behavioural aggregates used as ML features and for AI context.
    total_transactions: Mapped[int] = mapped_column(Integer, default=0)
    successful_transactions: Mapped[int] = mapped_column(Integer, default=0)
    failed_transactions: Mapped[int] = mapped_column(Integer, default=0)
    historical_recovery_rate: Mapped[float] = mapped_column(Float, default=0.0)
    average_payment_amount: Mapped[float] = mapped_column(Float, default=0.0)
    customer_value: Mapped[str] = mapped_column(String(16), default="medium")
    opted_out: Mapped[bool] = mapped_column(default=False)
    last_payment_at: Mapped[str | None] = mapped_column(String(40))

    transactions: Mapped[List["Transaction"]] = relationship(  # noqa: F821
        back_populates="customer", cascade="all, delete-orphan"
    )

    @property
    def success_rate(self) -> float:
        if self.total_transactions <= 0:
            return 0.0
        return round(self.successful_transactions / self.total_transactions, 4)
