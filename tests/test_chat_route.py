import pytest


def test_chat_route_or_skip():
    try:
        from api.main import app  # expected FastAPI app
    except Exception as e:
        pytest.skip(f"api not implemented yet: {e}")
        return

    try:
        from fastapi.testclient import TestClient
    except Exception as e:
        pytest.skip(f"fastapi not installed: {e}")
        return

    client = TestClient(app)
    try:
        r = client.post("/ask", json={"query": "ping"})
    except FileNotFoundError as exc:
        pytest.skip(f"index not built: {exc}")
        return
    assert r.status_code == 200
    data = r.json()
    assert "answer" in data


def test_chat_route_rejects_placeholder_or_skip():
    try:
        from api.main import app
    except Exception as e:
        import pytest

        pytest.skip(f"api not implemented yet: {e}")
        return

    try:
        from fastapi.testclient import TestClient
    except Exception as e:
        import pytest

        pytest.skip(f"fastapi not installed: {e}")
        return

    client = TestClient(app)
    try:
        r = client.post("/ask", json={"query": "string"})
    except FileNotFoundError as exc:
        pytest.skip(f"index not built: {exc}")
        return
    assert r.status_code == 400
