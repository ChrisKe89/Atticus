"""Service layer for answering questions via retrieval and generation."""

from __future__ import annotations

import logging
import os
import re
from collections.abc import Sequence

from atticus.config import AppSettings, load_settings
from atticus.logging import configure_logging, log_event

from .generator import GeneratorClient
from .models import Answer, Citation
from .vector_store import SearchResult, VectorStore


def _format_contexts(results: Sequence[SearchResult], limit: int) -> tuple[list[str], list[Citation]]:
    contexts: list[str] = []
    citations: list[Citation] = []
    for result in list(results)[:limit]:
        descriptor = result.source_path
        if result.page_number:
            descriptor += f" (page {result.page_number})"
        contexts.append(f"{descriptor}\n{result.text}")
        citations.append(
            Citation(
                chunk_id=result.chunk_id,
                source_path=result.source_path,
                page_number=result.page_number,
                heading=result.heading,
                score=round(result.score, 4),
            )
        )
    return contexts, citations


LLM_CONF_SWITCH = 0.80
SUMMARY_SENTENCE_LIMIT = 2
MAX_BULLETS = 3


def _split_sentences(text: str) -> list[str]:
    tokens = [token.strip() for token in re.split(r"(?<=[.!?])\s+", text) if token.strip()]
    return tokens or [text.strip()]


def _normalise_sentence(text: str) -> str:
    stripped = text.strip()
    if not stripped:
        return ""
    if stripped[-1] not in {".", "!", "?"}:
        stripped = f"{stripped}."
    return stripped


def _structure_answer(text: str) -> tuple[str, list[str]]:
    """Return a concise summary (1-2 sentences) and optional bullet list."""

    cleaned = (text or "").strip()
    if not cleaned:
        return "", []

    lines = [line.strip() for line in cleaned.splitlines() if line.strip()]
    bullets: list[str] = []
    narrative_lines: list[str] = []
    bullet_markers = ("- ", "* ", "•", "• ")
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith(bullet_markers):
            bullet = stripped.lstrip("-*• \t").strip()
            if bullet:
                bullets.append(_normalise_sentence(bullet))
            continue
        narrative_lines.append(line)

    summary_source = " ".join(narrative_lines) if narrative_lines else (bullets[0] if bullets else cleaned)
    sentences = _split_sentences(summary_source)
    summary = " ".join(sentences[:SUMMARY_SENTENCE_LIMIT]).strip()
    if summary and summary[-1] not in {".", "!", "?"}:
        summary = f"{summary}."
    if not summary:
        summary = cleaned[:200].strip()

    limited_bullets = [item for item in bullets if item][:MAX_BULLETS]
    return summary, limited_bullets


def estimate_confidence(
    results: Sequence[SearchResult],
    settings: AppSettings,
    llm_confidence: float | None = None,
) -> float:
    """Estimate overall confidence using retrieval and optional LLM scores."""

    head = min(5, settings.max_context_chunks)
    top_scores = [max(0.0, min(1.0, result.score)) for result in list(results)[:head]]
    retrieval_conf = sum(top_scores) / len(top_scores) if top_scores else 0.0
    retrieval_conf = max(0.0, min(1.0, retrieval_conf))

    if llm_confidence is None:
        return round(retrieval_conf, 2)

    w_r, w_l = 0.6, 0.4
    if llm_confidence >= LLM_CONF_SWITCH:
        w_r, w_l = 0.2, 0.8
    combined = w_r * retrieval_conf + w_l * max(0.0, min(1.0, llm_confidence))
    return round(max(0.0, min(1.0, combined)), 2)


def answer_question(
    question: str,
    settings: AppSettings | None = None,
    filters: dict[str, str] | None = None,
    logger: logging.Logger | None = None,
    request_id: str | None = None,
) -> Answer:
    settings = settings or load_settings()
    logger = logger or configure_logging(settings)
    store = VectorStore(settings, logger)
    results = store.search(question, top_k=settings.top_k, filters=filters, hybrid=True)

    if not results:
        response = "I don't have enough information in the current index to answer this."
        summary, bullets = _structure_answer(response)
        confidence = 0.2
        should_escalate = True
        answer = Answer(
            question=question,
            summary=summary,
            bullets=bullets,
            citations=[],
            confidence=confidence,
            should_escalate=should_escalate,
        )
        log_event(
            logger,
            "answer_generated",
            confidence=confidence,
            citations=0,
            escalate=should_escalate,
            request_id=request_id,
        )
        return answer

    contexts, citations = _format_contexts(results, settings.max_context_chunks)
    generator = GeneratorClient(settings, logger)
    citation_texts = []
    for item in citations:
        descriptor = item.source_path
        if item.page_number is not None:
            descriptor += f" (page {item.page_number})"
        if item.heading:
            descriptor += f" — {item.heading}"
        citation_texts.append(descriptor)

    response = generator.generate(question, contexts, citation_texts)
    summary, bullets = _structure_answer(response)

    llm_conf = generator.heuristic_confidence(response)
    confidence = estimate_confidence(results, settings, llm_confidence=llm_conf)
    should_escalate = confidence < settings.confidence_threshold
    if os.getenv("FORCE_LOW_CONFIDENCE") == "1":
        confidence = max(0.0, min(settings.confidence_threshold - 0.1, confidence))
        should_escalate = True

    answer = Answer(
        question=question,
        summary=summary,
        bullets=bullets,
        citations=citations[:MAX_BULLETS],
        confidence=confidence,
        should_escalate=should_escalate,
    )

    log_event(
        logger,
        "answer_generated",
        confidence=confidence,
        citations=len(answer.citations),
        escalate=should_escalate,
        request_id=request_id,
    )
    return answer
