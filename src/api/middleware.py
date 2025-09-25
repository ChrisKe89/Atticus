"""Custom middleware for request IDs and logging."""

from __future__ import annotations

import time
from collections.abc import Awaitable, Callable

from fastapi import Request
from opentelemetry.trace import Status, StatusCode
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

from atticus.logging import log_event, make_request_id
from atticus.telemetry import get_tracer


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach a request ID to each call and emit structured logs."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get("X-Request-ID") or make_request_id()
        request.state.request_id = request_id

        start = time.perf_counter()
        logger = getattr(request.app.state, "logger", None)
        tracer = get_tracer("atticus.api")
        span_name = f"{request.method} {request.url.path}"

        with tracer.start_as_current_span(span_name) as span:
            span.set_attribute("http.method", request.method)
            span.set_attribute("http.target", request.url.path)
            span.set_attribute("atticus.request_id", request_id)
            try:
                response = await call_next(request)
            except Exception as exc:  # pragma: no cover - runtime error path
                span.record_exception(exc)
                span.set_status(Status(StatusCode.ERROR, str(exc)))
                if logger is not None:
                    log_event(
                        logger,
                        "request_error",
                        request_id=request_id,
                        method=request.method,
                        path=request.url.path,
                        error=str(exc),
                    )
                raise

            elapsed_ms = (time.perf_counter() - start) * 1000
            span.set_attribute("http.status_code", response.status_code)
            span.set_attribute("http.response_time_ms", round(elapsed_ms, 2))

            response.headers["X-Request-ID"] = request_id

            if logger is not None:
                log_event(
                    logger,
                    "request_complete",
                    request_id=request_id,
                    method=request.method,
                    path=request.url.path,
                    status=response.status_code,
                    latency_ms=round(elapsed_ms, 2),
                )

            metrics = getattr(request.app.state, "metrics", None)
            if metrics is not None and request.url.path == "/ask" and hasattr(request.state, "confidence"):
                metrics.record(
                    float(request.state.confidence),
                    elapsed_ms,
                    bool(getattr(request.state, "escalate", False)),
                )

        return response
