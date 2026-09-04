"""Recovery orchestration — the core product loop.

DETECT -> DIAGNOSE -> DECIDE -> VALIDATE (guardrails) -> EXECUTE -> MEASURE -> LEARN

Every stage writes audit + timeline records. The AI's recommendation is always
routed through the guardrail engine before any channel side effect occurs.
"""
from __future__ import annotations

import json
import random
from typing import Optional, Tuple

from sqlalchemy.orm import Session

from ..agents import analyze_root_cause, decide
from ..integrations import channels, razorpay_client
from ..logging_config import get_logger
from ..ml import get_model
from ..ml.model import human_readable_signals
from ..models.customer import Customer
from ..models.enums import (
    CaseStatus,
    ExecutionMode,
    Priority,
    RecoveryActionType,
    RecoveryChannel,
    RiskLevel,
    TransactionStatus,
)
from ..models.recovery_action import RecoveryAction
from ..models.recovery_case import RecoveryCase
from ..models.recovery_decision import RecoveryDecision
from ..models.transaction import Transaction
from ..policies import GuardrailContext, evaluate
from . import audit_service, customer_service, memory_service

logger = get_logger(__name__)

_PRIORITY_BY_RISK = {
    RiskLevel.CRITICAL.value: Priority.URGENT.value,
    RiskLevel.HIGH.value: Priority.HIGH.value,
    RiskLevel.MEDIUM.value: Priority.MEDIUM.value,
    RiskLevel.LOW.value: Priority.LOW.value,
}


# --------------------------------------------------------------------------- #
# DETECT
# --------------------------------------------------------------------------- #
def get_or_create_case(db: Session, txn: Transaction) -> Tuple[RecoveryCase, bool]:
    """Idempotent: one recovery case per transaction."""
    if txn.recovery_case is not None:
        return txn.recovery_case, False

    rc = analyze_root_cause(txn.failure_reason, txn.loss_type)
    case = RecoveryCase(
        transaction_id=txn.id,
        loss_type=txn.loss_type,
        status=CaseStatus.OPEN.value,
        root_cause=rc.code.value,
        root_cause_detail=rc.detail,
    )
    db.add(case)
    txn.recovery_case = case  # keep the reverse relationship populated in-memory
    db.flush()
    audit_service.add_event(db, case.id, "Payment Failed",
                            detail=f"{txn.currency} {txn.amount:,.0f} — {rc.summary}", icon="alert")
    audit_service.add_event(db, case.id, "Risk Detected", actor="Risk Agent", icon="shield")
    audit_service.log(db, event="Payment Failed", actor="Webhook", action="Received",
                      result=rc.code.value, recovery_case_id=case.id,
                      input_data={"amount": txn.amount, "failure_reason": txn.failure_reason})
    return case, True


# --------------------------------------------------------------------------- #
# DIAGNOSE + DECIDE
# --------------------------------------------------------------------------- #
def analyze_case(db: Session, case: RecoveryCase, *, use_llm: bool = True,
                 require_llm: bool = False) -> RecoveryCase:
    txn = case.transaction
    customer = txn.customer
    case.status = CaseStatus.ANALYZING.value

    payload = customer_service.build_decision_input(db, customer, txn, case)
    model = get_model()
    explanation = model.explain(payload)
    ml_signals = human_readable_signals(payload, explanation)

    decision = decide(payload, ml_signals, use_llm=use_llm, require_llm=require_llm)
    expected_value = round(txn.amount * decision.recovery_probability, 2)

    rationale = {
        "signals": decision.signals,
        "top_positive": explanation.top_positive,
        "top_negative": explanation.top_negative,
        "model_version": model.version,
        "decided_by": decision.decided_by,
        "fallback_reason": decision.fallback_reason,
    }
    rec = RecoveryDecision(
        recovery_case_id=case.id,
        decision=decision.recommended_action.value,
        channel=decision.channel.value,
        risk_level=decision.risk_level.value,
        recovery_probability=decision.recovery_probability,
        expected_recovery_value=expected_value,
        confidence=decision.confidence,
        delay_minutes=decision.delay_minutes,
        max_attempts=decision.max_attempts,
        reason=decision.reason,
        root_cause=decision.root_cause_code.value,
        decided_by=decision.decided_by,
        model_version=model.version,
        rationale_signals=json.dumps(rationale, default=str),
    )
    db.add(rec)

    case.risk_level = decision.risk_level.value
    case.recovery_probability = decision.recovery_probability
    case.expected_recovery_value = expected_value
    case.root_cause = decision.root_cause_code.value
    case.recommended_action = decision.recommended_action.value
    case.recommended_channel = decision.channel.value
    case.priority = _PRIORITY_BY_RISK.get(decision.risk_level.value, Priority.MEDIUM.value)
    case.status = CaseStatus.RECOMMENDED.value

    audit_service.add_event(db, case.id, f"Recovery Probability = {decision.recovery_probability*100:.0f}%",
                            actor="Recovery Model", icon="gauge")
    audit_service.add_event(db, case.id, f"AI Recommendation = {decision.recommended_action.value}",
                            detail=decision.reason, actor="Recovery Agent", icon="brain")
    audit_service.log(db, event="Decision", actor=decision.decided_by,
                      action=decision.recommended_action.value, result=decision.risk_level.value,
                      reason=decision.reason, recovery_case_id=case.id,
                      input_data=payload.model_dump(mode="json"),
                      decision_data=decision.model_dump(mode="json"))
    if decision.decided_by == "heuristic_fallback" and decision.fallback_reason:
        audit_service.log(db, event="LLM Fallback", actor="Recovery Agent",
                          result=decision.fallback_reason,
                          reason="LLM unavailable after one retry; used deterministic heuristic.",
                          recovery_case_id=case.id)
    db.flush()
    return case


# --------------------------------------------------------------------------- #
# VALIDATE (guardrails) + EXECUTE + MEASURE
# --------------------------------------------------------------------------- #
def execute_case(db: Session, case: RecoveryCase, *, simulate: bool = True, force: bool = False,
                 use_llm: bool = True) -> dict:
    txn = case.transaction
    customer = txn.customer

    if case.is_terminal and not force:
        return {"status": "skipped", "reason": f"Case already {case.status}."}

    if not case.recommended_action:
        analyze_case(db, case)

    action = _coerce_action(case.recommended_action)
    retries_used, messages_used = customer_service.action_counts(db, case.id)
    hours = customer_service.minutes_since(txn.created_at) / 60.0

    ctx = GuardrailContext(
        payment_already_succeeded=txn.status == TransactionStatus.CAPTURED.value,
        case_terminal=case.is_terminal,
        retries_used=retries_used,
        messages_used=messages_used,
        customer_opted_out=customer.opted_out,
        hours_since_failure=hours,
        recovery_probability=case.recovery_probability,
        customer_email_present=bool(customer.email),
    )
    verdict = evaluate(action, ctx)

    result_label = "APPROVED" if verdict.allowed else (
        "DOWNGRADED" if verdict.override_action else "BLOCKED")
    audit_service.log(db, event="Guardrail", actor="Policy Engine", action=action.value,
                      result=result_label, reason=verdict.reason, recovery_case_id=case.id,
                      decision_data={"rule": verdict.rule, "checks": verdict.checks})
    audit_service.add_event(db, case.id,
                            f"Guardrails = {'PASSED' if verdict.allowed else result_label}",
                            detail=verdict.reason, actor="Policy Engine", icon="shield")

    # Fully blocked (no override) -> record a blocked action and stop.
    if verdict.effective_action_blocked:
        db.add(RecoveryAction(
            recovery_case_id=case.id, action_type=action.value,
            channel=(case.recommended_channel or RecoveryChannel.NONE.value),
            status="BLOCKED", execution_mode=ExecutionMode.SIMULATED.value,
            attempt_number=retries_used + 1, result=verdict.reason,
        ))
        case.status = CaseStatus.CLOSED.value
        db.flush()
        return {"status": "blocked", "rule": verdict.rule, "reason": verdict.reason}

    # Apply a downgrade (e.g. below-threshold -> DO_NOTHING, retries exhausted -> link).
    if verdict.override_action is not None:
        action = verdict.override_action
        case.recommended_action = action.value

    # DO_NOTHING: deliberate stand-down, no channel side effect.
    if action == RecoveryActionType.DO_NOTHING:
        db.add(RecoveryAction(
            recovery_case_id=case.id, action_type=action.value,
            channel=RecoveryChannel.NONE.value, status="EXECUTED",
            execution_mode=ExecutionMode.SIMULATED.value, attempt_number=1,
            result="Deliberate stand-down — expected value below intervention cost.",
            executed_at=audit_service.now_iso(),
        ))
        case.status = CaseStatus.DO_NOTHING.value
        audit_service.add_event(db, case.id, "Decision = DO NOTHING",
                                detail="Expected recovery value too low to justify action.",
                                actor="Recovery Engine", icon="pause")
        audit_service.log(db, event="Execution", actor="Recovery Engine",
                          action=action.value, result="DO_NOTHING", recovery_case_id=case.id)
        db.flush()
        return {"status": "do_nothing", "action": action.value}

    # EXECUTE the approved action.
    channel = _coerce_channel(case.recommended_channel)
    exec_ctx = channels.ExecutionContext(
        customer_name=customer.name, amount=txn.amount, currency=txn.currency,
        customer_email=customer.email, customer_phone=customer.phone,
        description=f"Complete your {txn.currency} {txn.amount:,.0f} payment",
    )
    # Interactive EMAIL -> send a REAL email via Resend (with a real test payment link).
    if action == RecoveryActionType.EMAIL and use_llm:
        outcome = _execute_real_email(db, case, customer, txn, exec_ctx)
    else:
        outcome = channels.execute(action, channel, exec_ctx, use_llm=use_llm, live=use_llm)

    act = RecoveryAction(
        recovery_case_id=case.id, action_type=outcome.action_type, channel=outcome.channel,
        status=outcome.status, execution_mode=outcome.execution_mode,
        attempt_number=retries_used + 1, result=outcome.detail,
        external_reference=outcome.external_reference, executed_at=audit_service.now_iso(),
    )
    db.add(act)
    case.status = CaseStatus.IN_RECOVERY.value
    audit_service.add_event(db, case.id, f"{action.value} Executed", detail=outcome.detail,
                            actor="Recovery Engine", icon="send")
    audit_service.log(db, event="Execution", actor="Recovery Engine", action=action.value,
                      result=outcome.status, reason=outcome.detail, recovery_case_id=case.id,
                      decision_data={"execution_mode": outcome.execution_mode,
                                     "external_reference": outcome.external_reference})

    real_test_event = outcome.execution_mode == ExecutionMode.REAL_RAZORPAY_TEST.value
    if real_test_event and outcome.external_reference:
        audit_service.add_event(
            db, case.id, "Real Razorpay TEST artifact created",
            detail=f"{outcome.external_reference} (awaiting customer payment / webhook)",
            actor="Razorpay", icon="link")

    result: dict = {
        "status": "executed", "action": action.value, "channel": outcome.channel,
        "execution_mode": outcome.execution_mode, "external_reference": outcome.external_reference,
        "detail": outcome.detail, "message_body": outcome.message_body,
    }

    # MEASURE. Communication channels (email/whatsapp/human) NEVER auto-recover —
    # a sent email is not a payment. Recovery for those comes only from a real
    # Razorpay capture webhook, so they stay PENDING. Payment-instrument actions
    # (retry/link/alternate) sample a simulated capture for the demo.
    _COMMS = {RecoveryActionType.EMAIL, RecoveryActionType.WHATSAPP,
              RecoveryActionType.HUMAN_ESCALATION}
    if action in _COMMS:
        result["outcome"] = "PENDING"
        audit_service.add_event(db, case.id, "Awaiting payment (email sent ≠ recovered)",
                                detail="Recovery is confirmed only by a Razorpay capture webhook.",
                                actor="Recovery Engine", icon="flag")
    elif simulate:
        recovered = _sample_outcome(case.id, case.recovery_probability, act.attempt_number)
        if recovered:
            _finalize_recovered(db, case, txn, txn.amount, action, real=False)
            result["outcome"] = "RECOVERED"
        else:
            _finalize_failed(db, case, txn, action)
            result["outcome"] = "NOT_RECOVERED"
    else:
        result["outcome"] = "PENDING"

    db.flush()
    return result


def _execute_real_email(db, case, customer, txn, exec_ctx) -> "channels.ChannelOutcome":
    """Generate a real Razorpay test payment link + personalized content, then send
    a REAL email via Resend. Returns a ChannelOutcome reflecting the send result."""
    from . import email_service

    # 1. Real Razorpay TEST payment link to embed (if Razorpay configured).
    payment_link = None
    if razorpay_client.is_configured():
        try:
            link = razorpay_client.create_payment_link(
                txn.amount, customer.name, customer.email, customer.phone,
                exec_ctx.description, txn.currency)
            payment_link = link.get("short_url") or link.get("id")
            audit_service.add_event(db, case.id, "Razorpay TEST payment link created",
                                    detail=str(payment_link), actor="Razorpay", icon="link")
        except razorpay_client.RazorpayError as exc:
            logger.warning("Payment link for email failed: %s", exc)

    # 2. Personalized, factual content (LLM if configured, else safe template).
    msg = channels.generate_message(
        exec_ctx, RecoveryChannel.EMAIL.value, RecoveryActionType.EMAIL.value,
        payment_link, use_llm=True)

    # 3. Send the REAL email (records status + audits internally).
    rec = email_service.send_recovery_email(
        db, recovery_case_id=case.id, customer_id=customer.id, to_email=customer.email,
        customer_name=customer.name, amount=txn.amount, currency=txn.currency,
        subject=msg["subject"], body=msg["body"], payment_link=payment_link)

    status_map = {"SENT": "EXECUTED", "FAILED": "FAILED", "BLOCKED": "BLOCKED", "PENDING": "PENDING"}
    mode = ExecutionMode.REAL_RESEND_EMAIL.value if rec.status == "SENT" else ExecutionMode.SIMULATED.value
    detail = {
        "SENT": f"Real email sent via Resend to {email_service.mask_email(customer.email)} "
                f"(id {rec.provider_message_id}).",
        "FAILED": f"Email FAILED: {rec.failure_reason}",
        "BLOCKED": f"Email blocked: {rec.failure_reason}",
    }.get(rec.status, "Email queued.")
    return channels.ChannelOutcome(
        action_type=RecoveryActionType.EMAIL.value, channel=RecoveryChannel.EMAIL.value,
        status=status_map.get(rec.status, "SIMULATED"), execution_mode=mode, detail=detail,
        external_reference=payment_link or rec.provider_message_id,
        message_subject=rec.subject, message_body=msg["body"])


# --------------------------------------------------------------------------- #
# MEASURE helpers + webhook capture
# --------------------------------------------------------------------------- #
def _sample_outcome(case_id: int, probability: float, attempt: int) -> bool:
    rng = random.Random(case_id * 1000 + attempt)
    return rng.random() < probability


def _finalize_recovered(db, case, txn, amount, action, *, real: bool) -> None:
    case.status = CaseStatus.RECOVERED.value
    case.recovered_amount = amount
    txn.status = TransactionStatus.CAPTURED.value
    label = "Payment Successful" if real else "Payment Successful (SIMULATED capture — demo)"
    audit_service.add_event(db, case.id, label, detail=f"Recovered {txn.currency} {amount:,.0f}",
                            actor="Razorpay" if real else "Recovery Engine", icon="check")
    audit_service.log(db, event="Recovery Outcome",
                      actor="Razorpay" if real else "Recovery Engine",
                      action=str(action), result="RECOVERED", recovery_case_id=case.id,
                      decision_data={"amount": amount, "real": real})
    memory_service.record_outcome(db, loss_type=case.loss_type,
                                  root_cause=case.root_cause or "UNKNOWN",
                                  action_type=str(action), success=True, amount=amount)
    _bump_customer_success(db, txn.customer)


def _finalize_failed(db, case, txn, action) -> None:
    case.status = CaseStatus.FAILED.value
    audit_service.add_event(db, case.id, "Recovery attempt did not convert (SIMULATED)",
                            actor="Recovery Engine", icon="x")
    memory_service.record_outcome(db, loss_type=case.loss_type,
                                  root_cause=case.root_cause or "UNKNOWN",
                                  action_type=str(action), success=False, amount=0.0)


def _bump_customer_success(db, customer: Customer) -> None:
    customer.successful_transactions += 1
    total = customer.total_transactions or (customer.successful_transactions + customer.failed_transactions)
    if total > 0:
        customer.historical_recovery_rate = round(
            min(1.0, (customer.historical_recovery_rate * max(1, total - 1) + 1.0) / total), 4
        )


def mark_recovered_by_webhook(db: Session, txn: Transaction, payment_id: Optional[str]) -> Optional[RecoveryCase]:
    """Called when a real Razorpay capture webhook arrives for a tracked txn."""
    case = txn.recovery_case
    if payment_id:
        txn.razorpay_payment_id = payment_id
    if case is None:
        txn.status = TransactionStatus.CAPTURED.value
        db.flush()
        return None
    if case.status == CaseStatus.RECOVERED.value:
        return case  # idempotent
    action = case.recommended_action or RecoveryActionType.RETRY_PAYMENT.value
    _finalize_recovered(db, case, txn, txn.amount, action, real=True)
    audit_service.add_event(db, case.id, "Active recovery workflow stopped", icon="flag")
    db.flush()
    return case


# --------------------------------------------------------------------------- #
def process_failed_transaction(db: Session, txn: Transaction, *, execute: bool = False,
                               simulate: bool = True, use_llm: bool = True,
                               require_llm: bool = False) -> RecoveryCase:
    """Full intake: detect -> diagnose -> decide (and optionally validate+execute)."""
    case, _created = get_or_create_case(db, txn)
    analyze_case(db, case, use_llm=use_llm, require_llm=require_llm)
    if execute:
        execute_case(db, case, simulate=simulate, use_llm=use_llm)
    return case


def _coerce_action(value: Optional[str]) -> RecoveryActionType:
    try:
        return RecoveryActionType(value)
    except (ValueError, TypeError):
        return RecoveryActionType.DO_NOTHING


def _coerce_channel(value: Optional[str]) -> RecoveryChannel:
    try:
        return RecoveryChannel(value)
    except (ValueError, TypeError):
        return RecoveryChannel.NONE
