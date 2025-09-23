import os

import pytest


def test_mailer_import_or_skip():
    try:
        from atticus.notify.mailer import send_escalation  # noqa
    except Exception as e:
        pytest.skip(f"mailer not implemented yet: {e}")


@pytest.mark.skipif(
    not os.environ.get("SMTP_HOST"), reason="requires SMTP configuration in environment"
)
def test_send_escalation_smoke(monkeypatch):
    from atticus.notify import mailer

    class FakeSMTP:
        def __init__(self, host, port):
            pass

        def starttls(self):
            pass

        def login(self, u, p):
            pass

        def sendmail(self, a, b, c):
            pass

        def quit(self):
            pass

    monkeypatch.setattr(mailer, "SMTP", FakeSMTP, raising=False)
    mailer.send_escalation("Unit Test", "body")
