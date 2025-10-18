"""Glossary enrichment helpers for inline answer annotations."""

from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Sequence

from core.config import AppSettings

_DIACRITIC_PATTERN = re.compile(r"[\u0300-\u036f]")


def _strip_diacritics(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    return _DIACRITIC_PATTERN.sub("", normalized)


def _normalize_token(value: str) -> str:
    stripped = _strip_diacritics(value)
    return re.sub(r"[^a-z0-9]+", "", stripped.lower())


def _normalize_family(value: str) -> str:
    stripped = _strip_diacritics(value)
    cleaned = re.sub(r"[\s_-]+", " ", stripped.strip())
    return cleaned.upper()


@dataclass(slots=True)
class GlossaryEntry:
    term: str
    definition: str
    synonyms: tuple[str, ...]
    aliases: tuple[str, ...]
    units: tuple[str, ...]
    product_families: tuple[str, ...]
    normalized_aliases: tuple[str, ...]
    normalized_families: tuple[str, ...]

    @property
    def search_terms(self) -> tuple[str, ...]:
        terms: list[str] = [self.term]
        terms.extend(self.synonyms)
        terms.extend(self.aliases)
        terms.extend(self.product_families)
        return tuple({term for term in terms if term})


@dataclass(slots=True)
class GlossaryHit:
    term: str
    definition: str
    aliases: tuple[str, ...]
    units: tuple[str, ...]
    product_families: tuple[str, ...]
    matched_value: str


def _load_dictionary(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []
    if not isinstance(payload, list):
        return []
    entries: list[dict[str, object]] = []
    for item in payload:
        if isinstance(item, dict):
            entries.append(item)
    return entries


def _coerce_str_list(values: object) -> tuple[str, ...]:
    if values is None:
        return tuple()
    if isinstance(values, str):
        parts = [part.strip() for part in values.split(",") if part.strip()]
        return tuple(parts)
    if isinstance(values, Iterable):
        result: list[str] = []
        for item in values:
            if isinstance(item, str):
                trimmed = item.strip()
                if trimmed:
                    result.append(trimmed)
        return tuple(result)
    return tuple()


@lru_cache(maxsize=16)
def _load_entries_from_path(path: str) -> tuple[GlossaryEntry, ...]:
    raw_entries = _load_dictionary(Path(path))
    entries: list[GlossaryEntry] = []
    for item in raw_entries:
        term = str(item.get("term", "")).strip()
        definition = str(item.get("definition", "")).strip()
        if not term or not definition:
            continue
        synonyms = _coerce_str_list(item.get("synonyms"))
        aliases = _coerce_str_list(item.get("aliases"))
        units = _coerce_str_list(item.get("units"))
        product_families = _coerce_str_list(
            item.get("productFamilies") or item.get("product_families")
        )
        existing_normalized_aliases = _coerce_str_list(item.get("normalizedAliases"))
        normalized_aliases = tuple(
            {token for source in (term, *synonyms, *aliases) if (token := _normalize_token(source))}
            | {token for token in existing_normalized_aliases if token}
        )
        existing_normalized_families = _coerce_str_list(item.get("normalizedFamilies"))
        normalized_families = tuple(
            {
                _normalize_family(value)
                for value in (*product_families, *existing_normalized_families)
                if value
            }
        )
        entries.append(
            GlossaryEntry(
                term=term,
                definition=definition,
                synonyms=synonyms,
                aliases=aliases,
                units=units,
                product_families=product_families,
                normalized_aliases=normalized_aliases,
                normalized_families=normalized_families,
            )
        )
    return tuple(entries)


def load_glossary_entries(settings: AppSettings | object) -> tuple[GlossaryEntry, ...]:
    dictionary_path = getattr(settings, "dictionary_path", None)
    if dictionary_path is None:
        return tuple()
    path = Path(dictionary_path)
    return _load_entries_from_path(str(path.resolve()))


# Expose cache controls for tests.
load_glossary_entries.cache_clear = _load_entries_from_path.cache_clear  # type: ignore[attr-defined]


def find_glossary_hits(
    *,
    answer: str,
    question: str | None,
    entries: Sequence[GlossaryEntry],
) -> list[GlossaryHit]:
    haystack_parts = [answer or ""]
    if question:
        haystack_parts.append(question)
    haystack = " \n".join(haystack_parts)
    if not haystack.strip():
        return []
    normalized_haystack = _normalize_token(haystack)
    hits: list[GlossaryHit] = []
    seen_terms: set[str] = set()
    for entry in entries:
        if entry.term in seen_terms:
            continue
        matched_value: str | None = None
        for candidate in entry.search_terms:
            if not candidate:
                continue
            pattern = re.compile(rf"(?<!\w){re.escape(candidate)}(?!\w)", re.IGNORECASE)
            match = pattern.search(haystack)
            if match:
                matched_value = match.group(0)
                break
        if not matched_value and entry.normalized_aliases:
            for token in entry.normalized_aliases:
                if token and token in normalized_haystack:
                    matched_value = entry.term
                    break
        if not matched_value and entry.normalized_families:
            for family in entry.normalized_families:
                if family and family in _normalize_family(haystack):
                    matched_value = entry.term
                    break
        if matched_value:
            seen_terms.add(entry.term)
            hits.append(
                GlossaryHit(
                    term=entry.term,
                    definition=entry.definition,
                    aliases=entry.aliases,
                    units=entry.units,
                    product_families=entry.product_families,
                    matched_value=matched_value,
                )
            )
    return hits
