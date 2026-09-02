from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.audit_log import AuditLog
from ..schemas.audit import AuditLogOut, PaginatedAudit

router = APIRouter(tags=["audit"])


@router.get("/audit-logs", response_model=PaginatedAudit)
def list_audit_logs(
    db: Session = Depends(get_db),
    case_id: int | None = None,
    event: str | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
) -> PaginatedAudit:
    stmt = select(AuditLog)
    count_stmt = select(func.count()).select_from(AuditLog)
    if case_id is not None:
        stmt = stmt.where(AuditLog.recovery_case_id == case_id)
        count_stmt = count_stmt.where(AuditLog.recovery_case_id == case_id)
    if event:
        stmt = stmt.where(AuditLog.event == event)
        count_stmt = count_stmt.where(AuditLog.event == event)

    total = db.execute(count_stmt).scalar_one()
    rows = db.execute(
        stmt.order_by(AuditLog.id.desc()).limit(limit).offset(offset)
    ).scalars().all()
    return PaginatedAudit(total=total, items=[AuditLogOut.model_validate(r) for r in rows])
