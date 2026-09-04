from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..agents.decision_engine import LLMDecisionUnavailable
from ..database import get_db
from ..schemas.recovery import PaginatedCases, RecoveryCaseDetail
from ..services import case_service, recovery_service

router = APIRouter(tags=["recovery-cases"])


class ExecuteRequest(BaseModel):
    simulate: bool = True
    force: bool = False


@router.get("/recovery-cases", response_model=PaginatedCases)
def list_cases(
    db: Session = Depends(get_db),
    status: str | None = None,
    risk_level: str | None = None,
    loss_type: str | None = None,
    recommended_action: str | None = None,
    search: str | None = None,
    sort: str = "expected_value",
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> PaginatedCases:
    return case_service.list_cases(
        db, status=status, risk_level=risk_level, loss_type=loss_type,
        recommended_action=recommended_action, search=search, sort=sort,
        limit=limit, offset=offset,
    )


@router.get("/recovery-cases/{case_id}", response_model=RecoveryCaseDetail)
def get_case(case_id: int, db: Session = Depends(get_db)) -> RecoveryCaseDetail:
    detail = case_service.get_case_detail(db, case_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Recovery case not found")
    return detail


@router.post("/recovery-cases/{case_id}/analyze", response_model=RecoveryCaseDetail)
def analyze_case(case_id: int, db: Session = Depends(get_db)) -> RecoveryCaseDetail:
    case = case_service.get_case(db, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Recovery case not found")
    try:
        recovery_service.analyze_case(db, case, require_llm=True)
    except LLMDecisionUnavailable as exc:
        db.rollback()
        raise HTTPException(
            status_code=503,
            detail=f"LLM analysis failed ({exc}). Check the deployed LLM_API_KEY, model, quota, and API logs.",
        ) from exc
    db.commit()
    return case_service.get_case_detail(db, case_id)


@router.post("/recovery-cases/{case_id}/execute")
def execute_case(case_id: int, body: ExecuteRequest | None = None, db: Session = Depends(get_db)) -> dict:
    body = body or ExecuteRequest()
    case = case_service.get_case(db, case_id)
    if case is None:
        raise HTTPException(status_code=404, detail="Recovery case not found")
    result = recovery_service.execute_case(db, case, simulate=body.simulate, force=body.force)
    db.commit()
    detail = case_service.get_case_detail(db, case_id)
    return {"result": result, "case": detail.model_dump(mode="json") if detail else None}
