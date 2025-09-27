"""FastAPI application for Atticus."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.staticfiles import StaticFiles

from atticus.logging import configure_logging
from atticus.metrics import MetricsRecorder

from .dependencies import get_settings
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
    version="0.2.3",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)
app.add_middleware(RequestContextMiddleware)
app.include_router(health.router)
app.include_router(ingest.router)
app.include_router(chat_routes.router)
app.include_router(admin.router)
app.include_router(eval_routes.router)
app.include_router(contact_routes.router)

# Static and templates per acceptance
app.mount("/static", StaticFiles(directory="web/static"), name="static")
templates = Jinja2Templates(directory="web/templates")


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "index.html")


@app.get("/ui", response_class=HTMLResponse)
async def ui_alias(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(request, "index.html")
