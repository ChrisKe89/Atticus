import pytest
from typing import Any


def test_chat_route_or_skip() -> None:
    api_main = pytest.importorskip("api.main")
    TestClient = pytest.importorskip("fastapi.testclient").TestClient

    client = TestClient(api_main.app)
    try:
        r = client.post("/ask", json={"question": "ping"})
    except FileNotFoundError as exc:
        pytest.skip(f"index not built: {exc}")
        return
    except ValueError as exc:
        pytest.skip(f"vector store unavailable: {exc}")
        return

    assert r.status_code == 200
    data: dict[str, Any] = r.json()
    assert data["request_id"]
    assert r.headers.get("X-Request-ID") == data["request_id"]
    assert "answer" in data
    assert "sources" in data
    assert isinstance(data["sources"], list)
    if data["sources"]:
        first = data["sources"][0]
        assert {"path"}.issubset(first)
        assert "chunkId" in first
    assert isinstance(data["confidence"], (float, int))
    assert isinstance(data["should_escalate"], bool)


def test_chat_route_rejects_placeholder_or_skip() -> None:
    api_main = pytest.importorskip("api.main")
    TestClient = pytest.importorskip("fastapi.testclient").TestClient

    client = TestClient(api_main.app)
    try:
        r = client.post("/ask", json={"question": "string"})
    except FileNotFoundError as exc:
        pytest.skip(f"index not built: {exc}")
        return
    except ValueError as exc:
        pytest.skip(f"vector store unavailable: {exc}")
        return

    assert r.status_code == 400
    data = r.json()
    assert data["error"] == "bad_request"
    assert "Provide a real question" in data["detail"]
    assert data["request_id"]
    assert r.headers.get("X-Request-ID") == data["request_id"]


def test_chat_route_rate_limit(monkeypatch) -> None:
    config_module = pytest.importorskip("atticus.config")
    config_module.reset_settings_cache()
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", "1")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "60")

    api_main = pytest.importorskip("api.main")
    TestClient = pytest.importorskip("fastapi.testclient").TestClient

    client = TestClient(api_main.app)
    try:
        first = client.post("/ask", json={"question": "ping"})
    except FileNotFoundError as exc:
        pytest.skip(f"index not built: {exc}")
        return
    except ValueError as exc:
        pytest.skip(f"vector store unavailable: {exc}")
        return

    if first.status_code != 200:
        pytest.skip("first request did not succeed; skipping rate limit assertion")
        return

    second = client.post("/ask", json={"question": "another"})
    assert second.status_code == 429
    data = second.json()
    assert data["error"] == "rate_limited"
    assert "request_id" in data
