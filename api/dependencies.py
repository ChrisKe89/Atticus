"""Shared FastAPI dependencies."""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from fastapi import Depends

from atticus.config import AppSettings, load_settings
from atticus.logging import configure_logging
from atticus.metrics import MetricsRecorder


@lru_cache(maxsize=1)
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
