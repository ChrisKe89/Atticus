import pytest
from typing import Any


def test_chat_route_or_skip() -> None:
    api_main = pytest.importorskip("api.main")
    TestClient = pytest.importorskip("fastapi.testclient").TestClient

    client = TestClient(api_main.app)
    try:
        r = client.post("/ask", json={"query": "ping"})
    except FileNotFoundError as exc:
        pytest.skip(f"index not built: {exc}")
        return

    assert r.status_code == 200
    data: dict[str, Any] = r.json()
    assert "answer" in data


def test_chat_route_rejects_placeholder_or_skip() -> None:
    api_main = pytest.importorskip("api.main")
    TestClient = pytest.importorskip("fastapi.testclient").TestClient

    client = TestClient(api_main.app)
    try:
        r = client.post("/ask", json={"query": "string"})
    except FileNotFoundError as exc:
        pytest.skip(f"index not built: {exc}")
        return

    assert r.status_code == 400
    data = r.json()
    assert data["error"] == "bad_request"
    assert "Provide a real question" in data["detail"]
    assert data["request_id"]
    assert r.headers.get("X-Request-ID") == data["request_id"]
