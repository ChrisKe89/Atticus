"""Shared FastAPI dependencies."""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from atticus.config import AppSettings, load_settings
from atticus.logging import configure_logging
from atticus.metrics import MetricsRecorder


def get_settings() -> AppSettings:
    settings = load_settings()
    settings.ensure_directories()
    return settings


SettingsDep = Annotated[AppSettings, Depends(get_settings)]


def get_logger(settings: SettingsDep) -> logging.Logger:
    return configure_logging(settings)


@lru_cache(maxsize=1)
def get_metrics(settings: SettingsDep) -> MetricsRecorder:
    recorder = MetricsRecorder(settings=settings, store_path=Path("logs/metrics/metrics.csv"))
    return recorder


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
