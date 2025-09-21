"""Vector retrieval utilities for Atticus."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import faiss  # type: ignore[import-untyped]
import numpy as np
from rapidfuzz import fuzz

from atticus.config import AppSettings, Manifest, load_manifest
from atticus.embeddings import EmbeddingClient
from atticus.faiss_index import StoredChunk, load_faiss_index, load_metadata
from atticus.logging import log_event


@dataclass(slots=True)
class SearchResult:
    chunk_id: str
    source_path: str
    text: str
    score: float
    page_number: int | None
    heading: str | None
    metadata: dict[str, str]


class VectorStore:
    """FAISS-backed vector search with optional hybrid re-ranking."""

    def __init__(self, settings: AppSettings, logger: logging.Logger) -> None:
        self.settings = settings
        self.logger = logger

        manifest = load_manifest(settings.manifest_path)
        if manifest is None:
            raise FileNotFoundError("Vector manifest not found. Run ingestion first.")
        self.manifest: Manifest = manifest

        self.chunks: list[StoredChunk] = load_metadata(settings.metadata_path)
        self.index = load_faiss_index(settings.faiss_index_path, settings.embed_dimensions)
        self.embedding_client = EmbeddingClient(settings, logger=logger)

        if self.index.ntotal != len(self.chunks):
            raise RuntimeError("FAISS index size does not match metadata entries")

    def _apply_filters(self, chunk: StoredChunk, filters: dict[str, str] | None) -> bool:
        if not filters:
            return True
        manifest_entry: dict[str, Any] = self.manifest.documents.get(chunk.source_path, {})
        source_type = manifest_entry.get("source_type")
        if filters.get("source_type") and filters["source_type"] != source_type:
            return False
        prefix = filters.get("path_prefix")
        if prefix and not Path(chunk.source_path).as_posix().startswith(prefix):
            return False
        return True

    def search(self, query: str, top_k: int = 10, filters: dict[str, str] | None = None, hybrid: bool = True) -> list[SearchResult]:
        if self.index.ntotal == 0:
            return []

        embedding = np.array(self.embedding_client.embed_texts([query])[0], dtype=np.float32)
        faiss.normalize_L2(embedding.reshape(1, -1))
        scores, indices = self.index.search(embedding.reshape(1, -1), min(self.index.ntotal, max(top_k * 2, top_k)))

        results: list[SearchResult] = []
        for idx, score in zip(indices[0], scores[0], strict=False):
            if idx < 0:
                continue
            chunk = self.chunks[int(idx)]
            if not self._apply_filters(chunk, filters):
                continue
            manifest_entry = self.manifest.documents.get(chunk.source_path, {})
            metadata: dict[str, str] = {"source_type": str(manifest_entry.get("source_type", ""))}
            metadata.update(chunk.extra)
            results.append(
                SearchResult(
                    chunk_id=chunk.chunk_id,
                    source_path=chunk.source_path,
                    text=chunk.text,
                    score=float(score),
                    page_number=chunk.page_number,
                    heading=chunk.section,
                    metadata=metadata,
                )
            )
            if len(results) >= top_k:
                break

        if hybrid and results:
            for item in results:
                text_score = fuzz.partial_ratio(query, item.text) / 100.0
                item.score = 0.7 * item.score + 0.3 * text_score
            results.sort(key=lambda result: result.score, reverse=True)
            results = results[:top_k]

        log_event(
            self.logger,
            "retrieval_query",
            query=query,
            top_k=top_k,
            results=len(results),
            filters=filters or {},
        )
        return results

