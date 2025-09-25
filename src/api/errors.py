"""Shared error response helpers for consistent API semantics."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import Request
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

SERVER_ERROR_THRESHOLD = 500


class ErrorResponse(BaseModel):
    """Structured error payload aligned with Atticus API policy."""

    error: str = Field(..., description="Stable error identifier")
    detail: str = Field(..., description="Human-readable description of the failure")
    status: int = Field(..., description="HTTP status code")
    request_id: str = Field(..., description="Correlation identifier echoed back to clients")
    fields: dict[str, Any] | None = Field(
        default=None,
        description="Optional map of field-level validation issues",
    )
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(tz=UTC),
        description="When the error was generated",
    )


def _ensure_request_id(request: Request) -> str:
    request_id = getattr(request.state, "request_id", "")
    if not request_id:
        request_id = uuid.uuid4().hex
        request.state.request_id = request_id
    return request_id


def _log_error(request: Request, response: ErrorResponse, exc: Exception | None = None) -> None:
    logger = getattr(request.app.state, "logger", None)
    if logger is None:
        return
    extra: dict[str, Any] = {
        "status": response.status,
        "request_id": response.request_id,
        "error": response.error,
    }
    if response.fields:
        extra["fields"] = response.fields
    if exc is not None:
        logger.error(
            response.detail,
            exc_info=exc,
            extra={"extra_payload": extra},
        )
    else:
        logger.warning(response.detail, extra={"extra_payload": extra})


def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    request_id = _ensure_request_id(request)
    detail: str
    fields: dict[str, Any] | None = None
    if isinstance(exc.detail, dict):
        detail = str(exc.detail.get("detail", exc.detail))
        fields = exc.detail.get("fields") if isinstance(exc.detail.get("fields"), dict) else None
        error_code = str(exc.detail.get("error", "http_error"))
    else:
        detail = str(exc.detail)
        error_code = "http_error"
    payload = ErrorResponse(
        error=error_code,
        detail=detail,
        status=exc.status_code,
        request_id=request_id,
        fields=fields,
    )
    _log_error(request, payload, exc if exc.status_code >= SERVER_ERROR_THRESHOLD else None)
    return JSONResponse(status_code=exc.status_code, content=payload.model_dump(mode="json"))


def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    request_id = _ensure_request_id(request)
    fields: dict[str, Any] = {}
    for error in exc.errors():
        location = ".".join(str(part) for part in error.get("loc", ()) if part != "body")
        key = location or "request"
        fields[key] = error.get("msg", "Invalid value")
    payload = ErrorResponse(
        error="validation_error",
        detail="One or more validation errors occurred",
        status=422,
        request_id=request_id,
        fields=fields or None,
    )
    _log_error(request, payload)
    return JSONResponse(status_code=422, content=payload.model_dump(mode="json"))


def server_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = _ensure_request_id(request)
    payload = ErrorResponse(
        error="internal_server_error",
        detail="An unexpected error occurred",
        status=500,
        request_id=request_id,
    )
    _log_error(request, payload, exc)
    return JSONResponse(status_code=500, content=payload.model_dump(mode="json"))
