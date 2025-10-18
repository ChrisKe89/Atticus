"""Utilities for decomposing multi-model questions before retrieval."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Iterable, Sequence

from core.config import AppSettings

from .models import Answer
from .resolver import ModelScope
from .service import answer_question

_MODEL_CODE_PATTERN = re.compile(r"\bC\d{4,5}\b", re.IGNORECASE)


@dataclass(slots=True)
class SplitQuery:
    """A specialised query targeted at a single model scope."""

    prompt: str
    scope: ModelScope


@dataclass(slots=True)
class QueryAnswer:
    """Answer payload paired with the originating scope."""

    scope: ModelScope
    answer: Answer


def _normalize_code(value: str) -> str:
    return value.strip().upper()


def detect_model_codes(question: str) -> list[str]:
    """Return distinct FUJIFILM-style model codes mentioned in the question."""

    codes: set[str] = set()
    for match in _MODEL_CODE_PATTERN.finditer(question):
        codes.add(_normalize_code(match.group(0)))
    return sorted(codes)


def _format_focus(scope: ModelScope) -> str:
    if scope.model:
        return scope.model
    if scope.family_label:
        return scope.family_label
    if scope.family_id:
        return scope.family_id
    return "this model family"


def split_question(question: str, scopes: Sequence[ModelScope]) -> list[SplitQuery]:
    """Generate targeted prompts for each model scope when needed."""

    if not scopes:
        raise ValueError("split_question requires at least one scope")

    distinct_families = {scope.family_id for scope in scopes if scope.family_id}
    mentioned_codes = detect_model_codes(question)

    # Only split when more than one family/model is in play.
    should_split = len(scopes) > 1 or len(distinct_families) > 1 or len(mentioned_codes) > 1
    if not should_split:
        return [SplitQuery(prompt=question, scope=scopes[0])]

    split_queries: list[SplitQuery] = []
    for scope in scopes:
        focus = _format_focus(scope)
        focus_clause = f"Focus only on information relevant to {focus}."
        prompt = f"{question}\n\n{focus_clause}"
        split_queries.append(SplitQuery(prompt=prompt, scope=scope))
    return split_queries


def run_rag_for_each(
    question: str,
    scopes: Sequence[ModelScope],
    *,
    settings: AppSettings,
    logger: logging.Logger,
    filters: dict[str, str] | None = None,
    top_k: int | None = None,
    context_hints: Iterable[str] | None = None,
) -> list[QueryAnswer]:
    """Execute retrieval and generation for each targeted query."""

    base_filters = dict(filters or {})
    split_queries = split_question(question, scopes)
    hints = list(context_hints or [])
    results: list[QueryAnswer] = []

    for split in split_queries:
        scoped_filters = dict(base_filters)
        answer = answer_question(
            split.prompt,
            settings=settings,
            filters=scoped_filters,
            logger=logger,
            top_k=top_k,
            context_hints=hints,
            product_family=split.scope.family_id or None,
            family_label=split.scope.family_label or None,
            model=split.scope.model,
        )
        results.append(QueryAnswer(scope=split.scope, answer=answer))

    return results
