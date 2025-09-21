"""Structured logging for Atticus."""

from __future__ import annotations

import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict

from .config import Settings


class JsonFormatter(logging.Formatter):
    """Format log records as structured JSON."""

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401
        payload: Dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "time": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S%z"),
        }

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        extra = getattr(record, "extra_payload", None)
        if isinstance(extra, dict):
            payload.update(extra)

        return json.dumps(payload, ensure_ascii=False)


def configure_logging(settings: Settings) -> logging.Logger:
    """Configure the Atticus logger with JSON rotation."""

    log_path = Path(settings.log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("atticus")
    logger.setLevel(logging.INFO)

    # Prevent duplicate handlers during repeated invocations.
    if not any(isinstance(h, RotatingFileHandler) for h in logger.handlers):
        handler = RotatingFileHandler(log_path, maxBytes=5_000_000, backupCount=5)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)

    return logger


def log_event(logger: logging.Logger, message: str, **payload: Any) -> None:
    """Emit a structured log entry."""

    logger.info(message, extra={"extra_payload": payload})
