import asyncio
from types import SimpleNamespace
from fastapi import status
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request

from api.errors import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)


class _Recorder:
    def __init__(self) -> None:
        self.info_calls: list[tuple[str, dict | None]] = []
        self.error_calls: list[tuple[str, dict | None]] = []

    def info(self, event: str, *, extra: dict | None = None) -> None:
        self.info_calls.append((event, extra))

    def error(self, event: str, *, extra: dict | None = None) -> None:
        self.error_calls.append((event, extra))


def _make_request(logger: _Recorder | None = None) -> Request:
    app = SimpleNamespace(state=SimpleNamespace(logger=logger))
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "GET",
        "path": "/tests",
        "headers": [],
        "app": app,
    }

    async def _receive() -> dict:
        return {"type": "http.request"}

    request = Request(scope, _receive)
    request.state.request_id = "req-123"
    return request


def test_http_exception_handler_logs_server_errors() -> None:
    logger = _Recorder()
    request = _make_request(logger)
    exc = StarletteHTTPException(status_code=500, detail="boom")

    response = asyncio.run(http_exception_handler(request, exc))

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert logger.error_calls
    payload = logger.error_calls[0][1]
    assert payload and payload["extra_payload"]["detail"] == "boom"


def test_validation_exception_handler_collects_fields() -> None:
    logger = _Recorder()
    request = _make_request(logger)
    exc = RequestValidationError(
        [
            {"loc": ("body", "question"), "msg": "field required"},
            {"loc": ("body", "filters", "source"), "msg": "invalid source"},
        ]
    )

    response = asyncio.run(validation_exception_handler(request, exc))

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    body = response.body.decode("utf-8")
    assert '"fields"' in body
    assert logger.error_calls  # validation errors are logged


def test_unhandled_exception_handler_logs_error() -> None:
    logger = _Recorder()
    request = _make_request(logger)

    response = asyncio.run(unhandled_exception_handler(request, RuntimeError("unexpected")))

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert logger.error_calls
