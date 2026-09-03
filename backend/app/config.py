"""Application configuration loaded from environment variables.

Secrets are never hardcoded. See `.env.example` at the repo root for the full
list of supported variables. All values have safe defaults so the application
runs out-of-the-box in a fully self-contained demo mode (SQLite + simulated
Razorpay + heuristic AI) with zero external credentials.
"""
from __future__ import annotations

import os
from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    # ---- Core app -----------------------------------------------------------
    app_name: str = "AI Revenue Recovery"
    environment: str = "development"
    api_prefix: str = "/api"
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # ---- Admin authentication ----------------------------------------------
    # Shared secret for the one endpoint that spends real money and sender
    # reputation (test email). Required on any publicly reachable deployment;
    # see `api/deps.py`. Unset locally so development stays frictionless.
    admin_token: str = ""

    # ---- Database -----------------------------------------------------------
    # Defaults to a local SQLite file so the project runs without Postgres.
    # Set DATABASE_URL to a postgresql+psycopg URL to use PostgreSQL instead.
    database_url: str = "sqlite:///./ai_revenue_recovery.db"

    # ---- Razorpay (TEST MODE) ----------------------------------------------
    razorpay_key_id: str = ""
    razorpay_key_secret: str = ""
    razorpay_webhook_secret: str = ""

    # ---- LLM decision engine (OpenAI or Anthropic) -------------------------
    llm_provider: str = "auto"  # auto | openai | anthropic
    llm_api_key: str = ""
    llm_model: str = ""  # empty -> a sensible per-provider default is used
    llm_max_tokens: int = 1024
    llm_timeout_seconds: float = 30.0

    # ---- Email (Resend — real transactional email) --------------------------
    # When RESEND_API_KEY and EMAIL_FROM are set, EMAIL recovery actions send a
    # REAL email via Resend. When unset, EMAIL actions are BLOCKED (never faked).
    resend_api_key: str = ""
    email_from: str = ""  # e.g. "AI Revenue Recovery <recovery@yourdomain.com>"
    email_reply_to: str = ""

    # ---- Guardrail policy engine -------------------------------------------
    max_payment_retries: int = 2
    max_customer_messages: int = 2
    recovery_window_hours: int = 24
    min_recovery_probability: float = 0.15

    # ---- ML model -----------------------------------------------------------
    # Trained parameters ship inside the package (app/ml/model_params.json), so
    # there is no model path to configure and no training at runtime.
    ml_random_seed: int = 42

    @field_validator("cors_origins")
    @classmethod
    def _strip(cls, v: str) -> str:
        return v.strip()

    @field_validator("database_url")
    @classmethod
    def _normalise_database_url(cls, v: str) -> str:
        """Accept the Postgres URL forms hosting providers actually hand out.

        Neon, Supabase and Vercel Postgres emit `postgres://...`, which
        SQLAlchemy does not recognise, and `postgresql://...`, which resolves to
        psycopg2 rather than the psycopg 3 driver this project installs. Both are
        rewritten to the explicit `postgresql+psycopg://` form.
        """
        v = v.strip()
        if v.startswith("postgres://"):
            return "postgresql+psycopg://" + v[len("postgres://"):]
        if v.startswith("postgresql://"):
            return "postgresql+psycopg://" + v[len("postgresql://"):]
        return v

    @property
    def cors_origin_list(self) -> List[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    @property
    def razorpay_configured(self) -> bool:
        return bool(self.razorpay_key_id and self.razorpay_key_secret)

    @property
    def razorpay_webhook_configured(self) -> bool:
        return bool(self.razorpay_webhook_secret)

    @property
    def llm_configured(self) -> bool:
        return bool(self.llm_api_key)

    @property
    def resolved_llm_provider(self) -> str:
        if self.llm_provider and self.llm_provider != "auto":
            return self.llm_provider
        # Auto-detect from the key shape.
        if self.llm_api_key.startswith("sk-ant"):
            return "anthropic"
        if self.llm_api_key.startswith(("sk-", "sk-proj-")):
            return "openai"
        return "anthropic"

    @property
    def resolved_llm_model(self) -> str:
        if self.llm_model:
            return self.llm_model
        return "gpt-4o-mini" if self.resolved_llm_provider == "openai" else "claude-sonnet-5"

    @property
    def resend_configured(self) -> bool:
        return bool(self.resend_api_key and self.email_from)

    @property
    def is_sqlite(self) -> bool:
        return self.database_url.startswith("sqlite")

    @property
    def is_public_deployment(self) -> bool:
        """True when this process is reachable from the public internet.

        Any Vercel deployment counts, including previews — an unlisted URL is
        not access control. Used to fail closed on endpoints that must not be
        anonymous in public (admin actions, unverified webhooks).
        """
        return bool(os.getenv("VERCEL")) or self.environment.strip().lower() in {
            "production",
            "prod",
            "staging",
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
