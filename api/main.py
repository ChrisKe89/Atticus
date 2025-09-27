"""FastAPI application for Atticus."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
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
from .routes import admin, health, ingest
from .routes import chat as chat_routes
from .routes import contact as contact_routes
from .routes import eval as eval_routes


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    logger = configure_logging(settings)
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
    version="0.4.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)
app.add_middleware(RequestContextMiddleware)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)
app.include_router(health.router)
app.include_router(ingest.router)
app.include_router(chat_routes.router)
app.include_router(admin.router)
app.include_router(eval_routes.router)
app.include_router(contact_routes.router)



@app.get("/", include_in_schema=False)
async def ui_placeholder() -> JSONResponse:
    """Inform callers that the UI is served by the Next.js frontend."""
    return JSONResponse(
        {"status": "ui_moved", "detail": "Next.js serves the UI on port 3000."},
        status_code=200,
    )
