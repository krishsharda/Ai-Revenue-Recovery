"""Read/query helpers for recovery cases used by the API layer."""
from __future__ import annotations

import json
from typing import List, Optional

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from ..models.customer import Customer
from ..models.recovery_case import RecoveryCase
from ..models.transaction import Transaction
from ..schemas.recovery import (
    ActionOut,
    CommunicationOut,
    CustomerOut,
    DecisionOut,
    EventOut,
    PaginatedCases,
    RecoveryCaseDetail,
    RecoveryCaseListItem,
    RecoveryCaseOut,
    TransactionOut,
)
from . import decision_intel


def list_cases(
    db: Session,
    *,
    status: Optional[str] = None,
    risk_level: Optional[str] = None,
    loss_type: Optional[str] = None,
    recommended_action: Optional[str] = None,
    search: Optional[str] = None,
    sort: str = "expected_value",
    limit: int = 50,
    offset: int = 0,
) -> PaginatedCases:
    stmt = (
        select(RecoveryCase, Transaction, Customer)
        .join(Transaction, RecoveryCase.transaction_id == Transaction.id)
        .join(Customer, Transaction.customer_id == Customer.id)
    )
    if status:
        stmt = stmt.where(RecoveryCase.status == status)
    if risk_level:
        stmt = stmt.where(RecoveryCase.risk_level == risk_level)
    if loss_type:
        stmt = stmt.where(RecoveryCase.loss_type == loss_type)
    if recommended_action:
        stmt = stmt.where(RecoveryCase.recommended_action == recommended_action)
    if search:
        like = f"%{search}%"
        stmt = stmt.where(or_(Customer.name.ilike(like), Customer.email.ilike(like)))

    all_rows = db.execute(stmt).all()
    total = len(all_rows)

    sort_key = {
        "expected_value": lambda r: r[0].expected_recovery_value,
        "amount": lambda r: r[1].amount,
        "probability": lambda r: r[0].recovery_probability,
        "created": lambda r: r[0].created_at,
    }.get(sort, lambda r: r[0].expected_recovery_value)
    all_rows.sort(key=sort_key, reverse=True)

    page = all_rows[offset: offset + limit]
    items = [_to_list_item(c, t, cu) for c, t, cu in page]
    return PaginatedCases(total=total, items=items)


def _to_list_item(case, txn, customer) -> RecoveryCaseListItem:
    base = RecoveryCaseOut.model_validate(case, from_attributes=True).model_dump()
    return RecoveryCaseListItem(
        **base,
        customer_name=customer.name,
        customer_value=customer.customer_value,
        amount=txn.amount,
        currency=txn.currency,
        payment_method=txn.payment_method,
        failure_reason=txn.failure_reason,
    )


def get_case(db: Session, case_id: int) -> Optional[RecoveryCase]:
    return db.execute(
        select(RecoveryCase)
        .where(RecoveryCase.id == case_id)
        .options(
            selectinload(RecoveryCase.decisions),
            selectinload(RecoveryCase.actions),
            selectinload(RecoveryCase.events),
            selectinload(RecoveryCase.transaction).selectinload(Transaction.customer),
        )
    ).scalar_one_or_none()


def get_case_detail(db: Session, case_id: int) -> Optional[RecoveryCaseDetail]:
    case = get_case(db, case_id)
    if case is None:
        return None
    txn = case.transaction
    customer = txn.customer
    latest = case.decisions[-1] if case.decisions else None
    base = RecoveryCaseOut.model_validate(case, from_attributes=True).model_dump()
    return RecoveryCaseDetail(
        **base,
        customer=CustomerOut.model_validate(customer, from_attributes=True),
        transaction=TransactionOut.model_validate(txn, from_attributes=True),
        decisions=[DecisionOut.model_validate(d, from_attributes=True) for d in case.decisions],
        actions=[ActionOut.model_validate(a, from_attributes=True) for a in case.actions],
        events=[EventOut.model_validate(e, from_attributes=True) for e in case.events],
        explainability=_explainability(case),
        intervention_options=decision_intel.compute_intervention_options(db, case),
        communications=_communications(db, case_id),
        decided_by=latest.decided_by if latest else None,
        fallback_reason=_fallback_reason(latest),
    )


def _communications(db: Session, case_id: int) -> List[CommunicationOut]:
    from ..models.communication import CommunicationRecord
    from .email_service import mask_email

    rows = db.execute(
        select(CommunicationRecord).where(CommunicationRecord.recovery_case_id == case_id)
        .order_by(CommunicationRecord.id)
    ).scalars().all()
    out = []
    for r in rows:
        item = CommunicationOut.model_validate(r, from_attributes=True)
        item.recipient = mask_email(r.recipient)  # never expose the full address in the API
        out.append(item)
    return out


def _fallback_reason(latest) -> Optional[str]:
    if not latest or not latest.rationale_signals:
        return None
    try:
        return json.loads(latest.rationale_signals).get("fallback_reason")
    except (json.JSONDecodeError, AttributeError):
        return None


def _explainability(case: RecoveryCase) -> List[str]:
    if not case.decisions:
        return []
    latest = case.decisions[-1]
    signals: List[str] = []
    if latest.rationale_signals:
        try:
            data = json.loads(latest.rationale_signals)
            signals = list(data.get("signals", []))
        except (json.JSONDecodeError, AttributeError):
            signals = []
    return signals
