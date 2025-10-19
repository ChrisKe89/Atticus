from __future__ import annotations

from pathlib import Path

from core.schemas.sse import AnswerEvent, EndEvent, StartEvent, event_schema, write_json_schema


def test_answer_event_payload_coercion():
    payload = {
        "answer": "Yes, the pilot concludes in four weeks.",
        "confidence": 0.82,
        "should_escalate": False,
        "request_id": "req-001",
        "sources": [],
    }
    event = AnswerEvent.model_validate({"type": "answer", "payload": payload})
    assert event.payload.request_id == "req-001"
    assert event.payload.answer == "Yes, the pilot concludes in four weeks."


def test_end_event_alias_supports_camel_case():
    event = EndEvent.model_validate({"type": "end", "requestId": "req-002"})
    assert event.request_id == "req-002"
    start = StartEvent.model_validate({"type": "start", "requestId": "req-002"})
    assert start.request_id == "req-002"


def test_json_schema_matches_fixture(tmp_path: Path):
    temp_target = tmp_path / "sse-events.schema.json"
    write_json_schema(temp_target)
    expected = Path("schemas/sse-events.schema.json").read_text(encoding="utf-8")
    actual = temp_target.read_text(encoding="utf-8")
    assert actual == expected


def test_event_schema_contains_references():
    schema = event_schema()
    assert "oneOf" in schema
    literals = []
    defs = schema.get("definitions", {})
    for entry in schema["oneOf"]:
        ref = entry.get("$ref")
        if ref:
            key = ref.split("/")[-1]
            node = defs.get(key, {})
            literal = node.get("properties", {}).get("type", {}).get("const")
            literals.append(literal)
    assert set(literals) == {"start", "answer", "end"}
