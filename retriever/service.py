"""High-level question answering orchestration."""

from __future__ import annotations

import logging

from atticus.config import AppSettings, load_settings
from atticus.logging import configure_logging, log_event

from .generator import GeneratorClient
from .models import Answer, Citation
from .vector_store import SearchResult, VectorStore


def _format_contexts(results: list[SearchResult], limit: int) -> tuple[list[str], list[Citation]]:
    contexts: list[str] = []
    citations: list[Citation] = []
    for result in results[:limit]:
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


def answer_question(
    question: str,
    settings: AppSettings | None = None,
    filters: dict[str, str] | None = None,
    logger: logging.Logger | None = None,
) -> Answer:
    settings = settings or load_settings()
    logger = logger or configure_logging(settings)
    store = VectorStore(settings, logger)
    results = store.search(question, top_k=settings.top_k, filters=filters, hybrid=True)

    if not results:
        response = "I don't have enough information in the current index to answer this."
        confidence = 0.2
        should_escalate = True
        answer = Answer(
            question=question,
            response=response,
            citations=[],
            confidence=confidence,
            should_escalate=should_escalate,
        )
        log_event(
            logger, "answer_generated", confidence=confidence, citations=0, escalate=should_escalate
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

    top_scores = [
        max(0.0, min(1.0, result.score)) for result in results[: settings.max_context_chunks]
    ]
    retrieval_conf = sum(top_scores) / len(top_scores) if top_scores else 0.0
    llm_conf = generator.heuristic_confidence(response)
    confidence = round(0.6 * retrieval_conf + 0.4 * llm_conf, 2)
    should_escalate = confidence < settings.confidence_threshold

    answer = Answer(
        question=question,
        response=response,
        citations=citations,
        confidence=confidence,
        should_escalate=should_escalate,
    )

    log_event(
        logger,
        "answer_generated",
        confidence=confidence,
        citations=len(citations),
        escalate=should_escalate,
    )
    return answer
