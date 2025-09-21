"""FastAPI application for Atticus."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from atticus.logging import configure_logging
from atticus.metrics import MetricsRecorder

from .dependencies import get_settings
from .middleware import RequestContextMiddleware
from .routes import admin, ask, health, ingest
from .routes import eval as eval_routes


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    logger = configure_logging(settings)
    metrics = MetricsRecorder(settings=settings)
    app.state.settings = settings
    app.state.logger = logger
    app.state.metrics = metrics
    try:
        yield
    finally:
        metrics.flush()


app = FastAPI(
    title="Atticus RAG API",
    version="0.2.1",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)
app.add_middleware(RequestContextMiddleware)
app.include_router(health.router)
app.include_router(ingest.router)
app.include_router(ask.router)
app.include_router(admin.router)
app.include_router(eval_routes.router)
