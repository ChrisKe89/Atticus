"""Configuration objects for Atticus."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from ipaddress import ip_network
from pathlib import Path
from typing import Any, Literal, cast
from zoneinfo import ZoneInfo

import yaml
from pydantic import AliasChoices, Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

SECRET_FIELD_NAMES = {
    "database_url",
    "openai_api_key",
    "smtp_user",
    "smtp_pass",
    "smtp_from",
    "smtp_to",
    "smtp_allow_list_raw",
    "contact_email",
    "admin_api_token",
}


EMBEDDING_MODEL_SPECS: dict[str, dict[str, object]] = {
    "text-embedding-3-large": {"dimensions": 3072, "probe_range": (2, 16)},
    "text-embedding-3-small": {"dimensions": 1536, "probe_range": (1, 12)},
    "text-embedding-ada-002": {"dimensions": 1536, "probe_range": (1, 12)},
}


def _fingerprint_secret(value: str | None) -> str | None:
    if not value:
        return None
    return hashlib.sha256(value.encode("utf-8")).hexdigest()[:12]


class AppSettings(BaseSettings):
    """Application configuration sourced from environment variables."""

    content_dir: Path = Field(
        default=Path("content"), validation_alias=AliasChoices("CONTENT_ROOT", "CONTENT_DIR")
    )
    indices_dir: Path = Field(default=Path("indices"), validation_alias="INDICES_DIR")
    logs_path: Path = Field(default=Path("logs/app.jsonl"), validation_alias="LOG_PATH")
    errors_path: Path = Field(default=Path("logs/errors.jsonl"), validation_alias="ERROR_LOG_PATH")
    manifest_path: Path = Field(default=Path("indices/manifest.json"))
    metadata_path: Path = Field(default=Path("indices/index_metadata.json"))
    snapshots_dir: Path = Field(default=Path("indices/snapshots"))
    dictionary_path: Path = Field(default=Path("indices/dictionary.json"), alias="DICTIONARY_PATH")
    database_url: str | None = Field(default=None, alias="DATABASE_URL")
    pgvector_lists: int = Field(default=100, alias="PGVECTOR_LISTS")
    pgvector_probes: int = Field(default=4, alias="PGVECTOR_PROBES")
    pgvector_index_max_dimensions: int = Field(
        default=2000, alias="PGVECTOR_INDEX_MAX_DIMENSIONS", ge=1
    )
    pgvector_index_build_mem_mb: int = Field(
        default=256, alias="PGVECTOR_INDEX_BUILD_MEM_MB", ge=16
    )
    prompt_token_limit: int = Field(default=1500, alias="PROMPT_TOKEN_LIMIT", ge=1)
    answer_token_limit: int = Field(default=1000, alias="ANSWER_TOKEN_LIMIT", ge=1)
    embedding_batch_size: int = Field(default=32, alias="EMBEDDING_BATCH_SIZE", ge=1)
    prompt_token_cost_per_1k: float = Field(default=0.005, alias="PROMPT_COST_PER_1K", ge=0.0)
    answer_token_cost_per_1k: float = Field(default=0.015, alias="ANSWER_COST_PER_1K", ge=0.0)
    chunk_size: int = Field(default=512, ge=64)
    chunk_overlap_ratio: float = Field(default=0.0, ge=0.0, lt=1.0)
    chunk_target_tokens: int = Field(default=512, alias="CHUNK_TARGET_TOKENS")
    chunk_min_tokens: int = Field(default=256, alias="CHUNK_MIN_TOKENS")
    chunk_overlap_tokens_setting: int | None = Field(
        default=None, alias="CHUNK_OVERLAP_TOKENS", ge=0
    )
    max_context_chunks: int = Field(default=10, ge=1)
    enable_reranker: bool = Field(default=False, alias="ENABLE_RERANKER")
    top_k: int = Field(default=20, ge=1)
    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    embed_model: str = Field(default="text-embedding-3-large", alias="EMBED_MODEL")
    embedding_model_version: str = Field(
        default="text-embedding-3-large@2025-01-15",
        alias="EMBEDDING_MODEL_VERSION",
    )
    embed_dimensions: int = Field(default=3072, ge=128)
    generation_model: str = Field(default="gpt-4.1", alias="GEN_MODEL")
    generation_prompt_version: str = Field(default="atticus-v1", alias="GEN_PROMPT_VERSION")
    confidence_threshold: float = Field(default=0.70, alias="CONFIDENCE_THRESHOLD")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="json", alias="LOG_FORMAT")
    verbose_logging: bool = Field(default=False, alias="LOG_VERBOSE")
    trace_logging: bool = Field(default=False, alias="LOG_TRACE")
    timezone: str = Field(default="UTC", alias="TIMEZONE")
    enforce_gateway_boundary: bool = Field(default=True, alias="ENFORCE_GATEWAY_BOUNDARY")
    allow_loopback_requests: bool = Field(default=True, alias="ALLOW_LOOPBACK_REQUESTS")
    require_forwarded_for_header: bool = Field(default=True, alias="REQUIRE_FORWARDED_FOR_HEADER")
    require_https_forward_proto: bool = Field(default=True, alias="REQUIRE_HTTPS_FORWARD_PROTO")
    service_mode: Literal["chat", "admin"] = Field(default="chat", alias="SERVICE_MODE")
    trusted_gateway_subnets_raw: str | list[str] | None = Field(
        default="127.0.0.1/32,::1/128", alias="TRUSTED_GATEWAY_SUBNETS"
    )
    evaluation_runs_dir: Path = Field(default=Path("eval/runs"))
    baseline_path: Path = Field(default=Path("eval/baseline.json"))
    gold_set_path: Path = Field(default=Path("eval/gold_set.csv"))
    eval_regression_threshold: float = Field(default=3.0, alias="EVAL_REGRESSION_THRESHOLD")
    eval_min_ndcg: float = Field(default=0.55, alias="EVAL_MIN_NDCG", ge=0.0, le=1.0)
    eval_min_mrr: float = Field(default=0.50, alias="EVAL_MIN_MRR", ge=0.0, le=1.0)
    evaluation_modes: list[str] = Field(
        default_factory=lambda: ["hybrid", "vector"], alias="EVAL_MODES"
    )
    config_path: Path = Field(default=Path("config.yaml"), alias="CONFIG_PATH")

    # Notification / escalation (from .env)
    contact_email: str | None = Field(default=None, alias="CONTACT_EMAIL")
    smtp_host: str | None = Field(default=None, alias="SMTP_HOST")
    smtp_port: int = Field(default=587, alias="SMTP_PORT")
    smtp_user: str | None = Field(default=None, alias="SMTP_USER")
    smtp_pass: str | None = Field(default=None, alias="SMTP_PASS")
    smtp_from: str | None = Field(default=None, alias="SMTP_FROM")
    smtp_to: str | None = Field(default=None, alias="SMTP_TO")
    smtp_dry_run: bool = Field(
        default=False, validation_alias=AliasChoices("SMTP_DRY_RUN", "EMAIL_SANDBOX")
    )
    smtp_allow_list_raw: str | list[str] | None = Field(default=None, alias="SMTP_ALLOW_LIST")
    rate_limit_requests: int = Field(default=5, alias="RATE_LIMIT_REQUESTS", ge=1)
    rate_limit_window_seconds: int = Field(default=60, alias="RATE_LIMIT_WINDOW_SECONDS", ge=1)
    cors_allowed_origins_raw: str | list[str] | None = Field(default=None, alias="ALLOWED_ORIGINS")
    admin_api_token: str | None = Field(default=None, alias="ADMIN_API_TOKEN")
    secrets_report: dict[str, dict[str, Any]] = Field(
        default_factory=dict, exclude=True, repr=False
    )

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def tzinfo(self) -> ZoneInfo:
        return ZoneInfo(self.timezone)

    @property
    def chunk_overlap_tokens(self) -> int:
        if self.chunk_overlap_tokens_setting is not None:
            return max(0, self.chunk_overlap_tokens_setting)
        return max(0, int(self.chunk_size * self.chunk_overlap_ratio))

    @property
    def evaluation_thresholds(self) -> dict[str, float]:
        return {"nDCG@10": self.eval_min_ndcg, "MRR": self.eval_min_mrr}

    @property
    def trusted_gateway_subnets(self) -> tuple[str, ...]:
        raw = self.trusted_gateway_subnets_raw
        if raw is None:
            return ("127.0.0.1/32", "::1/128")
        if isinstance(raw, str):
            values = [item.strip() for item in raw.split(",") if item.strip()]
        else:
            values = [str(item).strip() for item in raw if str(item).strip()]
        return tuple(values) if values else ("127.0.0.1/32", "::1/128")

    @property
    def trusted_gateway_networks(self) -> tuple[Any, ...]:
        return tuple(ip_network(subnet, strict=False) for subnet in self.trusted_gateway_subnets)

    @property
    def cors_allowed_origins(self) -> tuple[str, ...]:
        raw = self.cors_allowed_origins_raw
        if raw is None:
            return ()
        if isinstance(raw, str):
            values = [item.strip() for item in raw.split(",") if item.strip()]
        else:
            values = [str(item).strip() for item in raw if str(item).strip()]
        return tuple(values)

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

    def smtp_allowlist(self) -> set[str]:
        return {value.lower() for value in self.smtp_allow_list if value}

    @property
    def smtp_allow_list(self) -> list[str]:
        raw = self.smtp_allow_list_raw
        if raw is None:
            return []
        if isinstance(raw, str):
            return [item.strip() for item in raw.split(",") if item.strip()]
        return [str(item).strip() for item in raw if str(item).strip()]

    @field_validator("evaluation_modes", mode="before")
    @classmethod
    def _normalize_modes(cls, value: Any) -> list[str] | Any:
        if isinstance(value, str):
            return [item.strip() for item in value.split(",") if item.strip()]
        return value

    def model_post_init(
        self, __context: Any
    ) -> None:  # pragma: no cover - exercised via settings load
        super().model_post_init(__context)
        if self.pgvector_probes < 1:
            raise ValueError("pgvector_probes must be >= 1")
        spec = EMBEDDING_MODEL_SPECS.get(self.embed_model)
        if spec:
            expected_dimension = cast(int, spec.get("dimensions", self.embed_dimensions))
            env_override = any(
                os.environ.get(name)
                for name in (
                    "EMBED_DIMENSIONS",
                    "EMBED_MODEL",
                )
            )
            if (
                self.openai_api_key or env_override
            ) and self.embed_dimensions != expected_dimension:
                raise ValueError(
                    f"embed_dimensions={self.embed_dimensions} does not match the expected dimension {expected_dimension} for {self.embed_model}"
                )
            probe_range = spec.get("probe_range")
            if isinstance(probe_range, tuple) and len(probe_range) == 2:
                lower_int, upper_int = cast(tuple[int, int], probe_range)
                if not (lower_int <= self.pgvector_probes <= upper_int):
                    raise ValueError(
                        f"pgvector_probes={self.pgvector_probes} is outside the recommended range {probe_range} for {self.embed_model}"
                    )
        if self.pgvector_probes > self.pgvector_lists:
            raise ValueError("pgvector_probes cannot exceed pgvector_lists")
        if self.prompt_token_limit < self.answer_token_limit:
            raise ValueError(
                "PROMPT_TOKEN_LIMIT must be greater than or equal to ANSWER_TOKEN_LIMIT"
            )


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


@dataclass(slots=True)
class _SettingsCache:
    """Mutable holder for cached settings and their provenance."""

    key: tuple[float, float, str] | None = None
    settings: AppSettings | None = None


_SETTINGS_CACHE = _SettingsCache()


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
        for item in value:
            if isinstance(item, str):
                result.append(item)
            else:
                result.extend(_iter_alias_strings(item))
    except TypeError:
        pass
    return result


def _env_variables_fingerprint() -> str:
    keys: set[str] = set()
    for name, field in AppSettings.model_fields.items():
        keys.add(name.upper())
        alias = getattr(field, "alias", None)
        if alias:
            keys.update(_iter_alias_strings(alias))
        validation_alias = getattr(field, "validation_alias", None)
        keys.update(_iter_alias_strings(validation_alias))
    material = "|".join(f"{key}={os.environ.get(key, '')}" for key in sorted(keys))
    return hashlib.sha256(material.encode("utf-8")).hexdigest()


def _parse_env_file(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}

    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("export "):
            line = line[len("export ") :]
        if "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if value and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        values[key] = value
    return values


def _path_metadata(path: Path) -> dict[str, Any]:
    absolute = path if path.is_absolute() else path.resolve()
    metadata = {"path": str(absolute), "exists": absolute.exists()}
    if absolute.exists():
        stat_result = absolute.stat()
        metadata["modified_at"] = datetime.fromtimestamp(stat_result.st_mtime, tz=UTC).isoformat()
        metadata["size_bytes"] = stat_result.st_size
    else:
        metadata["modified_at"] = None
        metadata["size_bytes"] = None
    return metadata


def _serialize_value(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, ZoneInfo):
        return value.key
    if isinstance(value, dict):
        return {str(k): _serialize_value(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_serialize_value(item) for item in value]
    return value


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

    _SETTINGS_CACHE.key = None
    _SETTINGS_CACHE.settings = None


def load_settings() -> AppSettings:
    env_path = (_resolve_env_file() or Path(".env")).resolve()
    env_mtime = env_path.stat().st_mtime if env_path.exists() else -1.0
    env_values = _parse_env_file(env_path)
    env_fingerprint = _env_variables_fingerprint()

    base = AppSettings(
        _env_file=str(env_path),
        _env_file_encoding="utf-8",
    )
    config_path = base.config_path
    config_mtime = config_path.stat().st_mtime if config_path.exists() else -1.0

    cache_key = (env_mtime, config_mtime, env_fingerprint)

    if _SETTINGS_CACHE.key == cache_key and _SETTINGS_CACHE.settings is not None:
        return _SETTINGS_CACHE.settings

    config_data = _load_yaml_config(config_path)

    if config_data:
        updates: dict[str, Any] = {}
        for name, value in config_data.items():
            field = AppSettings.model_fields.get(name)
            if field is None:
                updates[name] = value
                continue

            aliases = {name.upper()}
            aliases.update(_iter_alias_strings(getattr(field, "alias", None)))
            aliases.update(_iter_alias_strings(getattr(field, "validation_alias", None)))

            if any(alias in os.environ for alias in aliases):
                continue
            if any(alias in env_values for alias in aliases):
                continue

            updates[name] = value

        updates.setdefault("config_path", config_path)
        # Rebuild settings with validation so YAML string paths are coerced to Path
        # and other field types are normalized. model_copy(update=...) does not
        # perform validation in pydantic v2, which led to str values lacking
        # Path methods like `.mkdir()`.
        combined: dict[str, Any] = base.model_dump()
        combined.update(updates)
        settings = AppSettings.model_validate(combined)
    else:
        settings = base

    _SETTINGS_CACHE.key = cache_key
    _SETTINGS_CACHE.settings = settings
    return settings


def environment_diagnostics() -> dict[str, Any]:
    """Return sanitized diagnostics for environment configuration resolution."""

    env_path = _resolve_env_file() or Path(".env")
    env_values = _parse_env_file(env_path)

    settings = load_settings()
    config_path = settings.config_path
    config_data = _load_yaml_config(config_path)

    relevant_keys: set[str] = set()
    non_secret_settings: dict[str, Any] = {}
    secrets_report: dict[str, dict[str, Any]] = {}

    for name, field in AppSettings.model_fields.items():
        if name == "secrets_report":
            continue

        aliases = {name.upper()}
        aliases.update(_iter_alias_strings(getattr(field, "alias", None)))
        aliases.update(_iter_alias_strings(getattr(field, "validation_alias", None)))
        relevant_keys.update(aliases)

        env_key = next((key for key in aliases if key in os.environ), None)
        env_file_key = next((key for key in aliases if key in env_values), None)
        config_key = name if name in config_data else None

        if env_key:
            source = f"os.environ:{env_key}"
        elif env_file_key:
            source = f".env:{env_file_key}"
        elif config_key:
            source = f"config.yaml:{config_key}"
        else:
            source = "default"

        value = getattr(settings, name)

        if name in SECRET_FIELD_NAMES:
            fingerprint = _fingerprint_secret(str(value) if value is not None else None)
            secrets_report[name] = {
                "aliases": sorted(aliases),
                "defined": bool(value),
                "fingerprint": fingerprint,
                "source": source,
            }
        else:
            non_secret_settings[name] = {
                "aliases": sorted(aliases),
                "source": source,
                "value": _serialize_value(value),
            }

    settings.secrets_report = secrets_report

    env_override_keys = sorted(key for key in os.environ if key in relevant_keys)
    env_file_override_keys = sorted(key for key in env_values if key in relevant_keys)

    return {
        "generated_at": datetime.now(tz=UTC).isoformat(),
        "environment_fingerprint": _env_variables_fingerprint(),
        "env_file": _path_metadata(env_path),
        "config_file": _path_metadata(config_path),
        "overrides": {
            "environment": env_override_keys,
            ".env": env_file_override_keys,
            "config": sorted(str(key) for key in config_data.keys()),
        },
        "settings": non_secret_settings,
        "secrets": secrets_report,
    }
