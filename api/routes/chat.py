"""Chat route: POST /ask returning {answer, sources, confidence}.

This adapts the existing retriever pipeline but trims the response shape
to the acceptance contract.
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel, Field

from atticus.config import load_settings
from atticus.logging import configure_logging, log_event
from atticus.tokenization import count_tokens
from retriever import answer_question

router = APIRouter()


class AskPayload(BaseModel):
    # Accept either {query} or {question}
    query: str | None = Field(default=None)
    question: str | None = Field(default=None)


@router.post("/ask")
async def ask(payload: AskPayload, request: Request) -> dict[str, Any]:
    q = (payload.query or payload.question or "").strip()
    if not q:
        raise HTTPException(status_code=400, detail="Missing 'query' or 'question'")
    if q.lower() in {"string", "test", "example"}:
        raise HTTPException(status_code=400, detail="Provide a real question (not 'string')")

    settings = load_settings()
    logger = configure_logging(settings)

    result = answer_question(q, settings=settings, logger=logger)
    # Convert citations to simpler "sources" list (paths only)
    sources = []
    for c in result.citations:
        desc = c.source_path
        if c.page_number is not None:
            desc += f" (page {c.page_number})"
        if c.heading:
            desc += f" - {c.heading}"
        sources.append(desc)

    response_payload = {
        "answer": result.response,
        "sources": sources,
        "confidence": float(result.confidence),
    }

    # Verbose/trace logging (opt-in via .env)
    if getattr(settings, "verbose_logging", False):
        try:
            user_tokens = count_tokens(q)
        except Exception:
            user_tokens = None
        try:
            answer_tokens = count_tokens(result.response or "")
        except Exception:
            answer_tokens = None
        decision_trace: list[str] = []
        if getattr(settings, "trace_logging", False):
            decision_trace.append("received_question")
            decision_trace.append(
                f"retrieved_citations={len(getattr(result, 'citations', []) or [])}"
            )
            decision_trace.append(f"confidence={float(result.confidence):.3f}")
            if getattr(result, "should_escalate", False):
                decision_trace.append("escalate=true")
            else:
                decision_trace.append("escalate=false")
        request_id = getattr(request.state, "request_id", "unknown")
        log_event(
            logger,
            "chat_turn",
            request_id=request_id,
            question=q,
            answer=result.response,
            sources=sources,
            confidence=float(result.confidence),
            tokens={
                "question": user_tokens,
                "answer": answer_tokens,
                "total": (user_tokens or 0) + (answer_tokens or 0),
            },
            openai_key_present=bool(getattr(settings, "openai_api_key", None)),
            trace=decision_trace or None,
        )

    return response_payload
