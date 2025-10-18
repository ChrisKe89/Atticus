"""Shared SSE event schema used by Python services and the Next.js client."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

SCHEMA_PATH = Path("schemas/sse-events.schema.json")


def _ask_response_schema() -> dict[str, Any]:
    """Return the JSON schema for AskResponse without importing at module load."""

    from api.schemas import AskResponse  # local import avoids circular dependency

    return AskResponse.model_json_schema(ref_template="#/definitions/{model}")


def write_json_schema(path: Path = SCHEMA_PATH) -> None:
    """Synchronise the JSON schema file with the canonical Pydantic models."""

    schema = {
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "$id": "https://atticus.invalid/sse-events.schema.json",
        "title": "AtticusSseEvents",
        "oneOf": [
            {
                "type": "object",
                "properties": {
                    "type": {"const": "start"},
                    "requestId": {"type": "string"},
                },
                "required": ["type", "requestId"],
            },
            {
                "type": "object",
                "properties": {
                    "type": {"const": "end"},
                    "requestId": {"type": "string"},
                },
                "required": ["type", "requestId"],
            },
            {
                "type": "object",
                "properties": {
                    "type": {"const": "answer"},
                    "payload": _ask_response_schema(),
                },
                "required": ["type", "payload"],
            },
        ],
        "definitions": {
            "AskResponse": _ask_response_schema(),
        },
    }

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(schema, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


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
    payload: dict[str, Any]

    @model_validator(mode="after")
    def _validate_payload(self) -> "AnswerEvent":
        from api.schemas import AskResponse

        AskResponse.model_validate(self.payload)
        return self


AnySseEvent = StartEvent | AnswerEvent | EndEvent

__all__ = ["StartEvent", "AnswerEvent", "EndEvent", "AnySseEvent", "write_json_schema", "SCHEMA_PATH"]
