import pytest


@pytest.fixture
def app_with_settings(monkeypatch):
    api_main = pytest.importorskip("api.main")

    # Provide minimal SMTP configuration so startup validations succeed consistently.
    monkeypatch.setenv("SMTP_HOST", "smtp.test.local")
    monkeypatch.setenv("SMTP_PORT", "1025")
    monkeypatch.setenv("SMTP_FROM", "atticus-escalations@agentk.fyi")

    config_module = pytest.importorskip("atticus.config")
    config_module.reset_settings_cache()

    return api_main.app


def test_validation_error_schema(app_with_settings):
    TestClient = pytest.importorskip("fastapi.testclient").TestClient
    with TestClient(app_with_settings) as client:
        response = client.post("/contact", json={})

    assert response.status_code == 422
    payload = response.json()
    assert payload["error"] == "validation_error"
    assert "reason" in payload.get("fields", {})
    assert payload["request_id"]
    assert response.headers.get("X-Request-ID") == payload["request_id"]
    assert response.headers.get("X-Trace-ID") == payload["request_id"]


def test_unauthorized_error_schema(app_with_settings):
    fastapi = pytest.importorskip("fastapi")
    app = app_with_settings

    async def raise_unauthorized():
        raise fastapi.HTTPException(status_code=401, detail="Auth required")

    if not any(getattr(route, "path", None) == "/__unauthorized" for route in app.routes):
        app.add_api_route("/__unauthorized", raise_unauthorized)

    TestClient = pytest.importorskip("fastapi.testclient").TestClient
    with TestClient(app) as client:
        response = client.get("/__unauthorized")
    assert response.status_code == 401
    payload = response.json()
    assert payload["error"] == "unauthorized"
    assert payload["detail"] == "Auth required"
    assert payload["request_id"]
    assert response.headers.get("X-Trace-ID") == payload["request_id"]
