from __future__ import annotations

import logging
import os
import sys
from typing import cast

import structlog
from structlog.stdlib import BoundLogger

_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
_FORMAT = os.getenv("LOG_FORMAT", "json").lower()


def _configure_once() -> None:
    if getattr(_configure_once, "_did", False):
        return

    processors: list[structlog.types.Processor] = [
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]
    if _FORMAT == "console":
        processors.append(structlog.dev.ConsoleRenderer())
    else:
        processors.append(structlog.processors.JSONRenderer())

    level = getattr(logging, _LEVEL, logging.INFO)
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
