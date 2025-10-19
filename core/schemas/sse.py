"""Shared SSE event schema used by Python services and the Next.js client."""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any, Literal, Mapping

from pydantic import BaseModel, Field, TypeAdapter, model_validator

SCHEMA_PATH = Path("schemas/sse-events.schema.json")

if TYPE_CHECKING:
    from api.schemas import AskResponse


def _ask_response_model():
    from api.schemas import AskResponse  # noqa: PLC0415

    return AskResponse


def _ask_response_schema() -> dict[str, Any]:
    """Return the JSON schema for AskResponse without importing at module load."""

    return _ask_response_model().model_json_schema(ref_template="#/definitions/{model}")


class StartEvent(BaseModel):
    """Initial SSE message containing only the request identifier."""

    type: Literal["start"]
    request_id: str = Field(alias="requestId")

    model_config = {"populate_by_name": True}


class EndEvent(BaseModel):
    """Final SSE message signalling the end of the stream."""

    type: Literal["end"]
    request_id: str = Field(alias="requestId")

    model_config = {"populate_by_name": True}


class AnswerEvent(BaseModel):
    """Streamed answer payload validated against the canonical response contract."""

    type: Literal["answer"]
    payload: "AskResponse"

    model_config = {"populate_by_name": True}

    @model_validator(mode="before")
    @classmethod
    def _coerce_payload(cls, data: Any) -> Any:
        if isinstance(data, Mapping) and "payload" in data:
            raw = data["payload"]
            model = _ask_response_model()
            if raw is not None and not isinstance(raw, model):
                parsed = model.model_validate(raw)
                return {**data, "payload": parsed}
        return data


AnswerEvent.model_rebuild(_types_namespace={"AskResponse": _ask_response_model()})

AnySseEvent = StartEvent | AnswerEvent | EndEvent
_ANY_EVENT_ADAPTER = TypeAdapter(AnySseEvent)


def event_schema() -> dict[str, Any]:
    """Return the JSON schema for the SSE events union."""

    schema = _ANY_EVENT_ADAPTER.json_schema(ref_template="#/definitions/{model}")
    if "anyOf" in schema and "oneOf" not in schema:
        schema["oneOf"] = schema.pop("anyOf")
    if "$defs" in schema and "definitions" not in schema:
        schema["definitions"] = schema["$defs"]
    schema["title"] = "AtticusSseEvents"
    schema["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    schema["$id"] = "https://atticus.invalid/sse-events.schema.json"
    return schema


def write_json_schema(path: Path = SCHEMA_PATH) -> None:
    """Synchronise the JSON schema file with the canonical Pydantic models."""

    schema = event_schema()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


__all__ = [
    "SCHEMA_PATH",
    "AnswerEvent",
    "AnySseEvent",
    "EndEvent",
    "StartEvent",
    "_ANY_EVENT_ADAPTER",
    "event_schema",
    "write_json_schema",
]
