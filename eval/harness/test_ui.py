from __future__ import annotations

from fastapi.testclient import TestClient

from api.main import app

HTTP_OK = 200


def test_ui_served() -> None:
    with TestClient(app) as client:
        res = client.get("/ui")
        assert res.status_code == HTTP_OK
        assert "Atticus" in res.text
