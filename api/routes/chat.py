"""Unified chat route returning the canonical ask response contract."""

from __future__ import annotations

import time
from collections.abc import Iterable, Sequence

from fastapi import APIRouter, HTTPException, Request

from atticus.logging import log_event
from atticus.tokenization import count_tokens
from retriever import answer_question
from retriever.resolver import ModelResolution, ModelScope, resolve_models

from ..dependencies import LoggerDep, SettingsDep
from ..schemas import (
    AskAnswer,
    AskRequest,
    AskResponse,
    AskSource,
    ClarificationOption,
    ClarificationPayload,
)

router = APIRouter()
_Q_PLACEHOLDERS = {"string", "test", "example"}
_Q_MIN_LEN = 4
_CLARIFICATION_MESSAGE = (
    "Which model are you referring to? If you like, I can provide a list of product families that I can assist with."
)


def _format_sources(citations: Iterable[AskSource]) -> list[str]:
    sources: list[str] = []
    for citation in citations:
        desc = citation.path
        if citation.page is not None:
            desc += f" (page {citation.page})"
        if citation.heading:
            desc += f" - {citation.heading}"
        sources.append(desc)
    return sources


def _convert_citations(citations) -> list[AskSource]:
    return [
        AskSource(
            chunkId=item.chunk_id,
            path=item.source_path,
            page=item.page_number,
            heading=item.heading,
            score=item.score,
        )
        for item in citations
    ]


def _build_answer_payloads(
    question: str,
    scopes: Sequence[ModelScope],
    payload: AskRequest,
    settings: SettingsDep,
    logger: LoggerDep,
) -> list[AskAnswer]:
    answers: list[AskAnswer] = []
    for scope in scopes:
        filters = dict(payload.filters or {})
        answer = answer_question(
            question,
            settings=settings,
            filters=filters,
            logger=logger,
            top_k=payload.top_k,
            context_hints=payload.context_hints,
            product_family=scope.family_id or None,
            family_label=scope.family_label or None,
            model=scope.model,
        )
        ask_sources = _convert_citations(answer.citations)
        answers.append(
            AskAnswer(
                answer=answer.response,
                confidence=answer.confidence,
                should_escalate=answer.should_escalate,
                model=answer.model,
                family=answer.family,
                family_label=answer.family_label,
                sources=ask_sources,
            )
        )
    return answers


def _aggregate_answer_text(answers: Sequence[AskAnswer]) -> str:
    segments: list[str] = []
    for entry in answers:
        header_parts = [entry.model, entry.family_label or entry.family]
        header = " · ".join(part for part in header_parts if part)
        body = entry.answer.strip()
        if header:
            segments.append(f"### {header}\n\n{body}")
        else:
            segments.append(body)
    return "\n\n".join(segment for segment in segments if segment).strip()


def _clarification_response(resolution: ModelResolution, request_id: str) -> AskResponse:
    options = [
        ClarificationOption(id=option.id, label=option.label)
        for option in resolution.clarification_options
    ]
    clarification = ClarificationPayload(message=_CLARIFICATION_MESSAGE, options=options)
    return AskResponse(request_id=request_id, clarification=clarification)


@router.post("/ask", response_model=AskResponse)
async def ask_endpoint(
    payload: AskRequest,
    request: Request,
    settings: SettingsDep,
    logger: LoggerDep,
) -> AskResponse:
    start = time.perf_counter()
    question = payload.question.strip()
    if len(question) < _Q_MIN_LEN or question.lower() in _Q_PLACEHOLDERS:
        raise HTTPException(
            status_code=400,
            detail="Provide a real question (not a placeholder like 'string')",
        )

    resolution = resolve_models(question, payload.models)

    request_id = getattr(request.state, "request_id", "unknown")

    if resolution.needs_clarification:
        response = _clarification_response(resolution, request_id)
        request.state.confidence = 0.0
        request.state.escalate = False
        elapsed_ms = (time.perf_counter() - start) * 1000
        log_event(
            logger,
            "ask_endpoint_clarification",
            request_id=request_id,
            latency_ms=round(elapsed_ms, 2),
        )
        return response

    scopes: Sequence[ModelScope]
    if resolution.scopes:
        scopes = resolution.scopes
    else:
        scopes = [ModelScope(family_id="", family_label="", model=None)]

    answers = _build_answer_payloads(
        question=question,
        scopes=scopes,
        payload=payload,
        settings=settings,
        logger=logger,
    )

    confidence_values = [entry.confidence for entry in answers if entry.confidence is not None]
    aggregated_confidence = min(confidence_values) if confidence_values else 0.0
    aggregated_escalation = any(entry.should_escalate for entry in answers)
    flattened_sources = [source for entry in answers for source in entry.sources]
    aggregated_answer = _aggregate_answer_text(answers)

    request.state.confidence = aggregated_confidence
    request.state.escalate = aggregated_escalation

    elapsed_ms = (time.perf_counter() - start) * 1000

    if len(answers) == 1:
        primary = answers[0]
        response = AskResponse(
            answer=primary.answer,
            confidence=primary.confidence,
            should_escalate=primary.should_escalate,
            request_id=request_id,
            sources=primary.sources,
            answers=list(answers),
        )
    else:
        response = AskResponse(
            answer=aggregated_answer,
            confidence=aggregated_confidence,
            should_escalate=aggregated_escalation,
            request_id=request_id,
            sources=flattened_sources,
            answers=list(answers),
        )

    log_event(
        logger,
        "ask_endpoint_complete",
        request_id=request_id,
        confidence=aggregated_confidence,
        escalate=aggregated_escalation,
        latency_ms=round(elapsed_ms, 2),
        filters=payload.filters or {},
        models=payload.models or [],
    )

    if getattr(settings, "verbose_logging", False):
        try:
            user_tokens = count_tokens(question)
        except Exception:  # pragma: no cover - diagnostics only
            user_tokens = None
        try:
            answer_tokens = count_tokens(aggregated_answer or "")
        except Exception:  # pragma: no cover - diagnostics only
            answer_tokens = None

        trace: list[str] | None = None
        if getattr(settings, "trace_logging", False):
            trace = [
                "received_question",
                f"resolved_scopes={len(scopes)}",
                f"confidence={float(aggregated_confidence):.3f}",
                "escalate=true" if aggregated_escalation else "escalate=false",
            ]

        log_event(
            logger,
            "chat_turn",
            request_id=request_id,
            question=question,
            answer=aggregated_answer,
            sources=_format_sources(flattened_sources),
            confidence=float(aggregated_confidence),
            tokens={
                "question": user_tokens,
                "answer": answer_tokens,
                "total": (user_tokens or 0) + (answer_tokens or 0),
            },
            openai_key_present=bool(getattr(settings, "openai_api_key", None)),
            trace=trace,
        )

    return response
