"""Deterministic guardrail / policy engine.

This is the "Rules control" half of *AI decides, Rules control, System executes*.
It takes a validated `AIDecision` plus the live case context and returns a
verdict. No AI output is ever executed without passing through here. Every
blocked or downgraded action is surfaced to the caller for audit logging.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

from ..config import settings
from ..models.enums import RecoveryActionType


@dataclass
class GuardrailContext:
    payment_already_succeeded: bool = False
    case_terminal: bool = False
    retries_used: int = 0
    messages_used: int = 0
    customer_opted_out: bool = False
    hours_since_failure: float = 0.0
    recovery_probability: float = 0.0
    customer_email_present: bool = True


@dataclass
class GuardrailVerdict:
    allowed: bool
    rule: str
    reason: str
    override_action: Optional[RecoveryActionType] = None
    checks: List[dict] = field(default_factory=list)

    @property
    def effective_action_blocked(self) -> bool:
        return not self.allowed and self.override_action is None


_RETRY_ACTIONS = {RecoveryActionType.RETRY_PAYMENT, RecoveryActionType.SCHEDULE_RETRY}
_MESSAGE_ACTIONS = {
    RecoveryActionType.EMAIL,
    RecoveryActionType.WHATSAPP,
}


def policy_config() -> dict:
    return {
        "max_payment_retries": settings.max_payment_retries,
        "max_customer_messages": settings.max_customer_messages,
        "recovery_window_hours": settings.recovery_window_hours,
        "min_recovery_probability": settings.min_recovery_probability,
    }


def evaluate(action: RecoveryActionType, ctx: GuardrailContext) -> GuardrailVerdict:
    checks: List[dict] = []

    def record(name: str, passed: bool, detail: str) -> None:
        checks.append({"check": name, "passed": passed, "detail": detail})

    # 1. Payment already captured -> stop everything.
    ok = not ctx.payment_already_succeeded
    record("payment_not_already_succeeded", ok, "Payment already captured" if not ok else "OK")
    if not ok:
        return GuardrailVerdict(False, "payment_already_succeeded",
                                "Payment already succeeded; recovery halted.", None, checks)

    # 2. Case already closed/terminal.
    ok = not ctx.case_terminal
    record("case_open", ok, "Case already closed" if not ok else "OK")
    if not ok:
        return GuardrailVerdict(False, "case_already_closed",
                                "Recovery case is already in a terminal state.", None, checks)

    # 3. Recovery time window.
    ok = ctx.hours_since_failure <= settings.recovery_window_hours
    record("within_recovery_window", ok,
           f"{ctx.hours_since_failure:.1f}h / {settings.recovery_window_hours}h window")
    if not ok:
        return GuardrailVerdict(False, "recovery_window_exceeded",
                                "Recovery window has elapsed.", None, checks)

    # 4. DO_NOTHING is always permissible (no execution, deliberate stand-down).
    if action == RecoveryActionType.DO_NOTHING:
        record("do_nothing_allowed", True, "Deliberate stand-down")
        return GuardrailVerdict(True, "allowed", "DO_NOTHING approved.", None, checks)

    # 5. Minimum recovery probability -> downgrade to DO_NOTHING.
    ok = ctx.recovery_probability >= settings.min_recovery_probability
    record("min_recovery_probability", ok,
           f"{ctx.recovery_probability:.2f} >= {settings.min_recovery_probability}")
    if not ok:
        return GuardrailVerdict(
            False, "below_min_probability",
            "Recovery probability below threshold; downgraded to DO_NOTHING.",
            RecoveryActionType.DO_NOTHING, checks,
        )

    # 6. Customer opt-out blocks outbound messaging (retries/links are allowed).
    if action in _MESSAGE_ACTIONS and ctx.customer_opted_out:
        record("customer_opt_out", False, "Customer opted out of messaging")
        return GuardrailVerdict(False, "customer_opted_out",
                                "Customer has opted out of communications.", None, checks)
    record("customer_opt_out", True, "OK")

    # 6b. Email requires a recipient address on file.
    if action == RecoveryActionType.EMAIL and not ctx.customer_email_present:
        record("customer_email_present", False, "No email address on file")
        return GuardrailVerdict(False, "no_email_address",
                                "Customer has no email address on file.", None, checks)

    # 7. Retry cap.
    if action in _RETRY_ACTIONS:
        ok = ctx.retries_used < settings.max_payment_retries
        record("max_payment_retries", ok,
               f"{ctx.retries_used}/{settings.max_payment_retries} retries used")
        if not ok:
            return GuardrailVerdict(
                False, "max_retries_reached",
                "Maximum payment retries reached; downgraded to a payment link.",
                RecoveryActionType.PAYMENT_LINK, checks,
            )

    # 8. Message cap.
    if action in _MESSAGE_ACTIONS:
        ok = ctx.messages_used < settings.max_customer_messages
        record("max_customer_messages", ok,
               f"{ctx.messages_used}/{settings.max_customer_messages} messages sent")
        if not ok:
            return GuardrailVerdict(False, "max_messages_reached",
                                    "Maximum customer messages reached.", None, checks)

    record("action_eligible", True, "Action approved by policy")
    return GuardrailVerdict(True, "allowed", "Action approved by policy engine.", None, checks)
