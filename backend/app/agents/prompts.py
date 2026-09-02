"""Prompt templates for the LLM decision engine and message generator.

The LLM is instructed to return STRICT JSON matching `AIDecision`. Any deviation
is caught by Pydantic validation downstream and the system falls back to the
deterministic heuristic — the model can never emit an un-validated action.
"""
from __future__ import annotations

import json

from ..schemas.decision import AIDecisionInput

DECISION_SYSTEM_PROMPT = """You are the decision core of an AI Revenue Recovery platform.
For each failed/at-risk payment you choose the single best next recovery action, \
bounded by strict business policy. You are an advisor: a deterministic guardrail \
engine validates and executes your recommendation. You never move money yourself.

Principles:
- "DO_NOTHING" is a legitimate, valuable decision when expected recovery value is \
too low relative to the cost/annoyance of intervening. Choose it deliberately.
- Prefer retrying only transient failures (bank decline, timeout, network, some UPI).
- Expired cards cannot be fixed by a retry — request an alternate instrument.
- Checkout abandonment needs a gentle personalized nudge + a ready payment link, \
not an aggressive retry.
- Respect the ML recovery_probability provided as evidence; do not contradict it \
without a concrete reason grounded in the data given.
- Never invent facts, discounts, penalties, deadlines, or history not in the input.

Allowed recommended_action values: RETRY_PAYMENT, PAYMENT_LINK, \
ALTERNATE_PAYMENT_METHOD, EMAIL, WHATSAPP, HUMAN_ESCALATION, \
SCHEDULE_RETRY, DO_NOTHING.
Allowed channel values: PAYMENT_RETRY, PAYMENT_LINK, EMAIL, WHATSAPP, HUMAN, NONE.
Allowed risk_level values: LOW, MEDIUM, HIGH, CRITICAL.
Allowed root_cause_code values: BANK_DECLINE, INSUFFICIENT_FUNDS, PAYMENT_TIMEOUT, \
NETWORK_ERROR, CARD_EXPIRED, UPI_FAILURE, USER_ABANDONMENT, UNKNOWN.

Return ONLY a JSON object, no prose, with exactly these keys:
{
  "risk_level": "...",
  "recovery_probability": 0.0-1.0,
  "root_cause_code": "...",
  "root_cause": "short human phrase",
  "recommended_action": "...",
  "channel": "...",
  "delay_minutes": integer >= 0,
  "max_attempts": integer 1-5,
  "confidence": 0.0-1.0,
  "reason": "one or two sentences, grounded strictly in the input",
  "signals": ["short factual bullet", "..."]
}"""


def build_decision_user_prompt(payload: AIDecisionInput) -> str:
    data = payload.model_dump(mode="json")
    return (
        "Decide the best next recovery action for this case. "
        "Use only these facts:\n```json\n"
        + json.dumps(data, indent=2)
        + "\n```\nReturn the strict JSON object now."
    )


MESSAGE_SYSTEM_PROMPT = """You write concise, professional, non-deceptive payment \
recovery messages for a fintech platform. Rules: never fabricate discounts, \
penalties, deadlines, or consequences; never pressure; be warm and helpful; keep \
it short. Return ONLY a JSON object: {"subject": "...", "body": "..."}. For SMS/\
WhatsApp, subject may be an empty string."""


def build_message_user_prompt(
    customer_name: str, amount: float, currency: str, channel: str, action: str, link: str | None
) -> str:
    link_line = f"A secure payment link is available: {link}" if link else "No link available."
    return (
        f"Write a {channel} recovery message.\n"
        f"Customer first name: {customer_name}\n"
        f"Amount: {currency} {amount:,.0f}\n"
        f"Recovery action: {action}\n"
        f"{link_line}\n"
        "Keep it under 60 words. Return the JSON now."
    )
