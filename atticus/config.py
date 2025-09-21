"""Configuration objects for Atticus."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from zoneinfo import ZoneInfo


class AppSettings(BaseSettings):
    """Application configuration sourced from environment variables."""

    content_dir: Path = Field(default=Path("content"), validation_alias="CONTENT_ROOT")
    indices_dir: Path = Field(default=Path("indices"), validation_alias="INDICES_DIR")
    logs_path: Path = Field(default=Path("logs/app.jsonl"), validation_alias="LOG_PATH")
    errors_path: Path = Field(default=Path("logs/errors.jsonl"), validation_alias="ERROR_LOG_PATH")
    manifest_path: Path = Field(default=Path("indices/manifest.json"))
    metadata_path: Path = Field(default=Path("indices/index_metadata.json"))
    faiss_index_path: Path = Field(default=Path("indices/index.faiss"))
    snapshots_dir: Path = Field(default=Path("indices/snapshots"))
    dictionary_path: Path = Field(default=Path("indices/dictionary.json"))
    chunk_size: int = Field(default=512, ge=64)
    chunk_overlap_ratio: float = Field(default=0.2, ge=0.0, lt=1.0)
    max_context_chunks: int = Field(default=10, ge=1)
    top_k: int = Field(default=20, ge=1)
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    embed_model: str = Field(default="text-embedding-3-large", alias="EMBED_MODEL")
    embed_dimensions: int = Field(default=3072, ge=128)
    generation_model: str = Field(default="gpt-4.1", alias="GEN_MODEL")
    confidence_threshold: float = Field(default=0.70, alias="CONFIDENCE_THRESHOLD")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    timezone: str = Field(default="UTC", alias="TIMEZONE")
    evaluation_runs_dir: Path = Field(default=Path("eval/runs"))
    baseline_path: Path = Field(default=Path("eval/baseline.json"))
    gold_set_path: Path = Field(default=Path("eval/gold_set.csv"))
    eval_regression_threshold: float = Field(default=3.0, alias="EVAL_REGRESSION_THRESHOLD")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def tzinfo(self) -> ZoneInfo:
        return ZoneInfo(self.timezone)

    @property
    def chunk_overlap_tokens(self) -> int:
        return max(1, int(self.chunk_size * self.chunk_overlap_ratio))

    def ensure_directories(self) -> None:
        for path in [
            self.content_dir,
            self.indices_dir,
            self.logs_path.parent,
            self.snapshots_dir,
            self.evaluation_runs_dir,
        ]:
            path.mkdir(parents=True, exist_ok=True)

    def timestamp(self) -> str:
        return datetime.now(tz=self.tzinfo).isoformat(timespec="seconds")


@dataclass(slots=True)
class Manifest:
    """Represents a stored manifest of the active index."""

    embedding_model: str
    embedding_dimensions: int
    chunk_size: int
    chunk_overlap_ratio: float
    corpus_hash: str
    document_count: int
    chunk_count: int
    created_at: str
    metadata_path: Path
    index_path: Path
    snapshot_path: Path
    documents: dict[str, dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "embedding_model": self.embedding_model,
            "embedding_dimensions": self.embedding_dimensions,
            "chunk_size": self.chunk_size,
            "chunk_overlap_ratio": self.chunk_overlap_ratio,
            "corpus_hash": self.corpus_hash,
            "document_count": self.document_count,
            "chunk_count": self.chunk_count,
            "created_at": self.created_at,
            "metadata_path": str(self.metadata_path),
            "index_path": str(self.index_path),
            "snapshot_path": str(self.snapshot_path),
            "documents": self.documents,
        }


def load_manifest(path: Path) -> Manifest | None:
    if not path.exists():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return Manifest(
        embedding_model=data["embedding_model"],
        embedding_dimensions=int(data["embedding_dimensions"]),
        chunk_size=int(data["chunk_size"]),
        chunk_overlap_ratio=float(data["chunk_overlap_ratio"]),
        corpus_hash=data["corpus_hash"],
        document_count=int(data["document_count"]),
        chunk_count=int(data["chunk_count"]),
        created_at=data["created_at"],
        metadata_path=Path(data["metadata_path"]),
        index_path=Path(data["index_path"]),
        snapshot_path=Path(data["snapshot_path"]),
        documents={key: dict(value) for key, value in data.get("documents", {}).items()},
    )


def write_manifest(path: Path, manifest: Manifest) -> None:
    path.write_text(json.dumps(manifest.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

