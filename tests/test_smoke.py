from __future__ import annotations

import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api.main import app
from retriever.models import Answer, Citation


@pytest.fixture(name="client")
def client_fixture() -> TestClient:
    return TestClient(app, raise_server_exceptions=False)


def test_success_and_partial_paths(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    monkeypatch.setenv("CONFIDENCE_THRESHOLD", "0.70")
    monkeypatch.setenv("TEAM_EMAIL_NTS", "nts@example.com")
    monkeypatch.setenv("CONTACT_EMAIL", "contact@example.com")
    monkeypatch.setenv("ESCALATION_COUNTER_FILE", str(tmp_path / "counter"))
    monkeypatch.setenv("ESCALATION_LOG_JSON", str(tmp_path / "log.jsonl"))
    monkeypatch.setenv("ESCALATION_LOG_CSV", str(tmp_path / "log.csv"))
    monkeypatch.setenv("SMTP_HOST", "smtp.test.local")
    monkeypatch.setenv("SMTP_PORT", "2525")
    monkeypatch.setenv("SMTP_FROM", "atticus@example.com")
    monkeypatch.setenv("SMTP_DRY_RUN", "1")

    state = {"low": False}

    def fake_answer(question: str, *args, **kwargs) -> Answer:
        if state["low"]:
            return Answer(
                question=question,
                summary="Low confidence answer.",
                bullets=["Contact NTS for confirmation."],
                citations=[
                    Citation(
                        chunk_id="chunk-1",
                        source_path="content/doc.pdf",
                        page_number=2,
                        heading="Section",
                        score=0.5,
                    )
                ],
                confidence=0.42,
                should_escalate=True,
            )
        state["low"] = True
        return Answer(
            question=question,
            summary="High confidence answer.",
            bullets=["Workflow updated in 2024."],
            citations=[],
            confidence=0.92,
            should_escalate=False,
        )

    monkeypatch.setattr("api.routes.ask.answer_question", fake_answer)

    first = client.post(
        "/ask",
        json={"question": "What is the escalation policy for ApeosPro production printers?"},
    )
    assert first.status_code == 200
    first_payload = first.json()
    assert first_payload["should_escalate"] is False
    assert first_payload["request_id"]
    assert first_payload["bullets"]

    second = client.post(
        "/ask",
        json={"query": "Need more info about ApeosPro service warranty timelines"},
    )
    assert second.status_code == 206
    second_payload = second.json()
    assert second_payload["escalated"] is True
    assert second_payload["ae_id"].startswith("AE")
    assert second_payload["sources"]
    assert second_payload["bullets"]

    json_log = Path(os.environ["ESCALATION_LOG_JSON"])
    assert json_log.exists()
    logged = json_log.read_text(encoding="utf-8").strip().splitlines()
    assert any(second_payload["ae_id"] in line for line in logged)


def test_clarification_flow(monkeypatch: pytest.MonkeyPatch, client: TestClient) -> None:
    monkeypatch.setenv("CONFIDENCE_THRESHOLD", "0.70")

    response = client.post("/ask", json={"query": "help"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["clarification_needed"] is True
    assert "more context" in payload["answer"].lower()
