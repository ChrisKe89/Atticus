"""FastAPI application for Atticus."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from atticus.logging import configure_logging
from atticus.metrics import MetricsRecorder

from .dependencies import get_settings
from .errors import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from .middleware import RequestContextMiddleware
from .rate_limit import RateLimiter
from .routes import admin, chat, contact, eval, health, ingest, ui
from .security import TrustedGatewayMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    logger = configure_logging(settings)
    metrics = MetricsRecorder(settings=settings)
    app.state.settings = settings
    app.state.logger = logger
    app.state.metrics = metrics
    app.state.rate_limiter = RateLimiter(
        limit=settings.rate_limit_requests,
        window_seconds=settings.rate_limit_window_seconds,
    )
    # Warn when critical secrets are missing (non-fatal in dev/test)
    if not (settings.openai_api_key or "").strip():
        logger.warning(
            "OPENAI_API_KEY not set; embeddings/generation may fail",
            extra={"extra_payload": {"env": ".env", "key": "OPENAI_API_KEY"}},
        )
    try:
        yield
    finally:
        metrics.flush()


def _load_version() -> str:
    """Return the semantic version recorded in the repository root."""

    version_path = Path(__file__).resolve().parents[1] / "VERSION"
    try:
        version = version_path.read_text(encoding="utf-8").strip()
    except OSError:
        return "0.0.0"
    return version or "0.0.0"


_initial_settings = get_settings()


app = FastAPI(
    title="Atticus RAG API",
    version=_load_version(),
    docs_url=None,
    redoc_url=None,
    lifespan=lifespan,
)
if _initial_settings.cors_allowed_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(_initial_settings.cors_allowed_origins),
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=[
            "X-Request-ID",
            "X-RateLimit-Limit",
            "X-RateLimit-Remaining",
            "Retry-After",
        ],
    )
app.state.settings = _initial_settings
app.add_middleware(TrustedGatewayMiddleware)
app.add_middleware(RequestContextMiddleware)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)
app.include_router(health.router)

if _initial_settings.service_mode == "chat":
    app.include_router(ingest.router)
    app.include_router(chat.router)
    app.include_router(eval.router)
    app.include_router(contact.router)
    app.include_router(ui.router)
elif _initial_settings.service_mode == "admin":
    app.include_router(admin.router)
else:  # pragma: no cover - defensive guard for unexpected configuration
    raise ValueError(f"Unsupported SERVICE_MODE: {_initial_settings.service_mode}")
