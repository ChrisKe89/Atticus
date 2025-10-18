import asyncio
from types import SimpleNamespace
from typing import Any

import pytest

from api.routes.chat import ask_endpoint
from api.schemas import AskRequest
from retriever.models import Answer, Citation, FamilyOption
from retriever.query_splitter import QueryAnswer
from retriever.resolver import ModelResolution, ModelScope


class _DummyLogger:
    def info(self, *args, **kwargs):
        pass


def test_chat_route_or_skip() -> None:
    api_main = pytest.importorskip("api.main")
    TestClient = pytest.importorskip("fastapi.testclient").TestClient

    client = TestClient(api_main.app)
    try:
        r = client.post("/ask", json={"question": "ping"})
    except FileNotFoundError as exc:
        pytest.skip(f"index not built: {exc}")
        return
    except ValueError as exc:
        pytest.skip(f"vector store unavailable: {exc}")
        return

    assert r.status_code == 200
    data: dict[str, Any] = r.json()
    assert data["request_id"]
    assert r.headers.get("X-Request-ID") == data["request_id"]
    assert "answer" in data
    assert "sources" in data
    assert isinstance(data["sources"], list)
    if data["sources"]:
        first = data["sources"][0]
        assert {"path"}.issubset(first)
        assert "chunkId" in first
    assert isinstance(data["confidence"], (float, int))
    assert isinstance(data["should_escalate"], bool)


def test_chat_route_rejects_placeholder_or_skip() -> None:
    api_main = pytest.importorskip("api.main")
    TestClient = pytest.importorskip("fastapi.testclient").TestClient

    client = TestClient(api_main.app)
    try:
        r = client.post("/ask", json={"question": "string"})
    except FileNotFoundError as exc:
        pytest.skip(f"index not built: {exc}")
        return
    except ValueError as exc:
        pytest.skip(f"vector store unavailable: {exc}")
        return

    assert r.status_code == 400
    data = r.json()
    assert data["error"] == "bad_request"
    assert "Provide a real question" in data["detail"]
    assert data["request_id"]
    assert r.headers.get("X-Request-ID") == data["request_id"]


def test_chat_route_rate_limit(monkeypatch) -> None:
    config_module = pytest.importorskip("atticus.config")
    config_module.reset_settings_cache()
    monkeypatch.setenv("RATE_LIMIT_REQUESTS", "1")
    monkeypatch.setenv("RATE_LIMIT_WINDOW_SECONDS", "60")

    api_main = pytest.importorskip("api.main")
    TestClient = pytest.importorskip("fastapi.testclient").TestClient

    client = TestClient(api_main.app)
    try:
        first = client.post("/ask", json={"question": "ping"})
    except FileNotFoundError as exc:
        pytest.skip(f"index not built: {exc}")
        return
    except ValueError as exc:
        pytest.skip(f"vector store unavailable: {exc}")
        return

    if first.status_code != 200:
        pytest.skip("first request did not succeed; skipping rate limit assertion")
        return

    second = client.post("/ask", json={"question": "another"})
    assert second.status_code == 429
    data = second.json()
    assert data["error"] == "rate_limited"
    assert "request_id" in data


def test_ask_endpoint_returns_clarification(monkeypatch: pytest.MonkeyPatch) -> None:
    options = [
        FamilyOption(id="C7070", label="Apeos C7070 range"),
        FamilyOption(id="C8180", label="Apeos C8180 series"),
    ]

    def fake_resolve_models(*args, **kwargs) -> ModelResolution:
        return ModelResolution(
            scopes=[], confidence=0.0, needs_clarification=True, clarification_options=options
        )

    monkeypatch.setattr("api.routes.chat.resolve_models", fake_resolve_models)
    monkeypatch.setattr(
        "api.routes.chat.run_rag_for_each",
        lambda *args, **kwargs: pytest.fail(
            "run_rag_for_each should not be called when clarification is needed"
        ),
    )

    payload = AskRequest(question="Can the printer handle glossy stock?")
    request = SimpleNamespace(state=SimpleNamespace(request_id="req-clarify"))
    settings = SimpleNamespace(verbose_logging=False, trace_logging=False, openai_api_key=None)

    response = asyncio.run(ask_endpoint(payload, request, settings, _DummyLogger()))

    assert response.clarification is not None
    assert response.clarification.message
    assert {option.id for option in response.clarification.options} == {"C7070", "C8180"}
    assert response.answers == []
    assert response.sources == []
    assert response.confidence == 0.0
    assert response.should_escalate is False


def test_ask_endpoint_fans_out_answers(monkeypatch: pytest.MonkeyPatch) -> None:
    options = [
        FamilyOption(id="C7070", label="Apeos C7070 range"),
        FamilyOption(id="C8180", label="Apeos C8180 series"),
    ]
    scopes = [
        ModelScope(family_id="C7070", family_label="Apeos C7070 range", model="Apeos C4570"),
        ModelScope(family_id="C8180", family_label="Apeos C8180 series", model="Apeos C6580"),
    ]

    def fake_resolve_models(*args, **kwargs) -> ModelResolution:
        return ModelResolution(
            scopes=list(scopes),
            confidence=0.9,
            needs_clarification=False,
            clarification_options=options,
        )

    calls = []

    def fake_run_rag_for_each(
        question: str,
        scopes: list[ModelScope],
        **kwargs,
    ) -> list[QueryAnswer]:
        results: list[QueryAnswer] = []
        for scope in scopes:
            calls.append((scope.family_id, scope.model))
            citation = Citation(
                chunk_id=f"{scope.model}-chunk",
                source_path=f"content/{scope.family_id}.pdf",
                page_number=5,
                heading=f"{scope.model} Specs",
                score=0.88,
            )
            answer = Answer(
                question=question,
                response=f"{scope.model} capabilities summary.",
                citations=[citation],
                confidence=0.92,
                should_escalate=False,
                model=scope.model,
                family=scope.family_id,
                family_label=scope.family_label,
            )
            results.append(QueryAnswer(scope=scope, answer=answer))
        return results

    monkeypatch.setattr("api.routes.chat.resolve_models", fake_resolve_models)
    monkeypatch.setattr("api.routes.chat.run_rag_for_each", fake_run_rag_for_each)

    payload = AskRequest(question="Compare the Apeos C4570 and C6580 models.", top_k=2)
    request = SimpleNamespace(state=SimpleNamespace(request_id="req-multi"))
    settings = SimpleNamespace(verbose_logging=False, trace_logging=False, openai_api_key=None)

    response = asyncio.run(ask_endpoint(payload, request, settings, _DummyLogger()))

    assert len(calls) == 2
    assert ("C7070", "Apeos C4570") in calls
    assert ("C8180", "Apeos C6580") in calls

    assert response.answers is not None
    assert len(response.answers) == 2
    assert {answer.model for answer in response.answers} == {"Apeos C4570", "Apeos C6580"}
    assert all(answer.sources for answer in response.answers)
    assert response.should_escalate is False
    assert response.confidence is not None and response.confidence >= 0.0
    assert "###" in (response.answer or "")
