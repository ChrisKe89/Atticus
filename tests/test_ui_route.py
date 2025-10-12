import pytest

from retriever.models import FamilyOption
from retriever.resolver import ModelResolution


def test_ui_route_or_skip():
    try:
        from api.main import app
    except Exception as e:
        pytest.skip(f"api not implemented yet: {e}")
        return

    try:
        from fastapi.testclient import TestClient
    except Exception as e:
        pytest.skip(f"fastapi not installed: {e}")
        return

    client = TestClient(app)
    r = client.get("/")
    assert r.status_code == 404
    payload = r.json()
    assert payload["error"] == "not_found"
    assert payload["request_id"]


def test_ui_route_ask_returns_clarification(monkeypatch: pytest.MonkeyPatch):
    try:
        from api.main import app
        from fastapi.testclient import TestClient
    except Exception as exc:
        pytest.skip(f"api prerequisites missing: {exc}")
        return

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
        "api.routes.chat.answer_question",
        lambda *args, **kwargs: pytest.fail(
            "answer_question should not run when clarification is returned"
        ),
    )

    client = TestClient(app)
    response = client.post("/ask", json={"question": "Tell me about the printer."})
    assert response.status_code == 200
    data = response.json()
    assert data["clarification"]["message"]
    assert {option["id"] for option in data["clarification"]["options"]} == {"C7070", "C8180"}
    assert data.get("answers") == []
    assert data.get("sources") == []
