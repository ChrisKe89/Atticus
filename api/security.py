"""Security-related middleware for enforcing trusted gateway boundaries."""

from __future__ import annotations

import hashlib
import uuid
from ipaddress import ip_address
from typing import Awaitable, Callable

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from atticus.config import load_settings
from atticus.logging import log_event


def _hash_identifier(value: str | None) -> str | None:
    if not value:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


class TrustedGatewayMiddleware(BaseHTTPMiddleware):
    """Ensure requests originate from the enterprise gateway or loopback."""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable[[Request], Awaitable[Response]],
    ) -> Response:
        settings = getattr(request.app.state, "settings", None) or load_settings()

        if not settings.enforce_gateway_boundary:
            return await call_next(request)

        client_host = request.client.host if request.client else None
        rejection_reason: str | None = None

        if client_host is None:
            if settings.allow_loopback_requests:
                return await call_next(request)
            rejection_reason = "missing_client_ip"
        else:
            try:
                client_ip = ip_address(client_host)
            except ValueError:
                if settings.allow_loopback_requests and client_host in {"testclient", "localhost"}:
                    return await call_next(request)
                rejection_reason = "invalid_client_ip"
            else:
                if client_ip.is_loopback and settings.allow_loopback_requests:
                    return await call_next(request)

                networks = settings.trusted_gateway_networks
                if not networks:
                    rejection_reason = "no_trusted_networks"
                elif not any(client_ip in network for network in networks):
                    rejection_reason = "untrusted_source"
                elif settings.require_forwarded_for_header and not request.headers.get(
                    "X-Forwarded-For"
                ):
                    rejection_reason = "missing_forwarded_for"
                elif settings.require_https_forward_proto:
                    proto = request.headers.get("X-Forwarded-Proto", "").lower()
                    if proto != "https":
                        rejection_reason = "non_https_forwarded_proto"

        if rejection_reason is not None:
            return self._reject(
                request,
                reason=rejection_reason,
                client_host=client_host,
            )

        return await call_next(request)

    def _reject(
        self,
        request: Request,
        *,
        reason: str,
        client_host: str | None = None,
    ) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None) or request.headers.get(
            "X-Request-ID"
        )
        if request_id is None:
            request_id = uuid.uuid4().hex

        logger = getattr(request.app.state, "logger", None)
        if logger is not None:
            log_event(
                logger,
                "gateway_request_blocked",
                request_id=request_id,
                reason=reason,
                client_hash=_hash_identifier(client_host),
            )

        payload = {
            "error": "forbidden",
            "detail": "Request rejected by enterprise boundary enforcement.",
            "request_id": request_id,
        }
        return JSONResponse(payload, status_code=403, headers={"X-Request-ID": request_id})
