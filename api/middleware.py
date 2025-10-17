"""Custom middleware for request IDs and logging."""

from __future__ import annotations

import hashlib
import time
import uuid
from collections.abc import Awaitable, Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from atticus.config import load_settings
from atticus.logging import log_event

from .rate_limit import RateLimiter


class RequestContextMiddleware(BaseHTTPMiddleware):
    """Attach a request ID to each call and emit structured logs."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        request.state.request_id = request_id
        request.state.trace_id = request_id

        start = time.perf_counter()
        logger = getattr(request.app.state, "logger", None)

        limiter = getattr(request.app.state, "rate_limiter", None)
        # Clarification: rate limit applies to FastAPI /ask endpoint only.
        # The Next.js handler lives under /api/ask and is rate-limited separately via frontend middleware/infra.
        if request.url.path == "/ask":
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
            identifier = (
                request.headers.get("X-User-ID")
                or request.headers.get("X-Forwarded-For")
                or (request.client.host if request.client else "anonymous")
            )
            allowed, retry_after = limiter.allow(identifier)
            if not allowed:
                hashed = hashlib.sha256(identifier.encode("utf-8")).hexdigest()[:12]
                if logger is not None:
                    log_event(
                        logger,
                        "rate_limit_blocked",
                        request_id=request_id,
                        identifier_hash=hashed,
                        retry_after=retry_after,
                    )
                payload = {
                    "error": "rate_limited",
                    "detail": "Rate limit exceeded. Please retry later.",
                    "request_id": request_id,
                }
                return JSONResponse(
                    payload,
                    status_code=429,
                    headers={"Retry-After": str(retry_after), "X-Request-ID": request_id},
                )

        try:
            response = await call_next(request)
        except Exception as exc:  # pragma: no cover - runtime error path
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
        if (
            metrics is not None
            and request.url.path == "/ask"
            and hasattr(request.state, "confidence")
        ):
            metrics.record(
                float(request.state.confidence),
                elapsed_ms,
                bool(getattr(request.state, "escalate", False)),
                trace_id=request_id,
            )

        return response
