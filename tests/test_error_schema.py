"""Validate shared error response schema for the Atticus API."""

from __future__ import annotations

from typing import Any

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient

from api.main import app


@pytest.fixture(name="client")
def client_fixture() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


def _assert_schema(payload: dict[str, Any], status: int) -> None:
    assert payload["status"] == status
    assert isinstance(payload["request_id"], str) and payload["request_id"]
    assert isinstance(payload["detail"], str)
    assert isinstance(payload["error"], str)
    assert "timestamp" in payload


def test_validation_error_schema(client: TestClient) -> None:
    response = client.post("/ask", json={"query": {"unexpected": "type"}})
    assert response.status_code == 422
    body = response.json()
    _assert_schema(body, 422)
    assert body["error"] == "validation_error"
    assert isinstance(body.get("fields"), dict)


def test_http_exception_schema_for_bad_request(client: TestClient) -> None:
    response = client.post("/ask", json={})
    assert response.status_code == 422
    body = response.json()
    _assert_schema(body, 422)
    assert body["error"] == "validation_error"


def test_http_exception_schema_for_unauthorized(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    def fake_answer_question(*_: Any, **__: Any) -> Any:  # pragma: no cover - simple override
        raise HTTPException(
            status_code=401,
            detail={"error": "unauthorized", "detail": "missing credentials"},
        )

    monkeypatch.setattr("api.routes.ask.answer_question", fake_answer_question)
    response = client.post("/ask", json={"query": "auth-check workflow for ApeosPro production fleet"})
    assert response.status_code == 401
    body = response.json()
    _assert_schema(body, 401)
    assert body["error"] == "unauthorized"


def test_server_error_schema(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    def fake_answer_question(*_: Any, **__: Any) -> Any:  # pragma: no cover - deliberate failure
        raise RuntimeError("boom")

    monkeypatch.setattr("api.routes.ask.answer_question", fake_answer_question)
    response = client.post("/ask", json={"query": "boom-check failure for ApeosPro production fleet"})
    assert response.status_code == 500
    body = response.json()
    _assert_schema(body, 500)
    assert body["error"] == "internal_server_error"
