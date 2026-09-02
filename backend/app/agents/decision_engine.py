"""AI recovery decision engine.

Produces a validated `AIDecision`. When an LLM is configured it is consulted for
the recommendation; its raw output is parsed and validated against the strict
schema, and ANY failure (timeout, bad JSON, schema violation) falls back to the
deterministic heuristic. When no LLM key is present the heuristic is the engine.

The ML recovery_probability is always authoritative for the number shown — the
LLM may reason about it but cannot override the calibrated estimate.
"""
from __future__ import annotations

from typing import List, Optional

from ..config import settings
from ..logging_config import get_logger
from ..models.enums import (
    FailureReason,
    RecoveryActionType,
    RecoveryChannel,
    RevenueLossType,
    RiskLevel,
)
from ..schemas.decision import AIDecision, AIDecisionInput
from . import llm_client, prompts
from .root_cause import analyze as analyze_root_cause

logger = get_logger(__name__)

_TRANSIENT = {
    FailureReason.BANK_DECLINE,
    FailureReason.PAYMENT_TIMEOUT,
    FailureReason.NETWORK_ERROR,
}

_CHANNEL_FOR_ACTION = {
    RecoveryActionType.RETRY_PAYMENT: RecoveryChannel.PAYMENT_RETRY,
    RecoveryActionType.SCHEDULE_RETRY: RecoveryChannel.PAYMENT_RETRY,
    RecoveryActionType.PAYMENT_LINK: RecoveryChannel.PAYMENT_LINK,
    RecoveryActionType.ALTERNATE_PAYMENT_METHOD: RecoveryChannel.PAYMENT_LINK,
    RecoveryActionType.EMAIL: RecoveryChannel.EMAIL,
    RecoveryActionType.WHATSAPP: RecoveryChannel.WHATSAPP,
    RecoveryActionType.HUMAN_ESCALATION: RecoveryChannel.HUMAN,
    RecoveryActionType.DO_NOTHING: RecoveryChannel.NONE,
}

_TIMING = {  # action -> (delay_minutes, max_attempts)
    RecoveryActionType.RETRY_PAYMENT: (15, 2),
    RecoveryActionType.SCHEDULE_RETRY: (720, 2),
    RecoveryActionType.PAYMENT_LINK: (5, 1),
    RecoveryActionType.ALTERNATE_PAYMENT_METHOD: (10, 1),
    RecoveryActionType.EMAIL: (30, 1),
    RecoveryActionType.WHATSAPP: (30, 1),
    RecoveryActionType.HUMAN_ESCALATION: (0, 1),
    RecoveryActionType.DO_NOTHING: (0, 1),
}

_MESSAGING_ACTIONS = {
    RecoveryActionType.EMAIL,
    RecoveryActionType.WHATSAPP,
}


def decide(payload: AIDecisionInput, ml_signals: Optional[List[str]] = None,
           use_llm: bool = True) -> AIDecision:
    ml_signals = ml_signals or []
    # Always compute a valid heuristic baseline first (the safety net).
    base = _heuristic(payload, ml_signals, decided_by="heuristic")
    if use_llm and settings.llm_configured:
        merged, reason = _apply_llm_with_retry(base, payload, ml_signals)
        if merged is not None:
            return merged
        # Retried once and still failed → deterministic fallback, reason recorded.
        base.decided_by = "heuristic_fallback"
        base.fallback_reason = reason
        logger.warning("LLM decision fell back to heuristic after retry [%s].", reason)
    return base


def _apply_llm_with_retry(base: AIDecision, payload: AIDecisionInput,
                          ml_signals: List[str]) -> tuple[Optional[AIDecision], Optional[str]]:
    """Try the LLM, retry once on failure, then give up. Returns (decision, reason)."""
    reason: Optional[str] = None
    for attempt in (1, 2):
        merged, reason = _apply_llm(base, payload, ml_signals)
        if merged is not None:
            return merged, None
        logger.info("LLM decision attempt %d/2 failed [%s].", attempt, reason)
    return None, reason


# --------------------------------------------------------------------------- #
# Deterministic heuristic
# --------------------------------------------------------------------------- #
def _heuristic(
    payload: AIDecisionInput, ml_signals: List[str], decided_by: str
) -> AIDecision:
    prob = payload.model_recovery_probability
    rc = analyze_root_cause(payload.failure_reason.value, payload.loss_type.value)
    action = _select_action(payload, rc.code)
    channel = _CHANNEL_FOR_ACTION[action]
    delay, max_attempts = _TIMING[action]
    risk = _risk_level(payload.transaction_amount, prob)
    confidence = _confidence(prob, payload.failure_reason)
    reason = _reason_text(action, rc.summary, prob, payload)
    signals = _merge_signals(ml_signals, [_rule_signal(action, payload, rc.code)])

    return AIDecision(
        risk_level=risk,
        recovery_probability=prob,
        root_cause_code=rc.code,
        root_cause=rc.summary,
        recommended_action=action,
        channel=channel,
        delay_minutes=delay,
        max_attempts=max_attempts,
        confidence=confidence,
        reason=reason,
        signals=signals,
        decided_by=decided_by,
    )


def _select_action(p: AIDecisionInput, reason: FailureReason) -> RecoveryActionType:
    prob = p.model_recovery_probability
    amount = p.transaction_amount
    attempts = p.previous_recovery_attempts
    loss = p.loss_type

    # 1. Not worth it -> DO_NOTHING (a real, deliberate decision).
    if prob < settings.min_recovery_probability:
        return RecoveryActionType.DO_NOTHING
    if amount < 500 and prob < 0.35 and attempts >= 1:
        return RecoveryActionType.DO_NOTHING

    # 2. Memory-informed preference (only if it doesn't violate hard constraints).
    mem = _memory_action(p, reason)
    if mem is not None:
        return _apply_high_value_override(mem, amount, prob)

    # 3. Loss-type specific routing.
    if loss == RevenueLossType.CHECKOUT_ABANDONMENT:
        base = RecoveryActionType.PAYMENT_LINK if prob >= 0.45 else RecoveryActionType.EMAIL
        return _apply_high_value_override(base, amount, prob)
    if loss == RevenueLossType.OVERDUE_INVOICE:
        base = RecoveryActionType.EMAIL if amount < 20000 else RecoveryActionType.HUMAN_ESCALATION
        return base
    if loss == RevenueLossType.SUBSCRIPTION_FAILURE:
        if reason in _TRANSIENT and attempts < settings.max_payment_retries and prob >= 0.4:
            return RecoveryActionType.RETRY_PAYMENT
        return RecoveryActionType.PAYMENT_LINK

    # 4. Payment failure by root cause.
    base = _action_for_reason(reason, p)
    return _apply_high_value_override(base, amount, prob)


def _action_for_reason(reason: FailureReason, p: AIDecisionInput) -> RecoveryActionType:
    prob = p.model_recovery_probability
    attempts = p.previous_recovery_attempts

    if reason in _TRANSIENT:
        if attempts < settings.max_payment_retries and prob >= 0.4:
            return RecoveryActionType.RETRY_PAYMENT
        return RecoveryActionType.PAYMENT_LINK
    if reason == FailureReason.INSUFFICIENT_FUNDS:
        if attempts < settings.max_payment_retries:
            return RecoveryActionType.SCHEDULE_RETRY
        return RecoveryActionType.PAYMENT_LINK
    if reason == FailureReason.UPI_FAILURE:
        return RecoveryActionType.PAYMENT_LINK
    if reason == FailureReason.CARD_EXPIRED:
        return RecoveryActionType.ALTERNATE_PAYMENT_METHOD
    if reason == FailureReason.USER_ABANDONMENT:
        return RecoveryActionType.PAYMENT_LINK
    # UNKNOWN
    if prob >= 0.5 and attempts < settings.max_payment_retries:
        return RecoveryActionType.RETRY_PAYMENT
    return RecoveryActionType.EMAIL


def _apply_high_value_override(
    base: RecoveryActionType, amount: float, prob: float
) -> RecoveryActionType:
    # White-glove for large, likely-recoverable amounts.
    if amount >= 30000 and prob >= 0.8 and base in {
        RecoveryActionType.RETRY_PAYMENT,
        RecoveryActionType.PAYMENT_LINK,
    }:
        return RecoveryActionType.ALTERNATE_PAYMENT_METHOD
    # Escalate large, uncertain amounts to a human.
    if amount >= 50000 and 0.35 <= prob < 0.7:
        return RecoveryActionType.HUMAN_ESCALATION
    return base


def _memory_action(p: AIDecisionInput, reason: FailureReason) -> Optional[RecoveryActionType]:
    if not p.memory_best_action or p.memory_best_action_rate is None:
        return None
    if p.memory_best_action_rate < 0.55:
        return None
    try:
        action = RecoveryActionType(p.memory_best_action)
    except ValueError:
        return None
    # Hard constraint: never retry an expired card even if memory "liked" it.
    if reason == FailureReason.CARD_EXPIRED and action in {
        RecoveryActionType.RETRY_PAYMENT,
        RecoveryActionType.SCHEDULE_RETRY,
    }:
        return None
    return action


def _risk_level(amount: float, prob: float) -> RiskLevel:
    # Severity reflects how much revenue is at stake for this event. A large
    # amount that is also unlikely to recover is escalated one tier.
    if amount >= 25000:
        base = RiskLevel.CRITICAL
    elif amount >= 10000:
        base = RiskLevel.HIGH
    elif amount >= 3000:
        base = RiskLevel.MEDIUM
    else:
        base = RiskLevel.LOW
    if prob < 0.3 and amount >= 5000 and base != RiskLevel.CRITICAL:
        order = [RiskLevel.LOW, RiskLevel.MEDIUM, RiskLevel.HIGH, RiskLevel.CRITICAL]
        base = order[min(order.index(base) + 1, len(order) - 1)]
    return base


def _confidence(prob: float, reason: FailureReason) -> float:
    base = 0.55 + 0.4 * abs(prob - 0.5) * 2
    if reason != FailureReason.UNKNOWN:
        base += 0.05
    return round(min(0.98, base), 3)


def _reason_text(action, root_cause_summary, prob, p: AIDecisionInput) -> str:
    pct = f"{prob*100:.0f}%"
    if action == RecoveryActionType.DO_NOTHING:
        return (
            f"Expected recovery value is too low (probability {pct} on "
            f"{p.currency} {p.transaction_amount:,.0f}) to justify further "
            f"intervention cost. Standing down is the value-maximising choice."
        )
    verbs = {
        RecoveryActionType.RETRY_PAYMENT: "Retry the payment",
        RecoveryActionType.SCHEDULE_RETRY: "Schedule a later retry",
        RecoveryActionType.PAYMENT_LINK: "Send a secure payment link",
        RecoveryActionType.ALTERNATE_PAYMENT_METHOD: "Offer an alternate payment method",
        RecoveryActionType.EMAIL: "Send a personalized email nudge",
        RecoveryActionType.WHATSAPP: "Send a personalized WhatsApp nudge",
        RecoveryActionType.HUMAN_ESCALATION: "Escalate to a human specialist",
    }
    return (
        f"{verbs.get(action, 'Act')} — root cause is {root_cause_summary.lower()} "
        f"with an estimated {pct} recovery probability."
    )


def _rule_signal(action, p: AIDecisionInput, reason: FailureReason) -> str:
    if action == RecoveryActionType.DO_NOTHING:
        return "Intervention cost exceeds expected recovery value"
    if reason in _TRANSIENT:
        return "Failure is typically transient and recoverable"
    if reason == FailureReason.CARD_EXPIRED:
        return "Expired card requires a new instrument, not a retry"
    if reason == FailureReason.USER_ABANDONMENT:
        return "Intent shown at checkout; a nudge can convert"
    return "Action matched to root cause and customer history"


def _merge_signals(*groups: List[str]) -> List[str]:
    seen, out = set(), []
    for group in groups:
        for s in group:
            if s and s not in seen:
                seen.add(s)
                out.append(s)
    return out[:8]


# --------------------------------------------------------------------------- #
# LLM path
# --------------------------------------------------------------------------- #
def _apply_llm(base: AIDecision, payload: AIDecisionInput,
               ml_signals: List[str]) -> tuple[Optional[AIDecision], Optional[str]]:
    """Merge the LLM's recommendation onto the valid heuristic baseline.

    The LLM enriches action/reason/risk/root-cause; the ML probability stays
    authoritative. Returns (decision, reason); reason is a classified code on
    failure (LLM_TIMEOUT / INVALID_JSON / SCHEMA_VALIDATION_ERROR / API_ERROR /
    RATE_LIMIT) so callers can retry and audit.
    """
    out = llm_client.chat_json_ex(
        prompts.DECISION_SYSTEM_PROMPT, prompts.build_decision_user_prompt(payload)
    )
    if out.reason:
        return None, out.reason
    data = out.data
    if not isinstance(data, dict):
        return None, llm_client.INVALID_JSON
    action = _coerce_action(data.get("recommended_action"))
    if action is None:
        return None, llm_client.SCHEMA_VALIDATION_ERROR  # unusable action

    risk = _coerce_risk(data.get("risk_level")) or base.risk_level
    channel = _CHANNEL_FOR_ACTION.get(action, base.channel)
    rc_code = _coerce_reason_code(data.get("root_cause_code")) or base.root_cause_code
    root_cause = str(data.get("root_cause") or base.root_cause).strip()[:200] or base.root_cause
    reason = str(data.get("reason") or base.reason).strip()[:600] or base.reason
    delay = _clamp_int(data.get("delay_minutes"), base.delay_minutes, 0, 1440)
    max_attempts = _clamp_int(data.get("max_attempts"), base.max_attempts, 1, 5)
    confidence = _clamp_float(data.get("confidence"), base.confidence)
    llm_signals = data.get("signals") if isinstance(data.get("signals"), list) else []
    signals = _merge_signals(ml_signals, [str(s) for s in llm_signals], base.signals)

    decision = AIDecision(
        risk_level=risk,
        recovery_probability=payload.model_recovery_probability,
        root_cause_code=rc_code,
        root_cause=root_cause,
        recommended_action=action,
        channel=channel,
        delay_minutes=delay,
        max_attempts=max_attempts,
        confidence=confidence,
        reason=reason,
        signals=signals,
        decided_by="llm",
    )
    return decision, None


_ACTION_SYNONYMS = {
    "RETRY": RecoveryActionType.RETRY_PAYMENT,
    "RETRY_PAYMENT": RecoveryActionType.RETRY_PAYMENT,
    "SCHEDULE": RecoveryActionType.SCHEDULE_RETRY,
    "SCHEDULE_RETRY": RecoveryActionType.SCHEDULE_RETRY,
    "LINK": RecoveryActionType.PAYMENT_LINK,
    "PAYMENT_LINK": RecoveryActionType.PAYMENT_LINK,
    "ALTERNATE": RecoveryActionType.ALTERNATE_PAYMENT_METHOD,
    "ALTERNATE_PAYMENT_METHOD": RecoveryActionType.ALTERNATE_PAYMENT_METHOD,
    "ALTERNATE_METHOD": RecoveryActionType.ALTERNATE_PAYMENT_METHOD,
    "EMAIL": RecoveryActionType.EMAIL,
    "WHATSAPP": RecoveryActionType.WHATSAPP,
    "SMS": RecoveryActionType.WHATSAPP,
    "HUMAN": RecoveryActionType.HUMAN_ESCALATION,
    "ESCALATE": RecoveryActionType.HUMAN_ESCALATION,
    "HUMAN_ESCALATION": RecoveryActionType.HUMAN_ESCALATION,
    "DO_NOTHING": RecoveryActionType.DO_NOTHING,
    "NOTHING": RecoveryActionType.DO_NOTHING,
    "NONE": RecoveryActionType.DO_NOTHING,
}


def _coerce_action(value) -> Optional[RecoveryActionType]:
    if not value:
        return None
    key = str(value).strip().upper().replace(" ", "_").replace("-", "_")
    return _ACTION_SYNONYMS.get(key)


def _coerce_risk(value) -> Optional[RiskLevel]:
    if not value:
        return None
    try:
        return RiskLevel(str(value).strip().upper())
    except ValueError:
        return None


def _coerce_reason_code(value) -> Optional[FailureReason]:
    if not value:
        return None
    try:
        return FailureReason(str(value).strip().upper())
    except ValueError:
        return None


def _clamp_int(value, default: int, lo: int, hi: int) -> int:
    try:
        return max(lo, min(hi, int(float(value))))
    except (TypeError, ValueError):
        return default


def _clamp_float(value, default: float) -> float:
    try:
        f = float(value)
    except (TypeError, ValueError):
        return default
    if f > 1.0:  # model returned a percentage
        f = f / 100.0
    return max(0.0, min(1.0, f))
