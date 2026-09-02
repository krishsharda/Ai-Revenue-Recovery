from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from ..schemas.dashboard import AnalyticsResponse
from ..services import analytics_service

router = APIRouter(tags=["analytics"])


@router.get("/analytics", response_model=AnalyticsResponse)
def get_analytics(db: Session = Depends(get_db)) -> AnalyticsResponse:
    return analytics_service.analytics(db)
