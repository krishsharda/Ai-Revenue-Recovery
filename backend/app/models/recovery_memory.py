from __future__ import annotations

from sqlalchemy import Float, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base, TimestampMixin


class RecoveryMemory(Base, TimestampMixin):
    """Aggregated learning: which action works for which (loss_type, root_cause).

    This is the MVP's "recovery learning layer" — a measurable historical
    statistics table rather than full reinforcement learning. It feeds future
    recommendations via the memory service.
    """

    __tablename__ = "recovery_memory"
    __table_args__ = (
        UniqueConstraint("loss_type", "root_cause", "action_type", name="uq_memory_key"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    loss_type: Mapped[str] = mapped_column(String(32), index=True)
    root_cause: Mapped[str] = mapped_column(String(48), index=True)
    action_type: Mapped[str] = mapped_column(String(32), index=True)

    attempts: Mapped[int] = mapped_column(Integer, default=0)
    successes: Mapped[int] = mapped_column(Integer, default=0)
    recovered_amount: Mapped[float] = mapped_column(Float, default=0.0)

    @property
    def success_rate(self) -> float:
        if self.attempts <= 0:
            return 0.0
        return round(self.successes / self.attempts, 4)
