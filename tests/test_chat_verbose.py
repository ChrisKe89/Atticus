import asyncio
from types import SimpleNamespace

import pytest

from api.routes.chat import ask_endpoint
from api.schemas import AskRequest
from retriever.models import Answer, Citation
from retriever.query_splitter import QueryAnswer
from retriever.resolver import ModelScope


class _DummyLogger:
    def info(self, *args, **kwargs):
        pass


def test_ask_endpoint_emits_verbose_logs(monkeypatch: pytest.MonkeyPatch) -> None:
    scope = ModelScope(family_id="C7070", family_label="Apeos C7070", model="Apeos C7070")

    def fake_run_rag_for_each(*args, **kwargs):
        citation = Citation(
            chunk_id="chunk-1",
            source_path="content/manuals/guide.pdf",
            page_number=5,
            heading="Overview",
            score=0.87,
        )
        answer = Answer(
            question="Explain the workflow",
            response="All systems operational.",
            citations=[citation],
            confidence=0.72,
            should_escalate=False,
            model=scope.model,
            family=scope.family_id,
            family_label=scope.family_label,
        )
        return [QueryAnswer(scope=scope, answer=answer)]

    log_calls: list[tuple[str, dict]] = []

    def fake_log_event(logger, event: str, **payload):
        log_calls.append((event, payload))

    def fake_count_tokens(value: str) -> int:
        return len(value.split())

    monkeypatch.setattr("api.routes.chat.run_rag_for_each", fake_run_rag_for_each)
    monkeypatch.setattr("api.routes.chat.log_event", fake_log_event)
    monkeypatch.setattr("api.routes.chat.count_tokens", fake_count_tokens)

    payload = AskRequest(
        question="Explain the workflow", filters={"family": "C7070"}, top_k=3, models=["C7070"]
    )
    request = SimpleNamespace(state=SimpleNamespace(request_id="req-001"))
    settings = SimpleNamespace(verbose_logging=True, trace_logging=True, openai_api_key=None)

    response = asyncio.run(ask_endpoint(payload, request, settings, _DummyLogger()))

    assert response.answer == "All systems operational."
    assert response.sources[0].path == "content/manuals/guide.pdf"
    assert response.answers is not None and len(response.answers) == 1
    first_answer = response.answers[0]
    assert first_answer.model in (None, "Apeos C7070")

    # Two log events: completion + verbose chat turn
    assert {event for event, _ in log_calls} == {"ask_endpoint_complete", "chat_turn"}
    chat_turn_payload = dict(log_calls)["chat_turn"]  # keys are unique in this test, safe to coerce
    assert "Overview" in chat_turn_payload["sources"][0]
