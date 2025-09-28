"""Structured logging utilities."""

from __future__ import annotations

import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

from .config import AppSettings


class JsonFormatter(logging.Formatter):
    """Formats log records as JSON lines."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "time": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S%z"),
        }

        extra_data = getattr(record, "extra_payload", None)
        if isinstance(extra_data, dict):
            payload.update(extra_data)

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


def _build_file_handler(path: Path) -> RotatingFileHandler:
    path.parent.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(path, maxBytes=5_000_000, backupCount=5, encoding="utf-8")
    handler.setFormatter(JsonFormatter())
    return handler


def configure_logging(settings: AppSettings) -> logging.Logger:
    """Return a configured root logger for the service."""

    logger = logging.getLogger("atticus")
    if not logger.handlers:
        logger.setLevel(getattr(logging, settings.log_level.upper(), logging.INFO))
        logger.addHandler(_build_file_handler(settings.logs_path))

        error_handler = _build_file_handler(settings.errors_path)
        error_handler.setLevel(logging.ERROR)
        logger.addHandler(error_handler)
        # Prevent propagation to root handlers (avoids console encoding issues on Windows)
        logger.propagate = False
    return logger


def log_event(logger: logging.Logger, event: str, **payload: Any) -> None:
    if "trace_id" not in payload and "request_id" in payload:
        payload["trace_id"] = payload["request_id"]
    logger.info(event, extra={"extra_payload": payload})


def log_error(logger: logging.Logger, event: str, **payload: Any) -> None:
    payload.setdefault("severity", "ERROR")
    if "trace_id" not in payload and "request_id" in payload:
        payload["trace_id"] = payload["request_id"]
    logger.error(event, extra={"extra_payload": payload})
