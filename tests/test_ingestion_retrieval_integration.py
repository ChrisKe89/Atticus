"""Integration coverage for pgvector-backed ingestion and retrieval."""

from __future__ import annotations

import copy
import json
import logging
from pathlib import Path
from typing import Any
from collections.abc import Iterable, Sequence

import pytest

from core.config import AppSettings, load_manifest, reset_settings_cache
from atticus.vector_db import StoredChunk
from ingest.pipeline import IngestionOptions, ingest_corpus
from retriever.service import answer_question
from retriever.vector_store import RetrievalMode, VectorStore


class InMemoryPgVectorRepository:
    """In-memory substitute for PgVectorRepository used in tests."""

    _state: dict[str, dict[str, Any]] = {}

    def __init__(self, settings: AppSettings) -> None:
        self.settings = settings
        key = settings.database_url or "default"
        bucket = self._state.setdefault(
            key,
            {
                "documents": {},
                "chunks": {},
            },
        )
        self._documents: dict[str, dict[str, Any]] = bucket["documents"]
        self._chunks: dict[str, StoredChunk] = bucket["chunks"]

    @classmethod
    def reset(cls) -> None:
        cls._state.clear()

    def ensure_schema(self) -> None:  # pragma: no cover - behaviour is implicit in memory
        return

    def fetch_document(self, source_path: str) -> dict[str, Any] | None:
        document = self._documents.get(source_path)
        if not document:
            return None
        return {
            "document_id": document["document_id"],
            "sha256": document["sha256"],
            "source_type": document.get("source_type"),
            "chunk_count": len(document.get("chunks", ())),
        }

    def fetch_chunks_for_source(self, source_path: str) -> list[StoredChunk]:
        document = self._documents.get(source_path)
        if not document:
            return []
        return [copy.deepcopy(chunk) for chunk in document.get("chunks", [])]

    def load_all_chunk_metadata(self) -> list[StoredChunk]:
        return [copy.deepcopy(chunk) for chunk in self._chunks.values()]

    def replace_document(
        self,
        *,
        document_id: str,
        source_path: str,
        sha256: str,
        source_type: str | None,
        chunks: Sequence[StoredChunk],
        ingest_time: str,
    ) -> None:
        stored_chunks = [copy.deepcopy(chunk) for chunk in chunks]
        for chunk in stored_chunks:
            if chunk.embedding is None:
                raise ValueError(f"Chunk {chunk.chunk_id} missing embedding")
        self._documents[source_path] = {
            "document_id": document_id,
            "sha256": sha256,
            "source_type": source_type,
            "ingested_at": ingest_time,
            "chunks": stored_chunks,
        }
        for chunk in stored_chunks:
            self._chunks[chunk.chunk_id] = chunk

    def query_similar_chunks(
        self,
        embedding: Sequence[float],
        *,
        limit: int,
        probes: int | None = None,
    ) -> list[dict[str, Any]]:
        def dot_product(lhs: Iterable[float], rhs: Iterable[float]) -> float:
            return sum(float(a) * float(b) for a, b in zip(lhs, rhs, strict=False))

        results: list[dict[str, Any]] = []
        for chunk in self._chunks.values():
            if chunk.embedding is None:
                continue
            similarity = dot_product(chunk.embedding, embedding)
            distance = max(0.0, 1.0 - similarity)
            results.append(
                {
                    "chunk_id": chunk.chunk_id,
                    "document_id": chunk.document_id,
                    "source_path": chunk.source_path,
                    "text": chunk.text,
                    "metadata": dict(chunk.extra),
                    "page_number": chunk.page_number,
                    "section": chunk.section,
                    "distance": distance,
                }
            )
        results.sort(key=lambda row: row.get("distance", 1.0))
        return results[:limit]

    def truncate(self) -> None:
        self._documents.clear()
        self._chunks.clear()


@pytest.fixture(autouse=True)
def _patch_pgvector(monkeypatch: pytest.MonkeyPatch) -> None:
    InMemoryPgVectorRepository.reset()
    monkeypatch.setattr(
        "ingest.pipeline.PgVectorRepository", InMemoryPgVectorRepository, raising=False
    )
    monkeypatch.setattr(
        "atticus.vector_db.PgVectorRepository", InMemoryPgVectorRepository, raising=False
    )
    monkeypatch.setattr(
        "retriever.vector_store.PgVectorRepository", InMemoryPgVectorRepository, raising=False
    )
    yield
    InMemoryPgVectorRepository.reset()


@pytest.fixture
def test_settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> AppSettings:
    reset_settings_cache()
    base = tmp_path
    monkeypatch.setenv(
        "DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/test_ingestion"
    )
    settings = AppSettings(
        content_dir=base / "content",
        indices_dir=base / "indices",
        snapshots_dir=base / "indices" / "snapshots",
        manifest_path=base / "indices" / "manifest.json",
        metadata_path=base / "indices" / "index_metadata.json",
        logs_path=base / "logs" / "app.jsonl",
        errors_path=base / "logs" / "errors.jsonl",
        evaluation_runs_dir=base / "eval",
        embed_dimensions=128,
        chunk_target_tokens=48,
        chunk_min_tokens=0,
        chunk_overlap_tokens_setting=8,
        top_k=5,
        confidence_threshold=0.4,
    )
    monkeypatch.setattr(AppSettings, "timestamp", lambda self: "2025-02-01T12:00:00")
    yield settings
    reset_settings_cache()


def _write_sample_document(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "Atticus printers support up to 1200 x 1200 dpi resolution.\n"
        "Recommended duty cycle is 5,000 pages per month.",
        encoding="utf-8",
    )


def test_ingest_corpus_creates_manifest_and_metadata(test_settings: AppSettings) -> None:
    document_path = test_settings.content_dir / "catalog" / "spec.txt"
    _write_sample_document(document_path)

    summary = ingest_corpus(settings=test_settings, options=IngestionOptions(paths=[document_path]))

    assert summary.documents_processed == 1
    assert summary.chunks_indexed > 0
    assert Path(summary.manifest_path).exists()
    assert Path(summary.snapshot_path).exists()

    manifest = load_manifest(test_settings.manifest_path)
    assert manifest is not None
    record = manifest.documents.get(str(document_path))
    assert record is not None
    assert int(record.get("chunk_count", 0)) == summary.chunks_indexed

    metadata_payload = json.loads(test_settings.metadata_path.read_text(encoding="utf-8"))
    assert metadata_payload, "metadata snapshot should contain chunks"
    first_chunk = metadata_payload[0]
    assert first_chunk["extra"]["chunk_sha"] == first_chunk["sha256"]
    assert first_chunk["extra"]["source_type"] == "text"


def test_retrieval_pipeline_answers_question(test_settings: AppSettings) -> None:
    document_path = test_settings.content_dir / "catalog" / "capabilities.txt"
    _write_sample_document(document_path)

    ingest_corpus(settings=test_settings, options=IngestionOptions(paths=[document_path]))

    store = VectorStore(test_settings, logging.getLogger("atticus.test"))
    results = store.search(
        "What resolution do printers support?",
        top_k=3,
        mode=RetrievalMode.HYBRID,
    )
    assert results
    top_result = results[0]
    assert top_result.source_path == str(document_path)
    assert top_result.metadata.get("chunking") == "prose"

    answer = answer_question(
        "Summarise the supported print resolution.",
        settings=test_settings,
        logger=logging.getLogger("atticus.test"),
    )
    assert answer.citations, "expected citations in answer"
    assert any(
        "resolution" in cite.source_path or "capabilities" in cite.source_path
        for cite in answer.citations
    )
    assert answer.response
    assert answer.confidence >= 0.4
    assert answer.should_escalate is False
