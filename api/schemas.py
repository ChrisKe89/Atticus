"""Pydantic models for API payloads."""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    manifest_present: bool
    document_count: int
    chunk_count: int
    embedding_model: Optional[str] = None


class IngestRequest(BaseModel):
    full_refresh: bool = False
    paths: Optional[List[Path]] = None


class IngestResponse(BaseModel):
    documents_processed: int
    documents_skipped: int
    chunks_indexed: int
    elapsed_seconds: float
    manifest_path: str
    index_path: str
    snapshot_path: str


class AskRequest(BaseModel):
    question: str
    filters: Optional[Dict[str, str]] = Field(default=None, description="Metadata filters such as path_prefix or source_type")


class CitationModel(BaseModel):
    chunk_id: str
    source_path: str
    page_number: Optional[int] = None
    heading: Optional[str] = None
    score: float


class AskResponse(BaseModel):
    answer: str
    confidence: float
    should_escalate: bool
    citations: List[CitationModel]
    request_id: str


class EvalResponse(BaseModel):
    metrics: Dict[str, float]
    deltas: Dict[str, float]
    summary_csv: str
    summary_json: str


class DictionaryEntry(BaseModel):
    term: str
    synonyms: List[str]


class DictionaryPayload(BaseModel):
    entries: List[DictionaryEntry]


class ErrorLogEntry(BaseModel):
    time: str
    message: str
    details: Dict[str, str] = Field(default_factory=dict)

