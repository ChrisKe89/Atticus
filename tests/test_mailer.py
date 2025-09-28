from __future__ import annotations

import pytest


def test_mailer_import_or_skip():
    try:
        from atticus.notify.mailer import send_escalation  # noqa: F401
    except Exception as e:
        pytest.skip(f"mailer not implemented yet: {e}")


def test_send_escalation_smoke(monkeypatch):
    # Arrange: set minimal SMTP env so code paths that read env won't bail
    monkeypatch.setenv("SMTP_HOST", "smtp.test.local")
    monkeypatch.setenv("SMTP_PORT", "1025")
    monkeypatch.setenv("SMTP_USER", "user")
    monkeypatch.setenv("SMTP_PASS", "pass")
    monkeypatch.setenv("SMTP_FROM", "atticus-escalations@agentk.fyi")
    monkeypatch.setenv("CONTACT_EMAIL", "support@example.com")
    monkeypatch.setenv("SMTP_ALLOW_LIST", "support@example.com,atticus-escalations@agentk.fyi")

    config_module = pytest.importorskip("atticus.config")
    config_module.reset_settings_cache()

    mailer = pytest.importorskip("atticus.notify.mailer")

    created: list[FakeSMTP] = []

    class FakeSMTP:
        def __init__(self, host, port, timeout=None):
            # Assert the code is wiring host/port correctly
            assert host == "smtp.test.local"
            assert str(port) in ("1025", 1025)
            self.started_tls = False
            self.logged_in = False
            self.sent = False
            self.timeout = timeout
            self.message = None
            created.append(self)

        # If your code uses context manager: with smtplib.SMTP(...) as s:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def ehlo(self):
            pass

        # Real code often passes an ssl context
        def starttls(self, context=None):
            self.started_tls = True

        def login(self, u, p):
            # Should be called if SMTP_USER is set
            assert u == "user" and p == "pass"
            self.logged_in = True

        # Some code uses send_message; some uses sendmail
        def send_message(self, msg):
            assert msg["From"]
            assert msg["To"]
            assert msg["Subject"] is not None
            self.sent = True
            self.message = msg.get_content()

        def sendmail(self, a, b, c):
            # Accept either API
            self.sent = True

        def quit(self):
            pass

    # Patch the exact lookup site: atticus.notify.mailer.smtplib.SMTP
    monkeypatch.setattr("atticus.notify.mailer.smtplib.SMTP", FakeSMTP, raising=True)

    # Act: call your function
    trace = {
        "user_id": "user-123",
        "request_id": "req-abc",
        "top_documents": [{"chunk_id": "chunk-1", "score": 0.8, "source_path": "doc.pdf"}],
        "question": "Explain toner yield",
    }
    result = mailer.send_escalation("Unit Test", "body", trace=trace)

    # Assert: whatever your mailer returns; at least it shouldn't raise
    # If your function returns None, just assert True
    assert (
        result is None
        or result is True
        or (isinstance(result, dict) and result.get("status") in ("ok", "dry-run"))
    )
    assert created, "SMTP client should be instantiated"
    sent_client = created[-1]
    assert sent_client.sent
    assert sent_client.message is not None
    assert "Trace Payload" in sent_client.message
    assert "chunk-1" in sent_client.message


def test_send_escalation_dry_run(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.test.local")
    monkeypatch.setenv("SMTP_PORT", "2525")
    monkeypatch.setenv("SMTP_FROM", "atticus-dry-run@example.com")
    monkeypatch.setenv("CONTACT_EMAIL", "sales@example.com")
    monkeypatch.setenv("SMTP_DRY_RUN", "1")
    monkeypatch.setenv("SMTP_ALLOW_LIST", "sales@example.com,atticus-dry-run@example.com")

    config_module = pytest.importorskip("atticus.config")
    config_module.reset_settings_cache()

    mailer = pytest.importorskip("atticus.notify.mailer")

    def fail_connect(*_args, **_kwargs):
        raise AssertionError("SMTP connection should not be attempted in dry-run mode")

    monkeypatch.setattr("atticus.notify.mailer.smtplib.SMTP", fail_connect, raising=True)

    result = mailer.send_escalation("Dry Run", "body", trace={"request_id": "req-1"})

    assert isinstance(result, dict)
    assert result.get("status") == "dry-run"
    assert result.get("host") == "smtp.test.local"
    assert str(result.get("port")) == "2525"


def test_send_escalation_raises_on_connection_error(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.test.local")
    monkeypatch.setenv("SMTP_PORT", "2525")
    monkeypatch.setenv("CONTACT_EMAIL", "sales@example.com")
    monkeypatch.setenv("SMTP_FROM", "atticus@example.com")
    monkeypatch.setenv("SMTP_ALLOW_LIST", "sales@example.com,atticus@example.com")

    config_module = pytest.importorskip("atticus.config")
    config_module.reset_settings_cache()

    mailer = pytest.importorskip("atticus.notify.mailer")

    class BrokenSMTP:
        def __init__(self, *args, **kwargs):
            raise OSError("connection refused")

    monkeypatch.setattr("atticus.notify.mailer.smtplib.SMTP", BrokenSMTP, raising=True)

    with pytest.raises(mailer.EscalationDeliveryError) as excinfo:
        mailer.send_escalation("Fail", "body")

    assert excinfo.value.reason == "connection_error"


def test_send_escalation_rejects_recipient(monkeypatch):
    monkeypatch.setenv("SMTP_HOST", "smtp.test.local")
    monkeypatch.setenv("SMTP_PORT", "2525")
    monkeypatch.setenv("CONTACT_EMAIL", "blocked@example.com")
    monkeypatch.setenv("SMTP_FROM", "atticus@example.com")
    monkeypatch.setenv("SMTP_ALLOW_LIST", "atticus@example.com")

    config_module = pytest.importorskip("atticus.config")
    config_module.reset_settings_cache()

    mailer = pytest.importorskip("atticus.notify.mailer")

    with pytest.raises(mailer.EscalationDeliveryError) as excinfo:
        mailer.send_escalation("Blocked", "body")

    assert excinfo.value.reason == "recipient_not_allowed"
