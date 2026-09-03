"""Shared API dependencies.

The product has no user accounts, so nearly every endpoint is read-only and
open. One is not: `/settings/email/test` sends real mail from a verified sender
domain to a caller-supplied address, so leaving it anonymous on a public URL
would make it a spam relay that burns the domain's sending reputation.

The reseed/reset endpoints this guard also used to cover have been removed —
they were destructive, had no UI, and seeding is reachable without HTTP via
`bootstrap.ensure_ready()` and `scripts/seed.py`.
"""
from __future__ import annotations

import hmac

from fastapi import Header, HTTPException, status

from ..config import settings
from ..logging_config import get_logger

logger = get_logger(__name__)


def require_admin(x_admin_token: str | None = Header(default=None)) -> None:
    """Authorise a cost-incurring endpoint.

    · `ADMIN_TOKEN` set   → the `X-Admin-Token` header must match it.
    · `ADMIN_TOKEN` unset → allowed only when the app is not publicly
      reachable, so local development stays frictionless while a deployed
      instance fails closed instead of exposing an anonymous mail relay.

    The token is compared in constant time so a wrong guess leaks no timing
    information, and is never logged.
    """
    expected = settings.admin_token
    if expected:
        supplied = x_admin_token or ""
        if not hmac.compare_digest(supplied, expected):
            logger.warning("Rejected admin request: missing or invalid X-Admin-Token.")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing or invalid X-Admin-Token.",
                headers={"WWW-Authenticate": "X-Admin-Token"},
            )
        return

    if settings.is_public_deployment:
        logger.warning("Rejected admin request: ADMIN_TOKEN is not configured.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                "Sending test email is disabled on this deployment. "
                "Set ADMIN_TOKEN and send it as the X-Admin-Token header to enable it."
            ),
        )
