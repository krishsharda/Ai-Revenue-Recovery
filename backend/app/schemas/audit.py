from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class AuditLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    recovery_case_id: Optional[int] = None
    actor: str
    event: str
    action: Optional[str] = None
    result: Optional[str] = None
    reason: Optional[str] = None
    input_data: Optional[str] = None
    decision_data: Optional[str] = None
    created_at: datetime


class PaginatedAudit(BaseModel):
    total: int
    items: List[AuditLogOut]
