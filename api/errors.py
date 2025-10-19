"""Custom exception handlers returning the shared JSON error schema."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from atticus.logging import log_error

from .schemas import ErrorResponse

_ERROR_CODE_BY_STATUS: dict[int, str] = {
    status.HTTP_400_BAD_REQUEST: "bad_request",
    status.HTTP_401_UNAUTHORIZED: "unauthorized",
    status.HTTP_403_FORBIDDEN: "forbidden",
    status.HTTP_404_NOT_FOUND: "not_found",
    status.HTTP_409_CONFLICT: "conflict",
    status.HTTP_422_UNPROCESSABLE_ENTITY: "validation_error",
    status.HTTP_429_TOO_MANY_REQUESTS: "rate_limited",
}


def _lookup_error_code(status_code: int) -> str:
    if status_code in _ERROR_CODE_BY_STATUS:
        return _ERROR_CODE_BY_STATUS[status_code]
    if 500 <= status_code < 600:
        return "internal_error"
    return "http_error"


def _normalize_detail(detail: Any) -> str:
    if isinstance(detail, str):
        return detail
    if isinstance(detail, dict):
        return "; ".join(f"{k}: {v}" for k, v in detail.items()) or "An error occurred"
    if isinstance(detail, Iterable) and not isinstance(detail, (str, bytes)):
        return "; ".join(str(item) for item in detail)
    return str(detail) if detail is not None else "An error occurred"


def _build_response(
    request: Request,
    *,
    status_code: int,
    error: str,
    detail: str,
    fields: dict[str, str] | None = None,
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", "unknown")
    trace_id = getattr(request.state, "trace_id", request_id)
    payload = ErrorResponse(
        error=error,
        detail=detail,
        request_id=request_id,
        fields=fields,
    ).model_dump(exclude_none=True)
    response = JSONResponse(status_code=status_code, content=payload)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Trace-ID"] = trace_id
    return response


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    error_code = _lookup_error_code(exc.status_code)
    detail = _normalize_detail(exc.detail)
    if exc.status_code >= status.HTTP_500_INTERNAL_SERVER_ERROR:
        logger = getattr(request.app.state, "logger", None)
        if logger is not None:
            log_error(
                logger,
                "http_exception",
                request_id=getattr(request.state, "request_id", "unknown"),
                trace_id=getattr(request.state, "trace_id", "unknown"),
                status_code=exc.status_code,
                path=request.url.path,
            )
    return _build_response(
        request,
        status_code=exc.status_code,
        error=error_code,
        detail=detail,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    fields: dict[str, str] = {}
    messages: list[str] = []
    for err in exc.errors():
        loc = err.get("loc", ())
        field_parts = [str(part) for part in loc if part not in {"body", "query"}]
        field = ".".join(field_parts) if field_parts else "payload"
        message = err.get("msg", "Invalid value")
        fields[field] = message
        messages.append(f"{field}: {message}")
    detail = "; ".join(messages) if messages else "Invalid request payload"

    logger = getattr(request.app.state, "logger", None)
    if logger is not None:
        log_error(
            logger,
            "request_validation_error",
            request_id=getattr(request.state, "request_id", "unknown"),
            trace_id=getattr(request.state, "trace_id", "unknown"),
            path=request.url.path,
            field_count=len(fields),
        )
    return _build_response(
        request,
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error=_lookup_error_code(status.HTTP_422_UNPROCESSABLE_ENTITY),
        detail=detail,
        fields=fields or None,
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger = getattr(request.app.state, "logger", None)
    detail = "An internal error occurred."
    if logger is not None:
        log_error(
            logger,
            "unhandled_exception",
            request_id=getattr(request.state, "request_id", "unknown"),
            trace_id=getattr(request.state, "trace_id", "unknown"),
            path=request.url.path,
            error_type=exc.__class__.__name__,
        )
    return _build_response(
        request,
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error="internal_error",
        detail=detail,
    )
