"""FastAPI application for Atticus."""

from __future__ import annotations

from fastapi import FastAPI

from atticus.logging import configure_logging
from atticus.metrics import MetricsRecorder

from .dependencies import get_settings
from .middleware import RequestContextMiddleware
from .routes import admin, ask, eval as eval_routes, health, ingest

app = FastAPI(title="Atticus RAG API", version="0.1.0", docs_url="/docs", redoc_url="/redoc")
app.add_middleware(RequestContextMiddleware)
app.include_router(health.router)
app.include_router(ingest.router)
app.include_router(ask.router)
app.include_router(admin.router)
app.include_router(eval_routes.router)


@app.on_event("startup")
async def startup_event() -> None:
    settings = get_settings()
    logger = configure_logging(settings)
    metrics = MetricsRecorder(settings=settings)
    app.state.settings = settings
    app.state.logger = logger
    app.state.metrics = metrics


@app.on_event("shutdown")
async def shutdown_event() -> None:
    metrics: MetricsRecorder | None = getattr(app.state, "metrics", None)
    if metrics is not None:
        metrics.flush()

