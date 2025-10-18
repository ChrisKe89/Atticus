import httpx
import pytest


def _build_app():
    api_security = pytest.importorskip("api.security")
    FastAPI = pytest.importorskip("fastapi").FastAPI

    app = FastAPI()

    @app.get("/ping")
    async def ping() -> dict[str, str]:
        return {"status": "ok"}

    app.add_middleware(api_security.TrustedGatewayMiddleware)
    return app


async def _issue_request(
    client_tuple: tuple[str, int], headers: dict[str, str] | None = None
) -> httpx.Response:
    app = _build_app()
    transport = httpx.ASGITransport(app=app, client=client_tuple)
    async with httpx.AsyncClient(transport=transport, base_url="http://gateway") as client:
        return await client.get("/ping", headers=headers)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


@pytest.mark.anyio
async def test_trusted_gateway_allows_configured_proxy(monkeypatch):
    config_module = pytest.importorskip("atticus.config")
    config_module.reset_settings_cache()
    monkeypatch.setenv("ENFORCE_GATEWAY_BOUNDARY", "1")
    monkeypatch.setenv("ALLOW_LOOPBACK_REQUESTS", "0")
    monkeypatch.setenv("TRUSTED_GATEWAY_SUBNETS", "10.0.0.0/8")
    monkeypatch.setenv("REQUIRE_FORWARDED_FOR_HEADER", "1")
    monkeypatch.setenv("REQUIRE_HTTPS_FORWARD_PROTO", "1")

    response = await _issue_request(
        ("10.1.2.3", 443),
        headers={"X-Forwarded-For": "203.0.113.9", "X-Forwarded-Proto": "https"},
    )

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.anyio
async def test_trusted_gateway_blocks_untrusted_source(monkeypatch):
    config_module = pytest.importorskip("atticus.config")
    config_module.reset_settings_cache()
    monkeypatch.setenv("ENFORCE_GATEWAY_BOUNDARY", "1")
    monkeypatch.setenv("ALLOW_LOOPBACK_REQUESTS", "0")
    monkeypatch.setenv("TRUSTED_GATEWAY_SUBNETS", "10.0.0.0/8")
    monkeypatch.setenv("REQUIRE_FORWARDED_FOR_HEADER", "1")
    monkeypatch.setenv("REQUIRE_HTTPS_FORWARD_PROTO", "1")

    response = await _issue_request(
        ("198.51.100.5", 8443),
        headers={"X-Forwarded-For": "203.0.113.9", "X-Forwarded-Proto": "https"},
    )

    assert response.status_code == 403
    payload = response.json()
    assert payload["error"] == "forbidden"
    assert payload["detail"].startswith("Request rejected")


@pytest.mark.anyio
async def test_trusted_gateway_allows_loopback_when_enabled(monkeypatch):
    config_module = pytest.importorskip("atticus.config")
    config_module.reset_settings_cache()
    monkeypatch.setenv("ENFORCE_GATEWAY_BOUNDARY", "1")
    monkeypatch.setenv("ALLOW_LOOPBACK_REQUESTS", "1")
    monkeypatch.setenv("TRUSTED_GATEWAY_SUBNETS", "10.0.0.0/8")
    monkeypatch.setenv("REQUIRE_FORWARDED_FOR_HEADER", "1")
    monkeypatch.setenv("REQUIRE_HTTPS_FORWARD_PROTO", "1")

    response = await _issue_request(("127.0.0.1", 5000))
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
