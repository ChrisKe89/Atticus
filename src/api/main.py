"""FastAPI application for Atticus."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import cast

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles
from starlette.types import ExceptionHandler

from atticus.logging import configure_logging
from atticus.metrics import MetricsRecorder
from atticus.telemetry import configure_telemetry

from .dependencies import get_settings
from .errors import (
    http_exception_handler,
    server_exception_handler,
    validation_exception_handler,
)
from .middleware import RequestContextMiddleware
from .routes import admin, ask, health, ingest
from .routes import contact as contact_routes
from .routes import eval as eval_routes


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    logger = configure_logging(settings)
    configure_telemetry(settings, logger)
    metrics = MetricsRecorder(settings=settings)
    app.state.settings = settings
    app.state.logger = logger
    app.state.metrics = metrics
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


app = FastAPI(
    title="Atticus RAG API",
    version="0.5.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)
app.add_middleware(RequestContextMiddleware)
app.add_exception_handler(HTTPException, cast(ExceptionHandler, http_exception_handler))
app.add_exception_handler(
    RequestValidationError,
    cast(ExceptionHandler, validation_exception_handler),
)
app.add_exception_handler(Exception, server_exception_handler)
app.include_router(health.router)
app.include_router(ingest.router)
app.include_router(ask.router)
app.include_router(admin.router)
app.include_router(eval_routes.router)
app.include_router(contact_routes.router)

# Static and templates per acceptance
app.mount("/static", StaticFiles(directory="web/static"), name="static")
templates = Jinja2Templates(directory="web/templates")


def _template_context(request: Request) -> dict[str, object]:
    settings = getattr(request.app.state, "settings", None)
    banner_enabled = bool(getattr(settings, "escalation_banner_enabled", False))
    banner_timeout = getattr(settings, "ui_banner_dismiss_timeout_ms", 12000)
    return {
        "request": request,
        "banner_enabled": banner_enabled,
        "banner_timeout": banner_timeout,
    }


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("main.html", _template_context(request))


@app.get("/ui", response_class=HTMLResponse)
async def ui_alias(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("main.html", _template_context(request))
