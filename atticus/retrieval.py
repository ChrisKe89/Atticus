"""Retrieval utilities for Atticus."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List

import numpy as np

from .config import Settings
from .embedding import EmbeddingClient
from .logging_utils import configure_logging, log_event


@dataclass(slots=True)
class RetrievalResult:
    chunk_id: str
    document_path: str
    score: float
    text: str
    chunk_index: int


class VectorStore:
    """In-memory vector store backed by the persisted index."""

    def __init__(self, entries: List[Dict], settings: Settings) -> None:
        self.settings = settings
        self.entries = entries
        if entries:
            self.matrix = np.array([entry["embedding"] for entry in entries], dtype=np.float32)
        else:
            self.matrix = np.zeros((0, settings.embedding_dimension), dtype=np.float32)

    def query(self, embedding: np.ndarray, top_k: int = 10) -> List[RetrievalResult]:
        if self.matrix.size == 0:
            return []

        norms = np.linalg.norm(self.matrix, axis=1) * (np.linalg.norm(embedding) or 1.0)
        similarities = (self.matrix @ embedding) / np.where(norms == 0, 1.0, norms)
        indices = np.argsort(similarities)[::-1][:top_k]
        results: List[RetrievalResult] = []
        for idx in indices:
            entry = self.entries[int(idx)]
            results.append(
                RetrievalResult(
                    chunk_id=entry["id"],
                    document_path=entry["document_path"],
                    score=float(similarities[int(idx)]),
                    text=entry["text"],
                    chunk_index=int(entry["chunk_index"]),
                )
            )
        return results


def load_index(settings: Settings) -> Dict:
    index_path = Path(settings.index_path)
    if not index_path.exists():
        raise FileNotFoundError(f"Index not found at {index_path}")
    payload = json.loads(index_path.read_text(encoding="utf-8"))
    return payload


def build_vector_store(settings: Settings) -> VectorStore:
    payload = load_index(settings)
    entries = payload.get("entries", [])
    return VectorStore(entries, settings)


def search(query: str, settings: Settings | None = None, top_k: int = 10) -> List[RetrievalResult]:
    settings = settings or Settings()
    logger = configure_logging(settings)
    store = build_vector_store(settings)
    client = EmbeddingClient(settings, logger=logger)
    embedding = np.array(client.embed_texts([query])[0], dtype=np.float32)
    results = store.query(embedding, top_k=top_k)
    log_event(
        logger,
        "retrieval_query",
        query=query,
        top_k=top_k,
        results=len(results),
        embedding_model=client.model_name,
    )
    return results
