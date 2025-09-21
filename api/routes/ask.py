"""Question answering endpoint."""

from __future__ import annotations

import time

from fastapi import APIRouter, Request

from atticus.logging import log_event
from retriever import answer_question

from ..dependencies import LoggerDep, SettingsDep
from ..schemas import AskRequest, AskResponse, CitationModel

router = APIRouter()


@router.post("/ask", response_model=AskResponse)
async def ask_endpoint(
    payload: AskRequest,
    request: Request,
    settings: SettingsDep,
    logger: LoggerDep,
) -> AskResponse:
    start = time.perf_counter()
    answer = answer_question(payload.question, settings=settings, filters=payload.filters, logger=logger)
    elapsed_ms = (time.perf_counter() - start) * 1000

    request_id = getattr(request.state, "request_id", "unknown")
    request.state.confidence = answer.confidence
    request.state.escalate = answer.should_escalate

    log_event(
        logger,
        "ask_endpoint_complete",
        request_id=request_id,
        confidence=answer.confidence,
        escalate=answer.should_escalate,
        latency_ms=round(elapsed_ms, 2),
        filters=payload.filters or {},
    )

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

    return AskResponse(
        answer=answer.response,
        confidence=answer.confidence,
        should_escalate=answer.should_escalate,
        citations=citations,
        request_id=request_id,
    )
