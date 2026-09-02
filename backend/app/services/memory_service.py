"""Recovery memory: which action historically works for which loss/root cause.

An MVP learning layer implemented as measurable statistics. Outcomes feed back
into future recommendations via `best_action`.
"""
from __future__ import annotations

from typing import List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models.enums import RecoveryActionType
from ..models.recovery_memory import RecoveryMemory

# Actions that don't represent an "intervention we can learn a success rate for".
_NON_LEARNABLE = {RecoveryActionType.DO_NOTHING.value}


def record_outcome(
    db: Session,
    *,
    loss_type: str,
    root_cause: str,
    action_type: str,
    success: bool,
    amount: float,
    commit: bool = False,
) -> None:
    if action_type in _NON_LEARNABLE:
        return
    row = db.execute(
        select(RecoveryMemory).where(
            RecoveryMemory.loss_type == loss_type,
            RecoveryMemory.root_cause == root_cause,
            RecoveryMemory.action_type == action_type,
        )
    ).scalar_one_or_none()
    if row is None:
        row = RecoveryMemory(
            loss_type=loss_type, root_cause=root_cause, action_type=action_type,
            attempts=0, successes=0, recovered_amount=0.0,
        )
        db.add(row)
    row.attempts = (row.attempts or 0) + 1
    if success:
        row.successes = (row.successes or 0) + 1
        row.recovered_amount = (row.recovered_amount or 0.0) + amount
    db.flush()
    if commit:
        db.commit()


def best_action(
    db: Session, loss_type: str, root_cause: str, min_attempts: int = 3
) -> Tuple[Optional[str], Optional[float]]:
    rows = db.execute(
        select(RecoveryMemory).where(
            RecoveryMemory.loss_type == loss_type,
            RecoveryMemory.root_cause == root_cause,
            RecoveryMemory.attempts >= min_attempts,
        )
    ).scalars().all()
    if not rows:
        return None, None
    best = max(rows, key=lambda r: r.success_rate)
    return best.action_type, best.success_rate


def get_stat(db: Session, loss_type: str, root_cause: str, action_type: str) -> Optional[RecoveryMemory]:
    return db.execute(
        select(RecoveryMemory).where(
            RecoveryMemory.loss_type == loss_type,
            RecoveryMemory.root_cause == root_cause,
            RecoveryMemory.action_type == action_type,
        )
    ).scalar_one_or_none()


def list_memory(db: Session) -> List[RecoveryMemory]:
    return db.execute(
        select(RecoveryMemory).order_by(RecoveryMemory.attempts.desc())
    ).scalars().all()
