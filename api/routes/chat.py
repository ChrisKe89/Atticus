"""Unified chat route returning the canonical ask response contract."""

from __future__ import annotations

import time
from typing import Iterable

from fastapi import APIRouter, HTTPException, Request

from atticus.logging import log_event
from atticus.tokenization import count_tokens
from retriever import answer_question

from ..dependencies import LoggerDep, SettingsDep
from ..schemas import AskRequest, AskResponse, CitationModel

router = APIRouter()
_Q_PLACEHOLDERS = {"string", "test", "example"}
_Q_MIN_LEN = 4


def _format_sources(citations: Iterable[CitationModel]) -> list[str]:
    sources: list[str] = []
    for citation in citations:
        desc = citation.source_path
        if citation.page_number is not None:
            desc += f" (page {citation.page_number})"
        if citation.heading:
            desc += f" - {citation.heading}"
        sources.append(desc)
    return sources


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

    answer = answer_question(
        question,
        settings=settings,
        filters=payload.filters,
        logger=logger,
    )

    request_id = getattr(request.state, "request_id", "unknown")
    request.state.confidence = answer.confidence
    request.state.escalate = answer.should_escalate
    elapsed_ms = (time.perf_counter() - start) * 1000

    citations = [
        CitationModel(
            chunk_id=item.chunk_id,
            source_path=item.source_path,
            page_number=item.page_number,
            heading=item.heading,
            score=item.score,
        )
        for item in answer.citations
    ]

    response = AskResponse(
        answer=answer.response,
        confidence=answer.confidence,
        should_escalate=answer.should_escalate,
        citations=citations,
        request_id=request_id,
    )

    log_event(
        logger,
        "ask_endpoint_complete",
        request_id=request_id,
        confidence=answer.confidence,
        escalate=answer.should_escalate,
        latency_ms=round(elapsed_ms, 2),
        filters=payload.filters or {},
    )

    if getattr(settings, "verbose_logging", False):
        try:
            user_tokens = count_tokens(question)
        except Exception:  # pragma: no cover - diagnostics only
            user_tokens = None
        try:
            answer_tokens = count_tokens(answer.response or "")
        except Exception:  # pragma: no cover - diagnostics only
            answer_tokens = None

        trace: list[str] | None = None
        if getattr(settings, "trace_logging", False):
            trace = [
                "received_question",
                f"retrieved_citations={len(answer.citations)}",
                f"confidence={float(answer.confidence):.3f}",
                "escalate=true" if answer.should_escalate else "escalate=false",
            ]

        log_event(
            logger,
            "chat_turn",
            request_id=request_id,
            question=question,
            answer=answer.response,
            sources=_format_sources(citations),
            confidence=float(answer.confidence),
            tokens={
                "question": user_tokens,
                "answer": answer_tokens,
                "total": (user_tokens or 0) + (answer_tokens or 0),
            },
            openai_key_present=bool(getattr(settings, "openai_api_key", None)),
            trace=trace,
        )

    return response
