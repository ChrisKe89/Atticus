"""Utilities for resolving model references into retrieval scopes."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Sequence

from .models import (
    FamilyOption,
    ModelCatalog,
    ModelExtraction,
    ModelIdentifier,
    extract_models,
    load_model_catalog,
)


@dataclass(slots=True)
class ModelScope:
    family_id: str
    family_label: str
    model: str | None = None


@dataclass(slots=True)
class ModelResolution:
    scopes: list[ModelScope]
    confidence: float
    needs_clarification: bool
    clarification_options: list[FamilyOption]

    @property
    def families(self) -> set[str]:
        return {scope.family_id for scope in self.scopes if scope.family_id}


def _resolve_explicit_models(
    requested_models: Sequence[str],
    catalog: ModelCatalog,
) -> tuple[list[ModelScope], float]:
    scopes: list[ModelScope] = []
    for raw in requested_models:
        ident: ModelIdentifier | None = catalog.match_model(raw)
        if ident:
            scopes.append(ModelScope(family_id=ident.family_id, family_label=ident.family_label, model=ident.canonical))
            continue
        family = catalog.match_family(raw)
        if family:
            # Avoid duplicate family-only scopes if multiple aliases map to the same family.
            if not any(scope.family_id == family.id and scope.model is None for scope in scopes):
                scopes.append(ModelScope(family_id=family.id, family_label=family.label))
    confidence = 1.0 if scopes else 0.0
    return scopes, confidence


def resolve_models(
    question: str,
    requested_models: Iterable[str] | None = None,
    *,
    catalog: ModelCatalog | None = None,
    clarification_threshold: float = 0.65,
) -> ModelResolution:
    """Resolve models/families mentioned in a question or supplied explicitly."""

    catalog = catalog or load_model_catalog()
    options = catalog.family_options()
    requested: Sequence[str] = list(requested_models or [])

    scopes, confidence = _resolve_explicit_models(requested, catalog)
    if scopes:
        return ModelResolution(
            scopes=scopes,
            confidence=confidence,
            needs_clarification=False,
            clarification_options=options,
        )

    extraction: ModelExtraction = extract_models(question, catalog=catalog)
    scopes = []

    for model_name in sorted(extraction.models):
        ident = catalog.match_model(model_name)
        if not ident:
            continue
        scopes.append(
            ModelScope(
                family_id=ident.family_id,
                family_label=ident.family_label,
                model=ident.canonical,
            )
        )

    missing_families = extraction.families - {scope.family_id for scope in scopes}
    for family_id in sorted(missing_families):
        family_entry = catalog.families.get(family_id)
        if not family_entry:
            continue
        scopes.append(
            ModelScope(
                family_id=family_entry.id,
                family_label=family_entry.label,
            )
        )

    needs_clarification = not scopes and extraction.confidence < clarification_threshold

    return ModelResolution(
        scopes=scopes,
        confidence=extraction.confidence,
        needs_clarification=needs_clarification,
        clarification_options=options,
    )
