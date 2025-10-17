import asyncio
from types import SimpleNamespace

import pytest

from api.routes.contact import (
    ContactRequest,
    EscalationTrace,
    TraceDocument,
    contact,
)


class _Recorder:
    def __init__(self) -> None:
        self.info_calls: list[tuple[str, dict]] = []
        self.error_calls: list[tuple[str, dict]] = []

    def info(self, event: str, *, extra: dict | None = None) -> None:
        self.info_calls.append((event, extra or {}))

    def error(self, event: str, *, extra: dict | None = None) -> None:
        self.error_calls.append((event, extra or {}))


def test_contact_route_with_trace(monkeypatch: pytest.MonkeyPatch) -> None:
    logger = _Recorder()
    captured: dict[str, str | dict | None] = {}

    monkeypatch.setattr("api.routes.contact.load_settings", lambda: SimpleNamespace())
    monkeypatch.setattr("api.routes.contact.configure_logging", lambda settings: logger)

    def fake_send_escalation(*, subject: str, body: str, trace: dict | None):
        captured["subject"] = subject
        captured["body"] = body
        captured["trace"] = trace

    monkeypatch.setattr("api.routes.contact.send_escalation", fake_send_escalation)

    trace = EscalationTrace(
        user_id="user-1",
        request_id="trace-001",
        documents=[
            TraceDocument(chunk_id="c1", score=0.9, source_path="docs/file.pdf", page_number=2)
        ],
    )
    payload = ContactRequest(reason="low_confidence", transcript="step 1", trace=trace)
    request = SimpleNamespace(state=SimpleNamespace(request_id="req-001"))

    result = asyncio.run(contact(payload, request))

    assert result == {"status": "accepted"}
    assert captured["trace"]["request_id"] == "trace-001"
    assert "Trace Payload" in captured["body"]
    assert logger.info_calls
