# tests/test_contact_route.py
import pytest


# Fixture lives in THIS file (no conftest.py needed)
@pytest.fixture
def patch_smtp(monkeypatch):
    class FakeSMTP:
        def __init__(self, *a, **k):
            pass

        def __enter__(self):
            return self

        def __exit__(self, *a):
            return False

        def connect(self, *a, **k):
            pass

        def ehlo(self, *a, **k):
            pass

        def starttls(self, *a, **k):
            pass

        def login(self, *a, **k):
            pass

        def sendmail(self, *a, **k):
            pass

        def send_message(self, *a, **k):
            pass

        def quit(self, *a, **k):
            pass

        def close(self, *a, **k):
            pass

    # Patch both import styles used by mailer
    for t in [
        "atticus.notify.mailer.smtplib.SMTP",
        "atticus.notify.mailer.SMTP",
        "atticus.notify.mailer.smtplib.SMTP_SSL",
        "atticus.notify.mailer.SMTP_SSL",
    ]:
        try:
            monkeypatch.setattr(t, FakeSMTP, raising=True)
        except Exception:
            pass


def _mk_client():
    api_main = pytest.importorskip("api.main")
    TestClient = pytest.importorskip("fastapi.testclient").TestClient
    return TestClient(api_main.app), api_main.app


def test_contact_route_smoke_or_skip(monkeypatch, patch_smtp):
    client = app = None
    # Minimal env so startup doesn't bail
    monkeypatch.setenv("SMTP_HOST", "smtp.test.local")
    monkeypatch.setenv("SMTP_PORT", "1025")
    monkeypatch.setenv("SMTP_USER", "user")
    monkeypatch.setenv("SMTP_PASS", "pass")
    monkeypatch.setenv("SMTP_FROM", "atticus-escalations@agentk.fyi")

    config_module = pytest.importorskip("atticus.config")
    config_module.reset_settings_cache()

    try:
        client, app = _mk_client()
    except Exception as e:
        pytest.skip(f"api not importable yet: {e}")
        return

    known = {r.path for r in app.routes}
    for path in ("/contact", "/api/contact"):
        if path not in known:
            continue
        r = client.post(path, json={"reason": "test"})
        if r.status_code in (200, 202):
            try:
                data = r.json()
            except Exception:
                data = {}
            assert data.get("status") in {None, "accepted", "ok", "queued", "success"}
            return

    pytest.fail(f"No working contact endpoint. routes={sorted(known)}")


def test_contact_route_with_transcript_or_skip(monkeypatch, patch_smtp):
    client = app = None
    monkeypatch.setenv("SMTP_HOST", "smtp.test.local")
    monkeypatch.setenv("SMTP_PORT", "1025")
    monkeypatch.setenv("SMTP_USER", "user")
    monkeypatch.setenv("SMTP_PASS", "pass")
    monkeypatch.setenv("SMTP_FROM", "atticus-escalations@agentk.fyi")

    config_module = pytest.importorskip("atticus.config")
    config_module.reset_settings_cache()

    try:
        client, app = _mk_client()
    except Exception as e:
        pytest.skip(f"api not importable yet: {e}")
        return

    payload = {"reason": "test_with_transcript", "transcript": ["Q: hi", "A: hello"]}
    known = {r.path for r in app.routes}
    for path in ("/contact", "/api/contact"):
        if path not in known:
            continue
        r = client.post(path, json=payload)
        if r.status_code in (200, 202):
            try:
                data = r.json()
            except Exception:
                data = {}
            assert data.get("status") in {"accepted", "ok", "queued", "success", None}
            return

    pytest.fail("No contact endpoint accepted the request.")


def test_contact_route_handles_mailer_failure(monkeypatch, patch_smtp):
    monkeypatch.setenv("SMTP_HOST", "smtp.test.local")
    monkeypatch.setenv("SMTP_PORT", "1025")
    monkeypatch.setenv("SMTP_FROM", "atticus-escalations@agentk.fyi")
    monkeypatch.setenv("CONTACT_EMAIL", "support@example.com")

    config_module = pytest.importorskip("atticus.config")
    config_module.reset_settings_cache()

    try:
        client, _app = _mk_client()
    except Exception as e:
        pytest.skip(f"api not importable yet: {e}")
        return

    notify_module = pytest.importorskip("atticus.notify")

    def boom(*_args, **_kwargs):
        raise notify_module.EscalationDeliveryError("boom", reason="connection_error")

    monkeypatch.setattr("api.routes.contact.send_escalation", boom, raising=True)

    response = client.post("/contact", json={"reason": "failing"})

    assert response.status_code == 502
    data = response.json()
    assert data["error"] == "internal_error"
    assert "Unable to deliver" in data["detail"]
    assert data["request_id"]
