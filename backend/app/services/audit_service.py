"""Audit logging + case timeline events."""
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Optional

from sqlalchemy.orm import Session

from ..models.audit_log import AuditLog
from ..models.recovery_event import RecoveryEvent


def _dumps(value: Any) -> Optional[str]:
    if value is None:
        return None
    if isinstance(value, str):
        return value
    try:
        return json.dumps(value, default=str)
    except TypeError:
        return str(value)


def log(
    db: Session,
    *,
    event: str,
    actor: str = "system",
    action: Optional[str] = None,
    result: Optional[str] = None,
    reason: Optional[str] = None,
    input_data: Any = None,
    decision_data: Any = None,
    recovery_case_id: Optional[int] = None,
    commit: bool = False,
) -> AuditLog:
    entry = AuditLog(
        recovery_case_id=recovery_case_id,
        actor=actor,
        event=event,
        action=action,
        result=result,
        reason=reason,
        input_data=_dumps(input_data),
        decision_data=_dumps(decision_data),
    )
    db.add(entry)
    db.flush()
    if commit:
        db.commit()
    return entry


def add_event(
    db: Session,
    recovery_case_id: int,
    label: str,
    *,
    detail: Optional[str] = None,
    actor: str = "system",
    icon: Optional[str] = None,
    commit: bool = False,
) -> RecoveryEvent:
    evt = RecoveryEvent(
        recovery_case_id=recovery_case_id,
        label=label,
        detail=detail,
        actor=actor,
        icon=icon,
    )
    db.add(evt)
    db.flush()
    if commit:
        db.commit()
    return evt


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()
