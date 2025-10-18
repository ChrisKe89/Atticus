"""Vector retrieval utilities for Atticus."""

from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass
from enum import Enum
from typing import Any

from rapidfuzz import fuzz

from core.config import AppSettings, Manifest, load_manifest
from atticus.embeddings import EmbeddingClient
from atticus.logging import log_event
from atticus.vector_db import PgVectorRepository, StoredChunk


class RetrievalMode(str, Enum):
    """Supported retrieval scoring strategies."""

    HYBRID = "hybrid"
    VECTOR = "vector"
    LEXICAL = "lexical"

    @classmethod
    def from_inputs(
        cls,
        mode: "str | RetrievalMode | None",  # noqa: UP037
        hybrid: bool | None,
    ) -> "RetrievalMode":  # noqa: UP037
        if mode is not None:
            if isinstance(mode, cls):
                return mode
            try:
                return cls(str(mode).lower())
            except ValueError as exc:  # pragma: no cover - defensive guard
                raise ValueError(
                    f"Unsupported retrieval mode '{mode}'. Choose from {[item.value for item in cls]}"
                ) from exc
        if hybrid is None:
            return cls.HYBRID
        return cls.HYBRID if hybrid else cls.VECTOR


@dataclass(slots=True)
class SearchResult:
    chunk_id: str
    source_path: str
    text: str
    score: float
    page_number: int | None
    heading: str | None
    metadata: dict[str, str]
    chunk_index: int
    vector_score: float
    lexical_score: float
    fuzz_score: float


class VectorStore:
    """pgvector-backed vector search with optional hybrid re-ranking."""

    def __init__(self, settings: AppSettings, logger: logging.Logger) -> None:
        self.settings = settings
        self.logger = logger

        if not settings.database_url:
            raise ValueError("DATABASE_URL must be configured before querying the vector store")

        self.repository = PgVectorRepository(settings)
        self.repository.ensure_schema()
        manifest = load_manifest(settings.manifest_path)
        if manifest is None:
            raise FileNotFoundError("Vector manifest not found. Run ingestion first.")
        self.manifest: Manifest = manifest

        self.chunks: list[StoredChunk] = self.repository.load_all_chunk_metadata()
        self.chunk_index_map: dict[str, int] = {
            chunk.chunk_id: idx for idx, chunk in enumerate(self.chunks)
        }
        self.chunk_lookup: dict[str, StoredChunk] = {chunk.chunk_id: chunk for chunk in self.chunks}
        self.embedding_client = EmbeddingClient(settings, logger=logger)

        self._lex_tokens: list[list[str]] = []
        self._lex_df: dict[str, int] = {}
        self._lex_len: list[int] = []
        self._lex_avgdl: float = 0.0
        self._lex_ready: bool = False
        self._build_lexical_index()

    def _apply_filters(self, chunk: StoredChunk, filters: dict[str, str] | None) -> bool:
        if not filters:
            return True
        manifest_entry: dict[str, Any] = self.manifest.documents.get(chunk.source_path, {})
        source_type = manifest_entry.get("source_type")
        if filters.get("source_type") and filters["source_type"] != source_type:
            return False
        prefix = filters.get("path_prefix")
        if prefix and not chunk.source_path.startswith(prefix):
            return False
        family_filter = filters.get("product_family")
        if family_filter:
            allowed = {
                part.strip().lower() for part in str(family_filter).split(",") if part.strip()
            }
            if allowed:
                chunk_family = (
                    chunk.extra.get("product_family") or manifest_entry.get("product_family") or ""
                )
                if str(chunk_family).lower() not in allowed:
                    return False
        return True

    def _tokenize(self, text: str) -> list[str]:
        text = text.lower()
        tokens = re.split(r"[^a-z0-9]+", text)
        return [t for t in tokens if t and (len(t) > 1 or t.isdigit())]

    def _build_lexical_index(self) -> None:
        tokens_per_doc: list[list[str]] = []
        df: dict[str, int] = {}
        lengths: list[int] = []
        for chunk in self.chunks:
            toks = self._tokenize(chunk.text)
            tokens_per_doc.append(toks)
            lengths.append(len(toks))
            for tok in set(toks):
                df[tok] = df.get(tok, 0) + 1
        self._lex_tokens = tokens_per_doc
        self._lex_df = df
        self._lex_len = lengths
        self._lex_avgdl = (sum(lengths) / len(lengths)) if lengths else 0.0
        self._lex_ready = True

    def _bm25_scores(self, query: str) -> list[float]:
        if not self._lex_ready or not self._lex_tokens:
            return [0.0] * len(self.chunks)
        q_tokens = self._tokenize(query)
        if not q_tokens:
            return [0.0] * len(self.chunks)
        k1 = 1.5
        b = 0.75
        N = len(self._lex_tokens)
        scores = [0.0] * N
        for i, doc_tokens in enumerate(self._lex_tokens):
            if not doc_tokens:
                continue
            dl = self._lex_len[i]
            tf_counts: dict[str, int] = {}
            for t in doc_tokens:
                tf_counts[t] = tf_counts.get(t, 0) + 1
            s = 0.0
            for qt in q_tokens:
                df = self._lex_df.get(qt, 0)
                if df == 0:
                    continue
                idf = math.log((N - df + 0.5) / (df + 0.5) + 1.0)
                tf = tf_counts.get(qt, 0)
                if tf == 0:
                    continue
                denom = tf + k1 * (1 - b + b * (dl / (self._lex_avgdl or 1.0)))
                s += idf * (tf * (k1 + 1)) / denom
            scores[i] = s
        return scores

    def _rerank_results(self, results: list[SearchResult]) -> list[SearchResult]:
        if not results:
            return results
        vector_weight = 0.55
        lexical_weight = 0.25
        fuzz_weight = 0.20
        reranked = sorted(
            results,
            key=lambda item: (
                vector_weight * item.vector_score
                + lexical_weight * item.lexical_score
                + fuzz_weight * item.fuzz_score
            ),
            reverse=True,
        )
        for item in reranked:
            item.score = (
                vector_weight * item.vector_score
                + lexical_weight * item.lexical_score
                + fuzz_weight * item.fuzz_score
            )
        return reranked

    def search(
        self,
        query: str,
        top_k: int = 10,
        filters: dict[str, str] | None = None,
        hybrid: bool | None = None,
        *,
        mode: RetrievalMode | str | None = None,
    ) -> list[SearchResult]:
        if not self.chunks:
            return []

        retrieval_mode = RetrievalMode.from_inputs(mode, hybrid)
        vector_rows: list[dict[str, Any]] = []
        if retrieval_mode is not RetrievalMode.LEXICAL:
            query_embedding = self.embedding_client.embed_texts([query])
            if not query_embedding:
                return []
            embedding_vector = list(query_embedding[0])

            candidate_limit = max(top_k * 4, top_k)
            vector_rows = self.repository.query_similar_chunks(
                embedding_vector,
                limit=candidate_limit,
                probes=self.settings.pgvector_probes,
            )

        bm25_all = self._bm25_scores(query)
        candidates: dict[str, dict[str, Any]] = (
            {row["chunk_id"]: row for row in vector_rows} if vector_rows else {}
        )

        top_lexical = sorted(range(len(bm25_all)), key=lambda i: bm25_all[i], reverse=True)[
            : max(top_k * 3, 30)
        ]
        for idx in top_lexical:
            chunk_id = self.chunks[idx].chunk_id
            candidates.setdefault(chunk_id, {"chunk_id": chunk_id})

        if not candidates:
            return []

        if retrieval_mode is RetrievalMode.LEXICAL:
            candidate_indices = [idx for idx in top_lexical if idx < len(self.chunks)]
        else:
            candidate_indices = [
                self.chunk_index_map[c_id] for c_id in candidates if c_id in self.chunk_index_map
            ]
        bm25_min = min((bm25_all[i] for i in candidate_indices), default=0.0)
        bm25_max = max((bm25_all[i] for i in candidate_indices), default=0.0)

        def bm25_norm(idx: int) -> float:
            if bm25_max <= bm25_min:
                return 0.0
            return (bm25_all[idx] - bm25_min) / (bm25_max - bm25_min)

        # Weighting mirrors historical hybrid blend when reranker disabled
        alpha = 0.7 if self.embedding_client._client is not None else 0.35

        results: list[SearchResult] = []
        for chunk_id, row in candidates.items():
            chunk = self.chunk_lookup.get(chunk_id)
            if chunk is None:
                continue
            if not self._apply_filters(chunk, filters):
                continue
            manifest_entry = self.manifest.documents.get(chunk.source_path, {})
            metadata: dict[str, str] = {"source_type": str(manifest_entry.get("source_type", ""))}
            metadata.update(chunk.extra)
            if "metadata" in row:
                metadata.update(row["metadata"])

            idx = self.chunk_index_map.get(chunk_id, 0)
            lexical_score = bm25_norm(idx)
            fuzz_score = fuzz.partial_ratio(query, chunk.text) / 100.0

            distance = row.get("distance") if row else None
            if retrieval_mode is RetrievalMode.LEXICAL:
                vector_score = 0.0
            elif distance is None:
                vector_score = 0.0
            else:
                vector_score = max(0.0, 1.0 - float(distance))

            if retrieval_mode is RetrievalMode.LEXICAL:
                combined_score = lexical_score
            elif retrieval_mode is RetrievalMode.VECTOR:
                combined_score = vector_score
            else:
                base_score = alpha * vector_score + (1 - alpha) * lexical_score
                if not self.settings.enable_reranker:
                    combined_score = 0.8 * base_score + 0.2 * fuzz_score
                else:
                    combined_score = base_score

            results.append(
                SearchResult(
                    chunk_id=chunk.chunk_id,
                    source_path=chunk.source_path,
                    text=chunk.text,
                    score=combined_score,
                    page_number=chunk.page_number,
                    heading=chunk.section,
                    metadata=metadata,
                    chunk_index=idx,
                    vector_score=vector_score,
                    lexical_score=lexical_score,
                    fuzz_score=fuzz_score,
                )
            )

        if not results:
            return []

        if self.settings.enable_reranker and retrieval_mode is RetrievalMode.HYBRID:
            results = self._rerank_results(results)
        elif retrieval_mode is RetrievalMode.LEXICAL:
            results.sort(
                key=lambda result: (result.lexical_score, result.fuzz_score),
                reverse=True,
            )
        elif retrieval_mode is RetrievalMode.VECTOR:
            results.sort(key=lambda result: result.vector_score, reverse=True)
        else:
            results.sort(key=lambda result: result.score, reverse=True)

        results = results[:top_k]

        log_event(
            self.logger,
            "retrieval_query",
            query=query,
            top_k=top_k,
            results=len(results),
            filters=filters or {},
            mode=retrieval_mode.value,
        )
        return results
