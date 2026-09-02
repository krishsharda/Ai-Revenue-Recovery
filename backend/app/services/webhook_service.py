"""Razorpay webhook processing (idempotent).

payment.failed  -> create/analyze a recovery case (REAL Razorpay TEST event)
payment.captured / order.paid / payment_link.paid -> mark the matching case
                    recovered and stop the workflow.
"""
from __future__ import annotations

from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..agents.root_cause import from_razorpay
from ..logging_config import get_logger
from ..models.customer import Customer
from ..models.enums import PaymentMethod, TransactionStatus
from ..models.transaction import PaymentAttempt, Transaction
from . import recovery_service

logger = get_logger(__name__)

_CAPTURE_EVENTS = {"payment.captured", "order.paid", "payment_link.paid"}


def handle_event(db: Session, event: str, payload: dict, verified: bool) -> dict:
    entity = _extract_entity(payload)
    if event == "payment.failed":
        return _handle_failed(db, entity, verified)
    if event in _CAPTURE_EVENTS:
        return _handle_captured(db, entity, verified)
    logger.info("Ignoring unhandled webhook event: %s", event)
    return {"handled": False, "event": event}


def _handle_failed(db: Session, entity: dict, verified: bool) -> dict:
    payment_id = entity.get("id")
    order_id = entity.get("order_id")

    existing = _find_transaction(db, payment_id, order_id)
    if existing is not None:
        # Idempotent: record the attempt but don't duplicate the case.
        db.add(PaymentAttempt(
            transaction_id=existing.id, attempt_number=len(existing.attempts) + 1,
            status="FAILED", failure_reason=existing.failure_reason, razorpay_payment_id=payment_id))
        case, _ = recovery_service.get_or_create_case(db, existing)
        db.commit()
        return {"handled": True, "event": "payment.failed", "case_id": case.id,
                "duplicate": True, "real_event": verified}

    customer = _resolve_customer(db, entity)
    amount = float(entity.get("amount", 0)) / 100.0
    reason = from_razorpay(entity.get("error_code"), entity.get("error_description"))
    txn = Transaction(
        customer_id=customer.id,
        razorpay_payment_id=payment_id,
        razorpay_order_id=order_id,
        amount=amount,
        currency=entity.get("currency", "INR"),
        payment_method=_coerce_method(entity.get("method")),
        status=TransactionStatus.FAILED.value,
        failure_reason=reason.value,
        loss_type="PAYMENT_FAILURE",
        is_synthetic=False,
    )
    db.add(txn)
    db.flush()
    db.add(PaymentAttempt(transaction_id=txn.id, attempt_number=1, status="FAILED",
                          failure_reason=reason.value, razorpay_payment_id=payment_id))
    customer.failed_transactions = (customer.failed_transactions or 0) + 1
    customer.total_transactions = (customer.total_transactions or 0) + 1

    case = recovery_service.process_failed_transaction(db, txn, execute=False)
    db.commit()
    return {"handled": True, "event": "payment.failed", "case_id": case.id,
            "real_event": True, "verified": verified}


def _handle_captured(db: Session, entity: dict, verified: bool) -> dict:
    payment_id = entity.get("id")
    order_id = entity.get("order_id")
    txn = _find_transaction(db, payment_id, order_id)
    if txn is None:
        logger.info("Capture webhook for unknown transaction %s/%s", payment_id, order_id)
        return {"handled": True, "event": "captured", "matched": False, "real_event": True}
    case = recovery_service.mark_recovered_by_webhook(db, txn, payment_id)
    db.commit()
    return {"handled": True, "event": "captured", "matched": True,
            "case_id": case.id if case else None, "real_event": True, "verified": verified}


def _extract_entity(payload: dict) -> dict:
    p = payload.get("payload", payload)
    for key in ("payment", "order", "payment_link"):
        if key in p and isinstance(p[key], dict):
            return p[key].get("entity", p[key])
    if "entity" in p:
        return p["entity"]
    return p


def _find_transaction(db: Session, payment_id: Optional[str], order_id: Optional[str]) -> Optional[Transaction]:
    if payment_id:
        txn = db.execute(
            select(Transaction).where(Transaction.razorpay_payment_id == payment_id)
        ).scalars().first()
        if txn:
            return txn
    if order_id:
        return db.execute(
            select(Transaction).where(Transaction.razorpay_order_id == order_id)
        ).scalars().first()
    return None


def _resolve_customer(db: Session, entity: dict) -> Customer:
    email = entity.get("email")
    contact = entity.get("contact")
    if email:
        found = db.execute(select(Customer).where(Customer.email == email)).scalars().first()
        if found:
            return found
    cust = Customer(name=(email or contact or "Razorpay Customer"), email=email, phone=contact,
                    customer_value="medium", total_transactions=0, successful_transactions=0,
                    failed_transactions=0, historical_recovery_rate=0.0, average_payment_amount=0.0)
    db.add(cust)
    db.flush()
    return cust


def _coerce_method(method: Optional[str]) -> str:
    try:
        return PaymentMethod(str(method).lower()).value
    except (ValueError, TypeError):
        return PaymentMethod.CARD.value
