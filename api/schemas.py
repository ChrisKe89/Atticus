"""Pydantic models for API payloads."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    manifest_present: bool
    document_count: int
    chunk_count: int
    embedding_model: str | None = None
    embedding_model_version: str | None = None


class IngestRequest(BaseModel):
    full_refresh: bool = False
    paths: list[Path] | None = None


class IngestResponse(BaseModel):
    documents_processed: int
    documents_skipped: int
    chunks_indexed: int
    elapsed_seconds: float
    manifest_path: str
    index_path: str
    snapshot_path: str
    ingested_at: str
    embedding_model: str
    embedding_model_version: str


class AskRequest(BaseModel):
    question: str
    filters: dict[str, str] | None = Field(
        default=None, description="Metadata filters such as path_prefix or source_type"
    )


class CitationModel(BaseModel):
    chunk_id: str
    source_path: str
    page_number: int | None = None
    heading: str | None = None
    score: float


class AskResponse(BaseModel):
    answer: str
    confidence: float
    should_escalate: bool
    citations: list[CitationModel]
    request_id: str


class EvalResponse(BaseModel):
    metrics: dict[str, float]
    deltas: dict[str, float]
    summary_csv: str
    summary_json: str


class DictionaryEntry(BaseModel):
    term: str
    synonyms: list[str]


class DictionaryPayload(BaseModel):
    entries: list[DictionaryEntry]


class ErrorLogEntry(BaseModel):
    time: str
    message: str
    details: dict[str, str] = Field(default_factory=dict)


class SessionLogEntry(BaseModel):
    request_id: str
    method: str | None = None
    path: str | None = None
    status: int | None = None
    latency_ms: float | None = None
    time: str | None = None
    confidence: float | None = None
    escalate: bool | None = None
    filters: dict[str, Any] | None = None


class SessionLogResponse(BaseModel):
    sessions: list[SessionLogEntry]
