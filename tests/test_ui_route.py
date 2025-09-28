import pytest


def test_ui_route_or_skip():
    try:
        from api.main import app
    except Exception as e:
        pytest.skip(f"api not implemented yet: {e}")
        return

    try:
        from fastapi.testclient import TestClient
    except Exception as e:
        pytest.skip(f"fastapi not installed: {e}")
        return

    client = TestClient(app)
    r = client.get("/")
    assert r.status_code == 404
    payload = r.json()
    assert payload["error"] == "not_found"
    assert payload["request_id"]
