from __future__ import annotations

import logging
import sys
from typing import cast

import structlog
from structlog.stdlib import BoundLogger

from core.config import load_settings


def _logging_preferences() -> tuple[str, str]:
    settings = load_settings()
    level = settings.log_level.upper()
    fmt = settings.log_format.lower()
    if not hasattr(logging, level):
        level = "INFO"
    if fmt not in {"json", "console"}:
        fmt = "json"
    return level, fmt


def _configure_once() -> None:
    if getattr(_configure_once, "_did", False):
        return

    level_name, format_name = _logging_preferences()

    processors: list[structlog.types.Processor] = [
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    if format_name == "console":
        processors.append(structlog.dev.ConsoleRenderer())
    else:
        processors.append(structlog.processors.JSONRenderer())

    level = getattr(logging, level_name, logging.INFO)
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=level)

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(level),
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    _configure_once._did = True  # type: ignore[attr-defined]


def get_logger(name: str = "atticus") -> BoundLogger:
    _configure_once()
    logger = structlog.get_logger(name)
    return cast(BoundLogger, logger)
