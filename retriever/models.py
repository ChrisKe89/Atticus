"""Data models and catalog utilities for retrieval."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable

from atticus.config import load_settings


@dataclass(slots=True)
class Citation:
    chunk_id: str
    source_path: str
    page_number: int | None
    heading: str | None
    score: float


@dataclass(slots=True)
class Answer:
    question: str
    response: str
    citations: list[Citation]
    confidence: float
    should_escalate: bool
    model: str | None = None
    family: str | None = None
    family_label: str | None = None


@dataclass(frozen=True, slots=True)
class FamilyOption:
    """Selectable family used for clarifications."""

    id: str
    label: str


@dataclass(frozen=True, slots=True)
class ModelIdentifier:
    canonical: str
    family_id: str
    family_label: str


@dataclass(slots=True)
class FamilyCatalogEntry:
    id: str
    label: str
    aliases: set[str]
    models: dict[str, ModelIdentifier]


@dataclass(slots=True)
class ModelCatalog:
    families: dict[str, FamilyCatalogEntry]
    ordered_families: list[FamilyCatalogEntry]
    alias_to_model: dict[str, ModelIdentifier]
    compact_alias_to_model: dict[str, ModelIdentifier]
    family_alias_to_id: dict[str, FamilyOption]
    compact_family_alias_to_id: dict[str, FamilyOption]

    def match_model(self, raw: str) -> ModelIdentifier | None:
        norm = _normalize(raw)
        if norm in self.alias_to_model:
            return self.alias_to_model[norm]
        compact = _compact(raw)
        return self.compact_alias_to_model.get(compact)

    def match_family(self, raw: str) -> FamilyOption | None:
        norm = _normalize(raw)
        if norm in self.family_alias_to_id:
            return self.family_alias_to_id[norm]
        compact = _compact(raw)
        return self.compact_family_alias_to_id.get(compact)

    def family_options(self) -> list[FamilyOption]:
        return [FamilyOption(entry.id, entry.label) for entry in self.ordered_families]


@dataclass(slots=True)
class ModelExtraction:
    models: set[str]
    families: set[str]
    confidence: float


STRICT_MODEL_PATTERN = re.compile(r"\bapeos\s+c\s*(\d{4})\b", re.IGNORECASE)


def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def _compact(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", value.lower()).strip()


def _load_catalog_path(path: str | Path | None = None) -> Path:
    if path is not None:
        return Path(path)
    settings = load_settings()
    return (settings.indices_dir / "model_catalog.json").resolve()


def _load_catalog_json(path: Path) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Model catalog not found at {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _entry_aliases(raw_aliases: Iterable[str], canonical: str) -> set[str]:
    aliases = {canonical}
    aliases.update(raw_aliases)
    normalized: set[str] = set()
    for alias in aliases:
        alias = alias.strip()
        if not alias:
            continue
        normalized.add(alias)
        compact = _compact(alias)
        # Ensure we have single-token shorthand for values such as "Apeos C 7070"
        if len(compact) > 3:
            normalized.add(compact.upper())
    return normalized


@lru_cache(maxsize=2)
def load_model_catalog(path: str | Path | None = None) -> ModelCatalog:
    catalog_path = _load_catalog_path(path)
    payload = _load_catalog_json(catalog_path)
    families: dict[str, FamilyCatalogEntry] = {}
    ordered: list[FamilyCatalogEntry] = []
    alias_to_model: dict[str, ModelIdentifier] = {}
    compact_alias_to_model: dict[str, ModelIdentifier] = {}
    family_alias_to_id: dict[str, FamilyOption] = {}
    compact_family_alias_to_id: dict[str, FamilyOption] = {}

    for entry in payload.get("families", []):
        family_id = str(entry.get("id", "")).strip()
        label = str(entry.get("label", "")).strip() or family_id
        if not family_id:
            continue
        aliases_raw = entry.get("aliases", []) or []
        family_option = FamilyOption(family_id, label)
        entry_aliases = {_normalize(alias) for alias in aliases_raw if alias}
        entry_aliases.add(_normalize(label))
        entry_aliases.add(_normalize(family_id))
        compact_aliases = {_compact(alias) for alias in aliases_raw if alias}
        compact_aliases.add(_compact(label))
        compact_aliases.add(_compact(family_id))

        family_alias_to_id.update({alias: family_option for alias in entry_aliases if alias})
        compact_family_alias_to_id.update(
            {alias: family_option for alias in compact_aliases if alias}
        )

        models_map: dict[str, ModelIdentifier] = {}
        for model_entry in entry.get("models", []):
            canonical = str(model_entry.get("canonical", "")).strip()
            if not canonical:
                continue
            identifier = ModelIdentifier(canonical=canonical, family_id=family_id, family_label=label)
            aliases = _entry_aliases(model_entry.get("aliases", []) or [], canonical)
            for alias in aliases:
                normalized_alias = _normalize(alias)
                if normalized_alias:
                    alias_to_model.setdefault(normalized_alias, identifier)
                compact_alias = _compact(alias)
                if compact_alias:
                    compact_alias_to_model.setdefault(compact_alias, identifier)
            models_map[canonical] = identifier

        family_entry = FamilyCatalogEntry(
            id=family_id,
            label=label,
            aliases={_normalize(alias) for alias in aliases_raw if alias},
            models=models_map,
        )
        families[family_id] = family_entry
        ordered.append(family_entry)

    return ModelCatalog(
        families=families,
        ordered_families=ordered,
        alias_to_model=alias_to_model,
        compact_alias_to_model=compact_alias_to_model,
        family_alias_to_id=family_alias_to_id,
        compact_family_alias_to_id=compact_family_alias_to_id,
    )


def extract_models(question: str, catalog: ModelCatalog | None = None) -> ModelExtraction:
    """Extract explicit model or family references from a question."""

    catalog = catalog or load_model_catalog()
    normalized_question = _normalize(question)
    compact_question = _compact(question)
    tokens = set(normalized_question.split())

    models: set[str] = set()
    families: set[str] = set()
    confidences: list[float] = []

    for match in STRICT_MODEL_PATTERN.finditer(question):
        series = match.group(1)
        candidate = f"Apeos C{series}"
        identifier = catalog.match_model(candidate)
        if identifier:
            models.add(identifier.canonical)
            families.add(identifier.family_id)
            confidences.append(0.95)

    matched_aliases: set[str] = set()

    for alias, identifier in catalog.alias_to_model.items():
        if alias in matched_aliases:
            continue
        if " " in alias:
            padded = f" {alias} "
            if padded in f" {normalized_question} ":
                models.add(identifier.canonical)
                families.add(identifier.family_id)
                confidences.append(0.85)
                matched_aliases.add(alias)
        elif alias in tokens:
            models.add(identifier.canonical)
            families.add(identifier.family_id)
            confidences.append(0.8)
            matched_aliases.add(alias)
        else:
            compact_alias = _compact(alias)
            if compact_alias and compact_alias in compact_question:
                models.add(identifier.canonical)
                families.add(identifier.family_id)
                confidences.append(0.75)
                matched_aliases.add(alias)

    for alias, option in catalog.family_alias_to_id.items():
        if alias in matched_aliases:
            continue
        if " " in alias:
            if f" {alias} " in f" {normalized_question} ":
                families.add(option.id)
                confidences.append(0.7)
        elif alias in tokens:
            families.add(option.id)
            confidences.append(0.65)
        else:
            compact_alias = _compact(alias)
            if compact_alias and compact_alias in compact_question:
                families.add(option.id)
                confidences.append(0.6)

    confidence = max(confidences) if confidences else 0.0
    return ModelExtraction(models=models, families=families, confidence=confidence)
