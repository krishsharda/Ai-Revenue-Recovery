"""Realistic, regenerable demo seed data. All rows are clearly synthetic.

Creates ~14 customers across HIGH / MEDIUM / LOW recovery profiles, ~40
transactions spanning every failure reason and loss type, then runs the failed
ones through the pipeline (analyze; a subset executed) so the dashboard, funnel,
recovery memory and audit trail are populated on first launch.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List

from sqlalchemy import delete
from sqlalchemy.orm import Session

from ..logging_config import get_logger
from ..config import settings
from ..models.audit_log import AuditLog
from ..models.customer import Customer
from ..models.enums import (
    FailureReason,
    RecoveryActionType,
    RevenueLossType,
)
from ..models.recovery_action import RecoveryAction
from ..models.recovery_case import RecoveryCase
from ..models.recovery_decision import RecoveryDecision
from ..models.recovery_event import RecoveryEvent
from ..models.recovery_memory import RecoveryMemory
from ..models.transaction import PaymentAttempt, Transaction
from ..services import recovery_service

logger = get_logger(__name__)


@dataclass
class TxnSpec:
    amount: float
    method: str
    reason: str
    loss_type: str = RevenueLossType.PAYMENT_FAILURE.value
    execute: bool = False  # run guardrails+execute+measure at seed time


@dataclass
class CustomerSpec:
    name: str
    email: str
    phone: str | None
    value: str
    successful: int
    failed: int
    hist_rate: float
    avg_amount: float
    opted_out: bool
    txns: List[TxnSpec]


def _specs() -> List[CustomerSpec]:
    return [
        # --- Marquee HIGH-recovery opportunities (left active for the dashboard) ---
        CustomerSpec("Rahul Mehta", "rahul.mehta@example.test", "+919800000001", "high",
                     14, 2, 0.78, 11800, False,
                     [TxnSpec(12500, "card", FailureReason.BANK_DECLINE.value)]),
        CustomerSpec("Neha Kapoor", "neha.kapoor@example.test", "+919800000002", "high",
                     22, 1, 0.83, 28900, False,
                     [TxnSpec(35000, "card", FailureReason.BANK_DECLINE.value)]),
        CustomerSpec("Amit Sharma", "amit.sharma@example.test", "+919800000003", "high",
                     9, 2, 0.71, 7600, False,
                     [TxnSpec(8500, "upi", FailureReason.UPI_FAILURE.value)]),
        # --- HIGH profile, mixed outcomes ---
        CustomerSpec("Priya Nair", "priya.nair@example.test", "+919800000004", "high",
                     18, 3, 0.74, 15200, False,
                     [TxnSpec(21000, "netbanking", FailureReason.PAYMENT_TIMEOUT.value, execute=True),
                      TxnSpec(4500, "upi", FailureReason.UPI_FAILURE.value, execute=True)]),
        CustomerSpec("Vikram Singh", "vikram.singh@example.test", "+919800000005", "high",
                     12, 2, 0.69, 9800, False,
                     [TxnSpec(9800, "card", FailureReason.NETWORK_ERROR.value, execute=True)]),
        # --- MEDIUM profile ---
        CustomerSpec("Sanya Gupta", "sanya.gupta@example.test", "+919800000006", "medium",
                     6, 4, 0.48, 5400, False,
                     [TxnSpec(6200, "card", FailureReason.INSUFFICIENT_FUNDS.value, execute=True),
                      TxnSpec(3100, "wallet", FailureReason.PAYMENT_TIMEOUT.value)]),
        CustomerSpec("Rohan Das", "rohan.das@example.test", "+919800000007", "medium",
                     5, 3, 0.44, 4700, False,
                     [TxnSpec(2400, "upi", FailureReason.USER_ABANDONMENT.value,
                              RevenueLossType.CHECKOUT_ABANDONMENT.value, execute=True)]),
        CustomerSpec("Meera Iyer", "meera.iyer@example.test", "+919800000008", "medium",
                     8, 5, 0.52, 6100, False,
                     [TxnSpec(14500, "card", FailureReason.CARD_EXPIRED.value, execute=True),
                      TxnSpec(7300, "emi", FailureReason.BANK_DECLINE.value,
                              RevenueLossType.SUBSCRIPTION_FAILURE.value, execute=True)]),
        CustomerSpec("Karan Malhotra", "karan.malhotra@example.test", "+919800000009", "medium",
                     7, 4, 0.50, 8900, False,
                     [TxnSpec(18000, "netbanking", FailureReason.PAYMENT_TIMEOUT.value,
                              RevenueLossType.OVERDUE_INVOICE.value)]),
        CustomerSpec("Ananya Reddy", "ananya.reddy@example.test", "+919800000010", "medium",
                     6, 3, 0.46, 5200, False,
                     [TxnSpec(4300, "upi", FailureReason.UPI_FAILURE.value, execute=True)]),
        # --- LOW profile (repeated failures, low value; DO_NOTHING candidates) ---
        CustomerSpec("Deepak Verma", "deepak.verma@example.test", None, "low",
                     2, 7, 0.14, 900, False,
                     [TxnSpec(500, "wallet", FailureReason.USER_ABANDONMENT.value,
                              RevenueLossType.CHECKOUT_ABANDONMENT.value, execute=True),
                      TxnSpec(750, "upi", FailureReason.INSUFFICIENT_FUNDS.value, execute=True)]),
        CustomerSpec("Pooja Bhatia", "pooja.bhatia@example.test", None, "low",
                     1, 6, 0.10, 1200, True,
                     [TxnSpec(1100, "card", FailureReason.CARD_EXPIRED.value, execute=True)]),
        CustomerSpec("Suresh Kumar", "suresh.kumar@example.test", None, "low",
                     3, 8, 0.18, 1500, False,
                     [TxnSpec(1800, "upi", FailureReason.USER_ABANDONMENT.value,
                              RevenueLossType.CHECKOUT_ABANDONMENT.value, execute=True),
                      TxnSpec(650, "wallet", FailureReason.NETWORK_ERROR.value, execute=True)]),
        CustomerSpec("Farah Khan", "farah.khan@example.test", "+919800000014", "low",
                     2, 5, 0.16, 2100, False,
                     [TxnSpec(2600, "card", FailureReason.BANK_DECLINE.value, execute=True),
                      TxnSpec(900, "upi", FailureReason.UPI_FAILURE.value)]),
        # Written-off: terrible history + abandonment -> AI deliberately DOES NOTHING.
        CustomerSpec("Imran Sheikh", "imran.sheikh@example.test", None, "low",
                     0, 9, 0.05, 1400, False,
                     [TxnSpec(1500, "upi", FailureReason.USER_ABANDONMENT.value,
                              RevenueLossType.CHECKOUT_ABANDONMENT.value, execute=True),
                      TxnSpec(2200, "card", FailureReason.CARD_EXPIRED.value, execute=True)]),
    ]


def seed(db: Session, *, clear: bool = True, run_pipeline: bool = True) -> dict:
    if clear:
        _clear(db)

    rng = random.Random(2025)
    customers_created = 0
    txns_created = 0
    cases_created = 0
    seed_use_llm = settings.llm_configured

    for spec in _specs():
        cust = Customer(
            name=spec.name, email=spec.email, phone=spec.phone, customer_value=spec.value,
            total_transactions=spec.successful + spec.failed,
            successful_transactions=spec.successful, failed_transactions=spec.failed,
            historical_recovery_rate=spec.hist_rate, average_payment_amount=spec.avg_amount,
            opted_out=spec.opted_out,
        )
        db.add(cust)
        db.flush()
        customers_created += 1

        for tspec in spec.txns:
            txn = Transaction(
                customer_id=cust.id, amount=tspec.amount, currency="INR",
                payment_method=tspec.method, status="FAILED", failure_reason=tspec.reason,
                loss_type=tspec.loss_type, is_synthetic=True,
                razorpay_order_id=f"order_SEED{rng.randint(10**7, 10**8):08d}",
            )
            db.add(txn)
            db.flush()
            db.add(PaymentAttempt(transaction_id=txn.id, attempt_number=1, status="FAILED",
                                  failure_reason=tspec.reason))
            txns_created += 1

            if run_pipeline:
                recovery_service.process_failed_transaction(
                    db, txn, execute=tspec.execute, simulate=True, use_llm=seed_use_llm,
                    require_llm=seed_use_llm)
                cases_created += 1

    if run_pipeline:
        pair = _seed_contrast_pair(db, use_llm=seed_use_llm)
        customers_created += pair["customers"]
        txns_created += pair["transactions"]
        cases_created += pair["cases"]
        _seed_recovery_memory(db)

    db.commit()
    logger.info("Seeded %d customers, %d transactions, %d cases.",
                customers_created, txns_created, cases_created)
    return {"customers": customers_created, "transactions": txns_created, "cases": cases_created}


def _seed_contrast_pair(db: Session, *, use_llm: bool = False) -> dict:
    """Two customers, identical ₹12,500 bank-decline failure, opposite AI decisions —
    the proof that context (not the failure) drives the decision."""
    from ..models.recovery_action import RecoveryAction

    # Customer A — reliable, high engagement -> RETRY (high recovery probability).
    a = Customer(name="Aarav Menon", email="aarav.menon@example.test", phone="+919800001001",
                 customer_value="high", total_transactions=16, successful_transactions=14,
                 failed_transactions=2, historical_recovery_rate=0.80, average_payment_amount=11900,
                 opted_out=False)
    db.add(a); db.flush()
    ta = Transaction(customer_id=a.id, amount=12500, currency="INR", payment_method="card",
                     status="FAILED", failure_reason=FailureReason.BANK_DECLINE.value,
                     loss_type="PAYMENT_FAILURE", is_synthetic=True,
                     razorpay_order_id="order_SEED_A0012500")
    db.add(ta); db.flush()
    db.add(PaymentAttempt(transaction_id=ta.id, attempt_number=1, status="FAILED",
                          failure_reason=FailureReason.BANK_DECLINE.value))
    recovery_service.process_failed_transaction(
        db, ta, execute=False, use_llm=use_llm, require_llm=use_llm
    )

    # Customer B — repeated failures, low engagement, 2 prior recovery attempts -> DO_NOTHING.
    b = Customer(name="Rehan Ali", email="rehan.ali@example.test", phone=None,
                 customer_value="low", total_transactions=17, successful_transactions=2,
                 failed_transactions=15, historical_recovery_rate=0.05, average_payment_amount=2100,
                 opted_out=False)
    db.add(b); db.flush()
    tb = Transaction(customer_id=b.id, amount=12500, currency="INR", payment_method="card",
                     status="FAILED", failure_reason=FailureReason.BANK_DECLINE.value,
                     loss_type="PAYMENT_FAILURE", is_synthetic=True,
                     razorpay_order_id="order_SEED_B0012500")
    db.add(tb); db.flush()
    db.add(PaymentAttempt(transaction_id=tb.id, attempt_number=1, status="FAILED",
                          failure_reason=FailureReason.BANK_DECLINE.value))
    case_b, _ = recovery_service.get_or_create_case(db, tb)
    # Two prior recovery attempts already made (drives the probability down).
    for n in (1, 2):
        db.add(RecoveryAction(recovery_case_id=case_b.id,
                              action_type=RecoveryActionType.RETRY_PAYMENT.value,
                              channel="PAYMENT_RETRY", status="SIMULATED",
                              execution_mode="SIMULATED", attempt_number=n,
                              result="Prior recovery attempt (no conversion).",
                              executed_at=None))
    db.flush()
    recovery_service.analyze_case(db, case_b, use_llm=use_llm, require_llm=use_llm)
    db.flush()
    return {"customers": 2, "transactions": 2, "cases": 2}


# Historical intervention performance (outcome-based recovery intelligence) —
# clearly labelled demo history that seeds the Recovery Memory table + EV comparison.
_MEMORY_SEED = [
    ("PAYMENT_FAILURE", "UPI_FAILURE", "PAYMENT_LINK", 25, 18),
    ("PAYMENT_FAILURE", "BANK_DECLINE", "RETRY_PAYMENT", 40, 27),
    ("PAYMENT_FAILURE", "BANK_DECLINE", "ALTERNATE_PAYMENT_METHOD", 22, 14),
    ("PAYMENT_FAILURE", "CARD_EXPIRED", "ALTERNATE_PAYMENT_METHOD", 18, 11),
    ("PAYMENT_FAILURE", "PAYMENT_TIMEOUT", "RETRY_PAYMENT", 20, 15),
    ("PAYMENT_FAILURE", "INSUFFICIENT_FUNDS", "SCHEDULE_RETRY", 16, 9),
    ("CHECKOUT_ABANDONMENT", "USER_ABANDONMENT", "PAYMENT_LINK", 30, 17),
    ("CHECKOUT_ABANDONMENT", "USER_ABANDONMENT", "EMAIL", 28, 11),
]


def _seed_recovery_memory(db: Session) -> None:
    from ..services import memory_service

    for loss, cause, action, attempts, successes in _MEMORY_SEED:
        row = memory_service.get_stat(db, loss, cause, action)
        avg = 8500.0
        if row is None:
            row = RecoveryMemory(loss_type=loss, root_cause=cause, action_type=action,
                                 attempts=attempts, successes=successes,
                                 recovered_amount=successes * avg)
            db.add(row)
        else:
            row.attempts = (row.attempts or 0) + attempts
            row.successes = (row.successes or 0) + successes
            row.recovered_amount = (row.recovered_amount or 0.0) + successes * avg
    db.flush()


def _clear(db: Session) -> None:
    for model in (AuditLog, RecoveryEvent, RecoveryAction, RecoveryDecision, RecoveryCase,
                  PaymentAttempt, RecoveryMemory, Transaction, Customer):
        db.execute(delete(model))
    db.commit()
