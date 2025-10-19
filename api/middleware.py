"""Custom middleware for request IDs and logging."""

from __future__ import annotations

import hashlib
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from atticus.logging import log_error, log_event
from core.config import load_settings

from .rate_limit import RateLimiter


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach a request ID to each call and emit structured logs."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        trace_id = request.headers.get("X-Trace-ID") or request_id
        request.state.request_id = request_id
        request.state.trace_id = trace_id

        start = time.perf_counter()
        logger = getattr(request.app.state, "logger", None)

        limiter = getattr(request.app.state, "rate_limiter", None)
        settings = load_settings()
        if (
            limiter is None
            or limiter.limit != settings.rate_limit_requests
            or limiter.window_seconds != settings.rate_limit_window_seconds
        ):
            limiter = RateLimiter(
                limit=settings.rate_limit_requests,
                window_seconds=settings.rate_limit_window_seconds,
            )
            request.app.state.rate_limiter = limiter
        request.app.state.settings = settings

        decision = None
        if request.method != "OPTIONS":
            identifier = (
                request.headers.get("X-User-ID")
                or request.headers.get("X-Forwarded-For")
                or (request.client.host if request.client else "anonymous")
            )
            decision = limiter.allow(identifier)
            if not decision.allowed:
                hashed = hashlib.sha256(identifier.encode("utf-8")).hexdigest()[:12]
                if logger is not None:
                    log_event(
                        logger,
                        "rate_limit_blocked",
                        request_id=request_id,
                        trace_id=trace_id,
                        identifier_hash=hashed,
                        retry_after=decision.retry_after,
                        path=request.url.path,
                    )
                payload = {
                    "error": "rate_limited",
                    "detail": "Rate limit exceeded. Please retry later.",
                    "request_id": request_id,
                    "trace_id": trace_id,
                }
                headers = {
                    "Retry-After": str(decision.retry_after or 0),
                    "X-Request-ID": request_id,
                    "X-Trace-ID": trace_id,
                    "X-RateLimit-Limit": str(limiter.limit),
                    "X-RateLimit-Remaining": "0",
                }
                return JSONResponse(payload, status_code=429, headers=headers)
            request.state.rate_limit_limit = limiter.limit
            request.state.rate_limit_remaining = decision.remaining

        try:
            response = await call_next(request)
        except Exception as exc:  # pragma: no cover - runtime error path
            if logger is not None:
                log_error(
                    logger,
                    "request_error",
                    request_id=request_id,
                    trace_id=trace_id,
                    method=request.method,
                    path=request.url.path,
                    error_type=exc.__class__.__name__,
                )
            raise

        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Request-ID"] = request_id
        response.headers["X-Trace-ID"] = trace_id
        if limiter is not None:
            limit_value = getattr(request.state, "rate_limit_limit", limiter.limit)
            response.headers["X-RateLimit-Limit"] = str(limit_value)
            remaining_value = getattr(request.state, "rate_limit_remaining", None)
            if remaining_value is not None:
                response.headers["X-RateLimit-Remaining"] = str(max(0, remaining_value))

        if logger is not None:
            log_event(
                logger,
                "request_complete",
                request_id=request_id,
                trace_id=trace_id,
                method=request.method,
                path=request.url.path,
                status=response.status_code,
                latency_ms=round(elapsed_ms, 2),
            )

        metrics = getattr(request.app.state, "metrics", None)
        if (
            metrics is not None
            and request.url.path == "/ask"
            and hasattr(request.state, "confidence")
        ):
            prompt_tokens = getattr(request.state, "prompt_tokens", 0)
            answer_tokens = getattr(request.state, "answer_tokens", 0)
            metrics.record(
                float(request.state.confidence),
                elapsed_ms,
                bool(getattr(request.state, "escalate", False)),
                trace_id=trace_id,
                prompt_tokens=int(prompt_tokens) if prompt_tokens is not None else 0,
                answer_tokens=int(answer_tokens) if answer_tokens is not None else 0,
                logger=logger,
            )

        return response
