"""Aggregate API router."""
from __future__ import annotations

from fastapi import APIRouter

from . import (
    routes_admin,
    routes_analytics,
    routes_audit,
    routes_cases,
    routes_customers,
    routes_dashboard,
    routes_health,
    routes_settings,
    routes_simulation,
    routes_webhooks,
)

api_router = APIRouter()
api_router.include_router(routes_health.router)
api_router.include_router(routes_dashboard.router)
api_router.include_router(routes_cases.router)
api_router.include_router(routes_customers.router)
api_router.include_router(routes_analytics.router)
api_router.include_router(routes_audit.router)
api_router.include_router(routes_simulation.router)
api_router.include_router(routes_settings.router)
api_router.include_router(routes_webhooks.router)
api_router.include_router(routes_admin.router)

__all__ = ["api_router"]
