"""Embedding utilities for Atticus."""

from __future__ import annotations

import hashlib
import logging
import os
import re
from typing import Iterable, List

import numpy as np

try:  # pragma: no cover - network branch
    from openai import OpenAI
except ImportError:  # pragma: no cover - optional dependency guard
    OpenAI = None  # type: ignore

from .config import Settings


_TOKEN_PATTERN = re.compile(r"\b\w+\b", re.UNICODE)


class EmbeddingClient:
    """Provides embeddings via OpenAI with a deterministic offline fallback."""

    def __init__(self, settings: Settings, logger: logging.Logger | None = None) -> None:
        self.settings = settings
        self.logger = logger or logging.getLogger("atticus")
        self._dimension = settings.embedding_dimension
        self._model_name = settings.embedding_model
        self._client = None

        api_key = os.getenv("OPENAI_API_KEY")
        if api_key and OpenAI is not None:  # pragma: no cover - requires network
            self._client = OpenAI()
        else:
            self.logger.warning(
                "OPENAI_API_KEY not set or OpenAI SDK unavailable; using deterministic fallback embeddings.",
                extra={
                    "extra_payload": {
                        "embedding_model": self._model_name,
                        "mode": "fallback",
                    }
                },
            )

    @property
    def model_name(self) -> str:
        return self._model_name

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_texts(self, texts: Iterable[str]) -> List[List[float]]:
        """Embed a collection of texts."""

        texts = list(texts)
        if not texts:
            return []

        if self._client is not None:  # pragma: no cover - requires network
            try:
                response = self._client.embeddings.create(model=self._model_name, input=texts)
                return [item.embedding for item in response.data]
            except Exception as exc:  # fallback to deterministic embeddings
                self.logger.error(
                    "OpenAI embedding request failed; falling back to deterministic embeddings.",
                    extra={
                        "extra_payload": {
                            "error": str(exc),
                            "embedding_model": self._model_name,
                            "mode": "fallback",
                        }
                    },
                )

        return [self._deterministic_embedding(text) for text in texts]

    # Deterministic fallback ensures reproducibility without external calls.
    def _deterministic_embedding(self, text: str) -> List[float]:
        tokens = _TOKEN_PATTERN.findall(text.lower())
        vector = np.zeros(self._dimension, dtype=np.float32)
        if not tokens:
            return vector.tolist()

        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            for i in range(0, len(digest), 4):
                idx = int.from_bytes(digest[i : i + 4], "little") % self._dimension
                vector[idx] += 1.0

        norm = np.linalg.norm(vector)
        if norm:
            vector /= norm
        return vector.tolist()
