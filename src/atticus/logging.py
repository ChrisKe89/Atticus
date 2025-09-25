"""Structured logging utilities."""

from __future__ import annotations

import json
import logging
import sys
import uuid
from logging import StreamHandler
from logging.handlers import RotatingFileHandler
from pathlib import Path
from types import ModuleType
from typing import Any

from .config import AppSettings

try:  # pragma: no cover - import guard for optional instrumentation
    from opentelemetry import trace as _otel_trace
except Exception:  # pragma: no cover - fallback when OTEL is unavailable
    trace: ModuleType | None = None
else:
    trace = _otel_trace


def _trace_attributes() -> dict[str, str]:
    if trace is None:
        return {}
    try:
        span = trace.get_current_span()
    except Exception:  # pragma: no cover - defensive
        return {}
    if span is None:
        return {}
    ctx = span.get_span_context()
    if ctx is None or not ctx.is_valid:
        return {}
    return {
        "trace_id": f"{ctx.trace_id:032x}",
        "span_id": f"{ctx.span_id:016x}",
    }


class JsonFormatter(logging.Formatter):
    """Formats log records as JSON lines (with optional trace context)."""

    def __init__(self, include_trace: bool = False) -> None:
        super().__init__()
        self.include_trace = include_trace

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

        if self.include_trace:
            payload.update(_trace_attributes())

        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        return json.dumps(payload, ensure_ascii=False)


class PlainFormatter(logging.Formatter):
    """Human friendly formatter for console output."""

    def __init__(self, include_trace: bool = False) -> None:
        super().__init__("[%(levelname)s] %(asctime)s %(message)s", "%Y-%m-%d %H:%M:%S")
        self.include_trace = include_trace

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        fragments: list[str] = []

        extra_data = getattr(record, "extra_payload", None)
        if isinstance(extra_data, dict) and extra_data:
            fragments.append(json.dumps(extra_data, ensure_ascii=False, sort_keys=True))

        if self.include_trace:
            trace_attrs = _trace_attributes()
            if trace_attrs:
                fragments.append(f"trace={trace_attrs['trace_id']} span={trace_attrs['span_id']}")

        if fragments:
            message = f"{message} | {' | '.join(fragments)}"
        return message


def _build_file_handler(path: Path, include_trace: bool) -> RotatingFileHandler:
    path.parent.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(path, maxBytes=5_000_000, backupCount=5, encoding="utf-8")
    handler.setFormatter(JsonFormatter(include_trace=include_trace))
    return handler


def configure_logging(settings: AppSettings) -> logging.Logger:
    """Return a configured root logger for the service."""

    logger = logging.getLogger("atticus")
    level = getattr(logging, settings.log_level.upper(), logging.INFO)
    logger.setLevel(level)

    include_trace = bool(settings.trace_logging or settings.telemetry_enabled)

    if not logger.handlers:
        console_handler = StreamHandler(stream=sys.stdout)
        if settings.verbose_logging:
            console_handler.setFormatter(JsonFormatter(include_trace=include_trace))
        else:
            console_handler.setFormatter(PlainFormatter(include_trace=include_trace))
        logger.addHandler(console_handler)

        logger.addHandler(_build_file_handler(settings.logs_path, include_trace=True))

        error_handler = _build_file_handler(settings.errors_path, include_trace=True)
        error_handler.setLevel(logging.ERROR)
        logger.addHandler(error_handler)
        # Prevent propagation to root handlers (avoids duplicate console output)
        logger.propagate = False
    return logger


def log_event(logger: logging.Logger, event: str, **payload: Any) -> None:
    logger.info(event, extra={"extra_payload": payload})


def log_error(logger: logging.Logger, event: str, **payload: Any) -> None:
    payload.setdefault("severity", "ERROR")
    logger.error(event, extra={"extra_payload": payload})


def make_request_id() -> str:
    """Return a unique request identifier."""

    return uuid.uuid4().hex
