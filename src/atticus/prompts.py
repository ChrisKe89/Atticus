"""Prompt management utilities with hot-reload support."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from threading import RLock


@dataclass(slots=True)
class PromptCache:
    path: Path
    _lock: RLock = field(default_factory=RLock)
    _cache: dict[str, str] = field(default_factory=dict)
    _mtime: float | None = None
    _fingerprint: str | None = None

    def _load(self) -> None:
        with self._lock:
            if not self.path.exists():
                self._cache = {}
                self._mtime = None
                return
            raw = self.path.read_text(encoding="utf-8")
            fingerprint = hashlib.sha256(raw.encode("utf-8")).hexdigest()
            current_mtime = self.path.stat().st_mtime
            if self._fingerprint == fingerprint:
                return
            data = json.loads(raw)
            if not isinstance(data, dict):
                raise ValueError(f"Prompt store {self.path} must be a JSON object")
            cache: dict[str, str] = {}
            for key, value in data.items():
                if not isinstance(key, str) or not isinstance(value, str):
                    raise ValueError("Prompt store keys and values must be strings")
                cache[key] = value
            self._cache = cache
            self._mtime = current_mtime
            self._fingerprint = fingerprint

    def get(self, name: str) -> str:
        self._load()
        if name not in self._cache:
            raise KeyError(f"Prompt '{name}' not found in {self.path}")
        return self._cache[name]

    def list(self) -> list[str]:
        self._load()
        return sorted(self._cache)


class PromptService:
    """Provide cached access to named prompts backed by a JSON store."""

    def __init__(self, path: Path) -> None:
        self._cache = PromptCache(path=path)

    def get_prompt(self, name: str) -> str:
        return self._cache.get(name)

    def available_prompts(self) -> list[str]:
        return self._cache.list()
