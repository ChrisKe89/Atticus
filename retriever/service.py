"""High-level question answering orchestration."""

from __future__ import annotations

import logging

from atticus.config import AppSettings, load_settings
from atticus.logging import configure_logging, log_event

from .answer_format import format_answer_markdown
from .citation_utils import dedupe_citations
from .generator import GeneratorClient
from .models import Answer, Citation
from .vector_store import RetrievalMode, SearchResult, VectorStore


def _format_contexts(results: list[SearchResult], limit: int) -> tuple[list[str], list[Citation]]:
    contexts: list[str] = []
    citations: list[Citation] = []
    seen: set[tuple[str, int | None]] = set()

    for result in results:
        page_value = result.page_number
        if isinstance(page_value, str):
            try:
                page_key = int(page_value)
            except ValueError:
                page_key = page_value.strip()
        else:
            page_key = page_value

        key = (result.source_path, page_key)
        if key in seen:
            continue

        seen.add(key)
        descriptor = result.source_path
        if page_value:
            descriptor += f" (page {page_value})"
        contexts.append(result.text)
        citations.append(
            Citation(
                chunk_id=result.chunk_id,
                source_path=result.source_path,
                page_number=page_key if isinstance(page_key, int) else result.page_number,
                heading=result.heading,
                score=round(result.score, 4),
            )
        )

        if len(contexts) >= limit:
            break

    return contexts, citations


LLM_CONF_SWITCH = 0.80


def answer_question(
    question: str,
    settings: AppSettings | None = None,
    filters: dict[str, str] | None = None,
    logger: logging.Logger | None = None,
    *,
    top_k: int | None = None,
    context_hints: list[str] | None = None,
    product_family: str | None = None,
    family_label: str | None = None,
    model: str | None = None,
) -> Answer:
    settings = settings or load_settings()
    logger = logger or configure_logging(settings)
    store = VectorStore(settings, logger)
    window = top_k or settings.top_k
    merged_filters = dict(filters or {})
    if product_family:
        merged_filters["product_family"] = product_family
    results = store.search(
        question,
        top_k=window,
        filters=merged_filters,
        mode=RetrievalMode.HYBRID,
    )

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
            model=model,
            family=product_family,
            family_label=family_label,
        )
        log_event(
            logger,
            "answer_generated",
            confidence=confidence,
            citations=0,
            escalate=should_escalate,
            filters=merged_filters,
        )
        return answer

    contexts, citations = _format_contexts(results, settings.max_context_chunks)
    if context_hints:
        contexts.extend(context_hints)
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

    # Emphasize the head of the ranking when computing retrieval confidence
    head = min(5, settings.max_context_chunks)
    top_scores = [max(0.0, min(1.0, result.score)) for result in results[:head]]
    retrieval_conf = sum(top_scores) / len(top_scores) if top_scores else 0.0
    llm_conf = generator.heuristic_confidence(response)
    w_r, w_l = 0.6, 0.4
    if llm_conf >= LLM_CONF_SWITCH:
        w_r, w_l = 0.2, 0.8
    confidence = round(w_r * retrieval_conf + w_l * llm_conf, 2)
    should_escalate = confidence < settings.confidence_threshold

    citations = dedupe_citations(citations)
    formatted_response = format_answer_markdown(response, citations)
    answer = Answer(
        question=question,
        response=formatted_response,
        citations=citations,
        confidence=confidence,
        should_escalate=should_escalate,
        model=model,
        family=product_family,
        family_label=family_label,
    )

    log_event(
        logger,
        "answer_generated",
        confidence=confidence,
        citations=len(citations),
        escalate=should_escalate,
        filters=merged_filters,
    )
    return answer
