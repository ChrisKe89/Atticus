"""Vector retrieval utilities for Atticus."""

from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import faiss
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
    chunk_index: int
    vector_score: float
    lexical_score: float
    fuzz_score: float


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

        # Build lightweight lexical structures for BM25-style fallback
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
        if prefix and not Path(chunk.source_path).as_posix().startswith(prefix):
            return False
        return True

    def _tokenize(self, text: str) -> list[str]:
        # Lowercase, keep alphanumerics, split on non-word, drop 1-char tokens unless digit
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
        # BM25 parameters
        k1 = 1.5
        b = 0.75
        N = len(self._lex_tokens)
        scores = [0.0] * N
        # Precompute term frequencies per doc for query tokens only for speed
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
        """Apply lightweight lexical + semantic re-ranking when enabled."""

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
        hybrid: bool = True,
    ) -> list[SearchResult]:
        if self.index.ntotal == 0:
            return []

        # Vector candidate set
        embedding = np.array(self.embedding_client.embed_texts([query])[0], dtype=np.float32)
        faiss.normalize_L2(embedding.reshape(1, -1))
        vec_scores, vec_indices = self.index.search(
            embedding.reshape(1, -1), min(self.index.ntotal, max(top_k * 4, top_k))
        )

        # Lexical scores for all chunks
        bm25_all = self._bm25_scores(query)

        # Collect candidates from both sources
        candidates: dict[int, float] = {}
        for idx, sc in zip(vec_indices[0], vec_scores[0], strict=False):
            if idx < 0:
                continue
            candidates[int(idx)] = max(candidates.get(int(idx), 0.0), float(sc))
        # Add top lexical candidates as well
        # Rank by BM25 score and take top set
        top_lex = sorted(range(len(bm25_all)), key=lambda i: bm25_all[i], reverse=True)[
            : max(top_k * 3, 30)
        ]
        for i in top_lex:
            candidates[i] = max(candidates.get(i, 0.0), 0.0)  # ensure presence

        # Normalize BM25 scores across candidate set for combination
        bm25_min = min((bm25_all[i] for i in candidates), default=0.0)
        bm25_max = max((bm25_all[i] for i in candidates), default=0.0)

        def bm25_norm(i: int) -> float:
            if bm25_max <= bm25_min:
                return 0.0
            return (bm25_all[i] - bm25_min) / (bm25_max - bm25_min)

        # Weighting: favor lexical more when running offline embeddings
        alpha = 0.7 if self.embedding_client._client is not None else 0.35

        results: list[SearchResult] = []
        for i in candidates.keys():
            chunk = self.chunks[i]
            if not self._apply_filters(chunk, filters):
                continue
            manifest_entry = self.manifest.documents.get(chunk.source_path, {})
            metadata: dict[str, str] = {"source_type": str(manifest_entry.get("source_type", ""))}
            metadata.update(chunk.extra)
            v_emb = np.array(chunk.embedding, dtype=np.float32)
            faiss.normalize_L2(v_emb.reshape(1, -1))
            vector_similarity = float(np.dot(embedding, v_emb))
            vector_score = max(0.0, min(1.0, (vector_similarity + 1.0) / 2.0))
            lexical_score = bm25_norm(i)
            base_score = alpha * vector_score + (1 - alpha) * lexical_score
            fuzz_score = fuzz.partial_ratio(query, chunk.text) / 100.0
            score = base_score
            if hybrid and not self.settings.enable_reranker:
                score = 0.8 * base_score + 0.2 * fuzz_score
            results.append(
                SearchResult(
                    chunk_id=chunk.chunk_id,
                    source_path=chunk.source_path,
                    text=chunk.text,
                    score=score,
                    page_number=chunk.page_number,
                    heading=chunk.section,
                    metadata=metadata,
                    chunk_index=i,
                    vector_score=vector_score,
                    lexical_score=lexical_score,
                    fuzz_score=fuzz_score,
                )
            )

        if self.settings.enable_reranker and results:
            results = self._rerank_results(results)
        elif hybrid and results:
            # Non-reranker flow already applied fuzzy weighting during scoring
            results.sort(key=lambda result: result.score, reverse=True)
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
        )
        return results
