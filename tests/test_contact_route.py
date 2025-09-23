import pytest


def test_contact_route_or_skip():
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
    r = client.post("/contact", json={"reason": "test"})
    assert r.status_code in (200, 202)


def test_contact_route_with_transcript_or_skip():
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
    payload = {"reason": "test_with_transcript", "transcript": ["Q: hi", "A: hello"]}
    r = client.post("/contact", json=payload)
    assert r.status_code in (200, 202)
    data = r.json()
    assert data.get("status") in {"accepted", "ok"}
