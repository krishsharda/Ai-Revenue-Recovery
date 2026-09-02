"""Channel dispatch: turns an APPROVED action into a concrete (test-mode or
simulated) side effect, and generates personalized customer messages.

Crucial invariant: this module only *executes* an action the guardrail engine
already approved. It clearly distinguishes REAL_RAZORPAY_TEST calls from
SIMULATED actions and never claims a simulated payment was really captured.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..agents import prompts
from ..config import settings
from ..logging_config import get_logger
from ..models.enums import ExecutionMode, RecoveryActionType, RecoveryChannel
from . import razorpay_client

logger = get_logger(__name__)


@dataclass
class ExecutionContext:
    customer_name: str
    amount: float
    currency: str = "INR"
    customer_email: Optional[str] = None
    customer_phone: Optional[str] = None
    description: str = "Complete your payment"


@dataclass
class ChannelOutcome:
    action_type: str
    channel: str
    status: str  # EXECUTED | SIMULATED | FAILED
    execution_mode: str  # REAL_RAZORPAY_TEST | SIMULATED
    detail: str
    external_reference: Optional[str] = None
    message_subject: Optional[str] = None
    message_body: Optional[str] = None


def execute(action: RecoveryActionType, channel: RecoveryChannel, ctx: ExecutionContext,
            use_llm: bool = True, live: bool = True) -> ChannelOutcome:
    # `live` gates real external calls (Razorpay). Bulk seed/simulation run with
    # live=False so booting/reseeding never fires dozens of real API calls; the
    # interactive Execute action runs live=True and creates real test artifacts.
    if action in (RecoveryActionType.RETRY_PAYMENT, RecoveryActionType.SCHEDULE_RETRY):
        return _retry(action, ctx, live)
    if action in (RecoveryActionType.PAYMENT_LINK, RecoveryActionType.ALTERNATE_PAYMENT_METHOD):
        return _payment_link(action, ctx, live)
    if action == RecoveryActionType.EMAIL:
        return _email(ctx, use_llm)
    if action == RecoveryActionType.WHATSAPP:
        return _whatsapp(ctx, use_llm)
    if action == RecoveryActionType.HUMAN_ESCALATION:
        return ChannelOutcome(
            action.value, RecoveryChannel.HUMAN.value, "SIMULATED", ExecutionMode.SIMULATED.value,
            "Escalated to a human recovery specialist (queued).",
        )
    return ChannelOutcome(
        action.value, RecoveryChannel.NONE.value, "SIMULATED", ExecutionMode.SIMULATED.value,
        "No action executed (DO_NOTHING).",
    )


def _retry(action: RecoveryActionType, ctx: ExecutionContext, live: bool = True) -> ChannelOutcome:
    # A card retry cannot be silently charged in test mode; we create a real TEST
    # order to represent the retry attempt when configured, else simulate it.
    if live and razorpay_client.is_configured():
        try:
            order = razorpay_client.create_order(
                ctx.amount, ctx.currency, notes={"purpose": "recovery_retry", "customer": ctx.customer_name}
            )
            return ChannelOutcome(
                action.value, RecoveryChannel.PAYMENT_RETRY.value, "EXECUTED",
                ExecutionMode.REAL_RAZORPAY_TEST.value,
                f"Created real Razorpay TEST order {order.get('id')} for retry.",
                external_reference=order.get("id"),
            )
        except razorpay_client.RazorpayError as exc:
            logger.warning("Retry order creation failed: %s", exc)
    return ChannelOutcome(
        action.value, RecoveryChannel.PAYMENT_RETRY.value, "SIMULATED", ExecutionMode.SIMULATED.value,
        "Simulated payment retry (no live Razorpay credentials).",
    )


def _payment_link(action: RecoveryActionType, ctx: ExecutionContext, live: bool = True) -> ChannelOutcome:
    if live and razorpay_client.is_configured():
        try:
            link = razorpay_client.create_payment_link(
                ctx.amount, ctx.customer_name, ctx.customer_email, ctx.customer_phone, ctx.description, ctx.currency
            )
            return ChannelOutcome(
                action.value, RecoveryChannel.PAYMENT_LINK.value, "EXECUTED",
                ExecutionMode.REAL_RAZORPAY_TEST.value,
                f"Created real Razorpay TEST payment link {link.get('id')}.",
                external_reference=link.get("short_url") or link.get("id"),
            )
        except razorpay_client.RazorpayError as exc:
            logger.warning("Payment link creation failed: %s", exc)
    fake = f"https://rzp.test/pl/{abs(hash(ctx.customer_name + str(ctx.amount))) % 10**8:08d}"
    return ChannelOutcome(
        action.value, RecoveryChannel.PAYMENT_LINK.value, "SIMULATED", ExecutionMode.SIMULATED.value,
        "Simulated payment link (no live Razorpay credentials).", external_reference=fake,
    )


def _email(ctx: ExecutionContext, use_llm: bool = True) -> ChannelOutcome:
    # Bulk/projection path only. Real interactive email is sent by the recovery
    # service via Resend (services/email_service.py); this never sends.
    msg = generate_message(ctx, RecoveryChannel.EMAIL.value, RecoveryActionType.EMAIL.value, None, use_llm)
    return ChannelOutcome(
        RecoveryActionType.EMAIL.value, RecoveryChannel.EMAIL.value, "SIMULATED",
        ExecutionMode.SIMULATED.value, "Simulated email (projection mode — no real send).",
        message_subject=msg["subject"], message_body=msg["body"],
    )


def _whatsapp(ctx: ExecutionContext, use_llm: bool = True) -> ChannelOutcome:
    msg = generate_message(ctx, RecoveryChannel.WHATSAPP.value, RecoveryActionType.WHATSAPP.value, None, use_llm)
    return ChannelOutcome(
        RecoveryActionType.WHATSAPP.value, RecoveryChannel.WHATSAPP.value, "SIMULATED",
        ExecutionMode.SIMULATED.value, "Simulated WhatsApp message (channel not wired to a provider).",
        message_body=msg["body"],
    )


# --------------------------------------------------------------------------- #
# Personalized message generation (LLM optional, safe template fallback)
# --------------------------------------------------------------------------- #
def generate_message(ctx: ExecutionContext, channel: str, action: str, link: Optional[str],
                     use_llm: bool = True) -> dict:
    first_name = ctx.customer_name.split()[0] if ctx.customer_name else "there"
    if use_llm and settings.llm_configured:
        llm = _llm_message(first_name, ctx, channel, action, link)
        if llm:
            return llm
    return _template_message(first_name, ctx, channel, link)


def _template_message(first_name: str, ctx: ExecutionContext, channel: str, link: Optional[str]) -> dict:
    amount = f"{ctx.currency} {ctx.amount:,.0f}"
    link_line = f" You can complete it securely here: {link}" if link else ""
    body = (
        f"Hi {first_name}, your {amount} payment couldn't be completed. "
        f"We've prepared a secure way for you to finish it whenever you're ready.{link_line}"
    )
    subject = f"Complete your {amount} payment"
    return {"subject": subject, "body": body, "generated_by": "template"}


def _llm_message(first_name, ctx, channel, action, link) -> Optional[dict]:
    from ..agents import llm_client

    data = llm_client.chat_json(
        prompts.MESSAGE_SYSTEM_PROMPT,
        prompts.build_message_user_prompt(first_name, ctx.amount, ctx.currency, channel, action, link),
        max_tokens=400,
    )
    if not data:
        return None
    body = str(data.get("body", "")).strip()
    if not body:
        return None
    return {"subject": str(data.get("subject", "")), "body": body, "generated_by": "llm"}
