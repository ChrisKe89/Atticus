"""Shared FastAPI dependencies."""

import logging
from pathlib import Path
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from atticus.logging import configure_logging
from atticus.metrics import MetricsRecorder
from core.config import AppSettings, load_settings


def get_settings() -> AppSettings:
    settings = load_settings()
    settings.ensure_directories()
    return settings


SettingsDep = Annotated[AppSettings, Depends(get_settings)]


def get_logger(settings: SettingsDep) -> logging.Logger:
    return configure_logging(settings)


_METRICS_SINGLETON: MetricsRecorder | None = None


def get_metrics(settings: SettingsDep) -> MetricsRecorder:
    global _METRICS_SINGLETON
    if _METRICS_SINGLETON is None or _METRICS_SINGLETON.settings is not settings:
        settings.ensure_directories()
        _METRICS_SINGLETON = MetricsRecorder(
            settings=settings,
            store_path=Path("logs/metrics/metrics.csv"),
        )
    return _METRICS_SINGLETON


LoggerDep = Annotated[logging.Logger, Depends(get_logger)]
MetricsDep = Annotated[MetricsRecorder, Depends(get_metrics)]


def require_admin_token(request: Request, settings: SettingsDep) -> None:
    token = settings.admin_api_token
    if not token:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Admin API token not configured.",
        )
    provided = request.headers.get("X-Admin-Token")
    if not provided:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Admin-Token header.",
        )
    if provided != token:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid admin token.",
        )


AdminGuard = Annotated[None, Depends(require_admin_token)]
