"""Provider-agnostic LLM client (OpenAI or Anthropic).

Exposes helpers used by the decision engine and message generator. The `*_ex`
variants return an `LLMOutcome` carrying a classified failure reason so callers
can retry and log exactly why a fallback happened:

  LLM_TIMEOUT · INVALID_JSON · SCHEMA_VALIDATION_ERROR · API_ERROR · RATE_LIMIT

Any failure returns an outcome with `data=None` and a reason, so the caller can
retry once and then fall back to the deterministic heuristic. Secrets never log.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Optional

from ..config import settings
from ..logging_config import get_logger

logger = get_logger(__name__)

# Fallback reason codes.
LLM_TIMEOUT = "LLM_TIMEOUT"
INVALID_JSON = "INVALID_JSON"
SCHEMA_VALIDATION_ERROR = "SCHEMA_VALIDATION_ERROR"
API_ERROR = "API_ERROR"
RATE_LIMIT = "RATE_LIMIT"


@dataclass
class LLMOutcome:
    data: Optional[dict] = None
    text: Optional[str] = None
    reason: Optional[str] = None  # None on success; a reason code on failure


def is_configured() -> bool:
    return settings.llm_configured


def provider() -> str:
    return settings.resolved_llm_provider


def _classify(exc: Exception) -> str:
    name = type(exc).__name__.lower()
    msg = str(exc).lower()
    if "timeout" in name or "timed out" in msg or "timeout" in msg:
        return LLM_TIMEOUT
    if "ratelimit" in name or "rate limit" in msg or "429" in msg or "quota" in msg:
        return RATE_LIMIT
    return API_ERROR


def chat_text_ex(system: str, user: str, max_tokens: Optional[int] = None,
                 force_json: bool = False) -> LLMOutcome:
    if not settings.llm_configured:
        return LLMOutcome(reason=API_ERROR)
    prov = settings.resolved_llm_provider
    max_tokens = max_tokens or settings.llm_max_tokens
    try:
        text = _openai(system, user, max_tokens, force_json) if prov == "openai" \
            else _anthropic(system, user, max_tokens)
        return LLMOutcome(text=text)
    except Exception as exc:  # noqa: BLE001
        reason = _classify(exc)
        logger.warning("LLM (%s) call failed [%s]: %s", prov, reason, exc)
        return LLMOutcome(reason=reason)


def chat_json_ex(system: str, user: str, max_tokens: Optional[int] = None) -> LLMOutcome:
    out = chat_text_ex(system, user, max_tokens=max_tokens, force_json=True)
    if out.reason:
        return out
    data = _extract_json(out.text or "")
    if data is None:
        return LLMOutcome(text=out.text, reason=INVALID_JSON)
    return LLMOutcome(data=data, text=out.text)


# Backwards-compatible simple accessors (used by the message generator).
def chat_text(system: str, user: str, max_tokens: Optional[int] = None,
              force_json: bool = False) -> Optional[str]:
    return chat_text_ex(system, user, max_tokens=max_tokens, force_json=force_json).text


def chat_json(system: str, user: str, max_tokens: Optional[int] = None) -> Optional[dict]:
    return chat_json_ex(system, user, max_tokens=max_tokens).data


# --------------------------------------------------------------------------- #
# Cached clients so the underlying HTTPS connection is pooled/reused across calls
# (avoids re-doing TLS setup every request; the startup warm-up primes it).
_openai_client = None
_anthropic_client = None


def _get_openai_client():
    global _openai_client
    if _openai_client is None:
        from openai import OpenAI
        _openai_client = OpenAI(api_key=settings.llm_api_key, timeout=settings.llm_timeout_seconds)
    return _openai_client


def _openai(system: str, user: str, max_tokens: int, force_json: bool) -> Optional[str]:
    client = _get_openai_client()
    kwargs = {
        "model": settings.resolved_llm_model,
        "max_tokens": max_tokens,
        "temperature": 0.2,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    }
    if force_json:
        kwargs["response_format"] = {"type": "json_object"}
    resp = client.chat.completions.create(**kwargs)
    return resp.choices[0].message.content


def _get_anthropic_client():
    global _anthropic_client
    if _anthropic_client is None:
        from anthropic import Anthropic
        _anthropic_client = Anthropic(api_key=settings.llm_api_key, timeout=settings.llm_timeout_seconds)
    return _anthropic_client


def _anthropic(system: str, user: str, max_tokens: int) -> Optional[str]:
    client = _get_anthropic_client()
    msg = client.messages.create(
        model=settings.resolved_llm_model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")


def _extract_json(text: str) -> Optional[dict]:
    if not text:
        return None
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    candidate = fenced.group(1) if fenced else text
    match = re.search(r"\{.*\}", candidate, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None
