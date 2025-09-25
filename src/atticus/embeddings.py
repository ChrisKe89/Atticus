"""Embedding helpers using OpenAI or deterministic fallback."""

from __future__ import annotations

import hashlib
import importlib
import logging
import os
from collections.abc import Iterable
from typing import Any, cast

import numpy as np

from .config import AppSettings


class EmbeddingClient:
    """Provides embeddings with deterministic offline fallback."""

    def __init__(self, settings: AppSettings, logger: logging.Logger | None = None) -> None:
        self.settings = settings
        self.logger = logger or logging.getLogger("atticus")
        self.model_name = settings.embed_model
        self.dimension = settings.embed_dimensions

        # Resolve API key and record source for diagnostics
        source = "none"
        api_key = None
        if getattr(settings, "openai_api_key", None):
            api_key = settings.openai_api_key
            source = "settings"
        elif os.getenv("OPENAI_API_KEY"):
            api_key = os.getenv("OPENAI_API_KEY")
            source = "os.environ"
        self._client: Any | None = None
        if api_key:  # pragma: no cover - requires network
            try:
                openai_module = importlib.import_module("openai")
                openai_class = cast(Any, openai_module).OpenAI
                # Pass the key explicitly so we don't rely on process env
                self._client = openai_class(api_key=api_key)
                # Safe fingerprint (sha256 prefix) for troubleshooting without leaking secrets
                try:
                    fp = hashlib.sha256(str(api_key).encode("utf-8")).hexdigest()[:12]
                except Exception:
                    fp = "unknown"
                self.logger.info(
                    "openai_client_initialized",
                    extra={
                        "extra_payload": {
                            "client": "embeddings",
                            "source": source,
                            "key_fp": fp,
                            "model": self.model_name,
                        }
                    },
                )
            except Exception as exc:  # pragma: no cover - network path
                self.logger.warning(
                    "OpenAI client initialization failed; using fallback embeddings",
                    extra={"extra_payload": {"error": str(exc)}},
                )
        else:
            self.logger.info("Using deterministic embeddings because no OpenAI API key was provided")

    def embed_texts(self, texts: Iterable[str]) -> list[list[float]]:
        payload = list(texts)
        if not payload:
            return []

        if self._client is not None:  # pragma: no cover - requires network
            try:
                response: Any = self._client.embeddings.create(model=self.model_name, input=payload)
                return [list(map(float, item.embedding)) for item in response.data]
            except Exception as exc:
                self.logger.error(
                    "OpenAI embedding request failed; falling back to deterministic embeddings",
                    extra={"extra_payload": {"error": str(exc), "model": self.model_name}},
                )

        return [self._deterministic_embedding(text) for text in payload]

    def _deterministic_embedding(self, text: str) -> list[float]:
        tokens = text.lower().split()
        vector = np.zeros(self.dimension, dtype=np.float32)
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            for index in range(0, len(digest), 4):
                offset = int.from_bytes(digest[index : index + 4], "little") % self.dimension
                vector[offset] += 1.0
        norm = np.linalg.norm(vector)
        if norm:
            vector /= norm
        return vector.astype(np.float32).tolist()
