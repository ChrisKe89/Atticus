"""Unit tests for the multi-model query splitter."""

from __future__ import annotations

import logging

import pytest

from retriever.models import Answer
from retriever.query_splitter import (
    detect_model_codes,
    run_rag_for_each,
    split_question,
)
from retriever.resolver import ModelScope


def test_detect_model_codes_returns_unique_sorted_codes() -> None:
    question = "Compare the Apeos C7070 and c8180 units to the C7070 pro variant."
    codes = detect_model_codes(question)
    assert codes == ["C7070", "C8180"]


def test_split_question_single_scope_returns_original_question() -> None:
    scope = ModelScope(family_id="apeos-c7070", family_label="Apeos C7070", model="Apeos C7070")
    splits = split_question("How fast is the Apeos C7070?", [scope])
    assert len(splits) == 1
    assert splits[0].prompt == "How fast is the Apeos C7070?"


def test_run_rag_for_each_generates_focus_prompts(monkeypatch: pytest.MonkeyPatch) -> None:
    scopes = [
        ModelScope(family_id="apeos-c7070", family_label="Apeos C7070", model="Apeos C7070"),
        ModelScope(family_id="apeos-c8180", family_label="Apeos C8180", model="Apeos C8180"),
    ]
    prompts: list[str] = []

    def fake_answer_question(
        prompt: str,
        *,
        settings,
        filters,
        logger,
        top_k,
        context_hints,
        product_family,
        family_label,
        model,
    ) -> Answer:
        prompts.append(prompt)
        return Answer(
            question=prompt,
            response=f"details for {model}",
            citations=[],
            confidence=0.9,
            should_escalate=False,
            model=model,
            family=product_family,
            family_label=family_label,
        )

    monkeypatch.setattr("retriever.query_splitter.answer_question", fake_answer_question)

    results = run_rag_for_each(
        "Compare the Apeos C7070 vs C8180 toner yields.",
        scopes,
        settings=object(),
        logger=logging.getLogger("test"),
        filters={},
        top_k=None,
        context_hints=[],
    )

    assert len(results) == 2
    assert all(result.answer.confidence == 0.9 for result in results)
    assert any("Apeos C7070" in prompt for prompt in prompts)
    assert any("Apeos C8180" in prompt for prompt in prompts)
    assert all("Focus only on information relevant" in prompt for prompt in prompts)
