"""FastAPI application entrypoint.

Startup is deliberately cheap so the app cold-starts fast as a serverless
function: schema creation and first-run demo seeding happen lazily on the first
request that touches the database (see `bootstrap.ensure_ready`). Running as a
long-lived local server, that work is done eagerly instead, so `uvicorn` is
ready to serve the moment it reports startup.

All financial actions remain bounded by the guardrail engine; the LLM never
executes anything directly.
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api import api_router
from .config import settings
from .database import IS_SERVERLESS
from .logging_config import configure_logging, get_logger
from .ml import get_model

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()

    # Loading the model is a small JSON read — cheap enough to do up front, and
    # it surfaces a corrupt/mismatched parameter file at boot rather than mid-request.
    model = get_model()
    logger.info("Recovery model ready (v=%s, acc=%.3f).", model.version, model.train_accuracy)

    if not IS_SERVERLESS:
        from .bootstrap import ensure_ready

        ensure_ready()

    logger.info(
        "%s API ready. serverless=%s db=%s Razorpay=%s LLM=%s email=%s",
        settings.app_name,
        IS_SERVERLESS,
        "sqlite" if settings.is_sqlite else "postgresql",
        settings.razorpay_configured,
        settings.llm_configured,
        settings.resend_configured,
    )
    yield


app = FastAPI(
    title=settings.app_name,
    version="0.1.0",
    description="AI-powered revenue recovery — detect, diagnose, decide, validate, "
                "recover, measure. Running in Razorpay Test Mode.",
    lifespan=lifespan,
)

# In deployment the UI and API share one origin, so CORS is only needed for
# local development. `*` with credentials is a hole (and browsers reject the
# combination anyway), so credentials are dropped whenever a wildcard is set
# rather than silently trusting every origin.
_cors_origins = settings.cors_origin_list
_cors_wildcard = "*" in _cors_origins
if _cors_wildcard:
    logger.warning("CORS_ORIGINS contains '*' — disabling credentialed CORS requests.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=not _cors_wildcard,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "X-Admin-Token", "X-Razorpay-Signature"],
)

app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/")
def root() -> dict:
    return {
        "app": settings.app_name,
        "tagline": "Find revenue that's slipping away and win it back.",
        "mode": "Razorpay Test Mode",
        "docs": "/docs",
        "api_prefix": settings.api_prefix,
    }


@app.exception_handler(Exception)
async def unhandled_exception_handler(request, exc):  # pragma: no cover
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})
