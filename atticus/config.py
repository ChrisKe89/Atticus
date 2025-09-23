"""Configuration objects for Atticus."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

import yaml
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


def _fingerprint_secret(value: str | None) -> str | None:
    if not value:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


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
    chunk_target_tokens: int = Field(default=512, alias="CHUNK_TARGET_TOKENS")
    chunk_min_tokens: int = Field(default=256, alias="CHUNK_MIN_TOKENS")
    chunk_overlap_tokens_setting: int = Field(default=100, alias="CHUNK_OVERLAP_TOKENS")
    max_context_chunks: int = Field(default=10, ge=1)
    top_k: int = Field(default=20, ge=1)
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    embed_model: str = Field(default="text-embedding-3-large", alias="EMBED_MODEL")
    embedding_model_version: str = Field(
        default="text-embedding-3-large@2025-01-15",
        alias="EMBEDDING_MODEL_VERSION",
    )
    embed_dimensions: int = Field(default=3072, ge=128)
    generation_model: str = Field(default="gpt-4.1", alias="GEN_MODEL")
    confidence_threshold: float = Field(default=0.70, alias="CONFIDENCE_THRESHOLD")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    verbose_logging: bool = Field(default=False, alias="LOG_VERBOSE")
    trace_logging: bool = Field(default=False, alias="LOG_TRACE")
    timezone: str = Field(default="UTC", alias="TIMEZONE")
    evaluation_runs_dir: Path = Field(default=Path("eval/runs"))
    baseline_path: Path = Field(default=Path("eval/baseline.json"))
    gold_set_path: Path = Field(default=Path("eval/gold_set.csv"))
    eval_regression_threshold: float = Field(default=3.0, alias="EVAL_REGRESSION_THRESHOLD")
    config_path: Path = Field(default=Path("config.yaml"), alias="CONFIG_PATH")

    # Notification / escalation (from .env)
    contact_email: str | None = Field(default=None, alias="CONTACT_EMAIL")
    smtp_host: str | None = Field(default=None, alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_user: str | None = Field(default=None, alias="SMTP_USER")
    smtp_pass: str | None = Field(default=None, alias="SMTP_PASS")
    smtp_from: str | None = Field(default=None, alias="SMTP_FROM")
    smtp_to: str | None = Field(default=None, alias="SMTP_TO")
    secrets_report: dict[str, dict[str, Any]] = Field(
        default_factory=dict, exclude=True, repr=False
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def tzinfo(self) -> ZoneInfo:
        return ZoneInfo(self.timezone)

    @property
    def chunk_overlap_tokens(self) -> int:
        if self.chunk_overlap_tokens_setting:
            return max(1, self.chunk_overlap_tokens_setting)
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
    embedding_model_version: str
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
            "embedding_model_version": self.embedding_model_version,
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
        embedding_model_version=data.get("embedding_model_version", "unknown"),
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
    path.write_text(
        json.dumps(manifest.to_dict(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )


def _load_yaml_config(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        return {str(key): value for key, value in data.items()}
    raise ValueError(f"Configuration file {path} must contain a mapping")


_SETTINGS_CACHE: tuple[tuple[float, float, str], AppSettings] | None = None


def _iter_alias_strings(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    choices = getattr(value, "choices", None)
    if choices is not None:
        return [str(item) for item in choices]
    result: list[str] = []
    try:
        for item in value:  # type: ignore[assignment]
            if isinstance(item, str):
                result.append(item)
            else:
                result.extend(_iter_alias_strings(item))
    except TypeError:
        pass
    return result


def _env_variables_fingerprint() -> str:
    for name, field in AppSettings.model_fields.items():
        keys.add(name.upper())
        alias = getattr(field, "alias", None)
        if alias:
            keys.update(_iter_alias_strings(alias))
        validation_alias = getattr(field, "validation_alias", None)
        keys.update(_iter_alias_strings(validation_alias))
    material = "|".join(f"{key}={os.environ.get(key, '')}" for key in sorted(keys))
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _resolve_env_file() -> Path | None:
    env_file = AppSettings.model_config.get("env_file")
    if isinstance(env_file, (list, tuple)):
        if not env_file:
            return None
        first = env_file[0]
        return Path(str(first))
    if isinstance(env_file, str):
        return Path(env_file)
    return None


def reset_settings_cache() -> None:
    """Clear the cached settings instance (primarily for tests)."""

    global _SETTINGS_CACHE
    _SETTINGS_CACHE = None


def load_settings() -> AppSettings:
    env_path = _resolve_env_file() or Path(".env")
    env_mtime = env_path.stat().st_mtime if env_path.exists() else -1.0
    env_fingerprint = _env_variables_fingerprint()

    base = AppSettings()
    config_path = base.config_path
    config_mtime = config_path.stat().st_mtime if config_path.exists() else -1.0

    cache_key = (env_mtime, config_mtime, env_fingerprint)

    global _SETTINGS_CACHE
    if _SETTINGS_CACHE and _SETTINGS_CACHE[0] == cache_key:
        return _SETTINGS_CACHE[1]

    config_data = _load_yaml_config(config_path)
    if config_data:
        merged: dict[str, Any] = base.model_dump()
        merged.update(config_data)
        settings = AppSettings(**merged)
    else:
        settings = base
