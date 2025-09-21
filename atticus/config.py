"""Configuration for the Atticus pipeline."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


@dataclass(slots=True)
class Settings:
    """Runtime configuration for ingestion, indexing, and evaluation."""

    chunk_size: int = 512
    chunk_overlap: float = 0.2
    content_root: Path = Path("content")
    index_path: Path = Path("indexes/atticus_index.json")
    snapshot_dir: Path = Path("indexes/snapshots")
    log_path: Path = Path("logs/app.jsonl")
    embedding_model: str = "text-embedding-3-large"
    embedding_dimension: int = 3072
    llm_model: str = "gpt-4.1"
    timezone: timezone = field(default=timezone.utc)

    def overlap_tokens(self) -> int:
        """Return the number of tokens to overlap between adjacent chunks."""
        return int(self.chunk_size * self.chunk_overlap)

    def timestamp(self) -> str:
        """Return an ISO8601 timestamp in the configured timezone."""
        return datetime.now(self.timezone).isoformat()

    def next_snapshot_path(self) -> Path:
        """Return a snapshot path for the current timestamp."""
        stamp = datetime.now(self.timezone).strftime("%Y%m%dT%H%M%SZ")
        return self.snapshot_dir / f"index_{stamp}.json"
