"""High-level question answering orchestration."""

from __future__ import annotations

import logging
import re

from atticus.logging import configure_logging, log_event
from core.config import AppSettings, load_settings

from .answer_format import format_answer_markdown
from .citation_utils import dedupe_citations
from .generator import GeneratorClient
from .models import Answer, Citation
from .vector_store import RetrievalMode, SearchResult, VectorStore


def _normalize_model_code(value: str | None) -> str | None:
    if not value:
        return None
    match = re.search(r"C\d{3,5}", value.upper())
    if match:
        return match.group(0)
    return None


def _expand_ampv_value(raw: str) -> str:
    token = raw.strip()
    match = re.fullmatch(r"(\d+(?:\.\d+)?)([KkMm])", token)
    if not match:
        return token
    number = float(match.group(1))
    multiplier = 1000 if match.group(2).lower() == "k" else 1_000_000
    expanded = number * multiplier
    if expanded.is_integer():
        return f"{int(expanded):,}"
    return f"{expanded:,.0f}"


def _summarise_ampv_chunk(
    text: str,
    *,
    target_codes: set[str],
    include_minimum: bool = True,
) -> str | None:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return None

    codes: list[str] = []
    idx = 0
    while idx < len(lines):
        if re.fullmatch(r"C\d{3,5}", lines[idx].upper()):
            while idx < len(lines) and re.fullmatch(r"C\d{3,5}", lines[idx].upper()):
                codes.append(lines[idx].upper())
                idx += 1
            break
        idx += 1

    if not codes:
        return None

    metrics: dict[str, dict[str, str]] = {code: {} for code in codes}
    metric_keys = {
        "minimum ampv": "minimum",
        "designed ampv": "designed",
        "maximum ampv": "maximum",
    }

    i = 0
    while i < len(lines):
        lower = lines[i].lower()
        for pattern, key in metric_keys.items():
            if pattern in lower:
                values: list[str] = []
                for offset in range(1, len(codes) + 1):
                    pos = i + offset
                    if pos < len(lines):
                        values.append(lines[pos])
                if len(values) == len(codes):
                    for code, value in zip(codes, values):
                        metrics.setdefault(code.upper(), {})[key] = value
                break
        i += 1

    ordered_targets = list(target_codes) if target_codes else codes
    for code in ordered_targets:
        info = metrics.get(code.upper())
        if not info:
            continue
        segments: list[str] = []
        if include_minimum and info.get("minimum"):
            segments.append(f"Minimum AMPV { _expand_ampv_value(info['minimum']) } A4 equivalent impressions")
        if info.get("designed"):
            segments.append(f"Designed AMPV { _expand_ampv_value(info['designed']) } A4 equivalent impressions")
        if info.get("maximum"):
            segments.append(f"Maximum AMPV { _expand_ampv_value(info['maximum']) } A4 equivalent impressions")
        if segments:
            return f"{code}: " + "; ".join(segments)
    return None


def _ampv_hint(
    question: str,
    results: list[SearchResult],
    *,
    product_family: str | None,
    model: str | None,
) -> str | None:
    lower_question = question.lower()
    if "ampv" not in lower_question and "apmv" not in lower_question:
        return None

    target_codes: set[str] = set()
    code_from_model = _normalize_model_code(model)
    if code_from_model:
        target_codes.add(code_from_model)
    code_from_family = _normalize_model_code(product_family)
    if code_from_family:
        target_codes.add(code_from_family)

    for result in results:
        summary = _summarise_ampv_chunk(result.text, target_codes=target_codes)
        if not summary:
            continue
        family_label = result.metadata.get("product_family_label") or result.metadata.get("product_family")
        if family_label:
            label = str(family_label).strip()
            if label and not summary.startswith(label):
                return f"{label}: {summary}"
        return summary
    return None


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
    ampv_context = _ampv_hint(
        question,
        results,
        product_family=product_family,
        model=model,
    )
    if ampv_context:
        contexts.insert(0, ampv_context)
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
