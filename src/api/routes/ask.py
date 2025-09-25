"""Question answering endpoint with escalation handling."""

from __future__ import annotations

import re
import time
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request, status
from fastapi.responses import JSONResponse

from atticus.escalation import (
    EscalationRecord,
    as_citation_dicts,
    build_email_body,
    build_email_subject,
    categorize,
    log_escalation,
    next_ae_id,
    select_recipient,
)
from atticus.logging import log_event, make_request_id
from atticus.notify.mailer import send_escalation
from retriever import answer_question

from ..dependencies import LoggerDep, SettingsDep
from ..schemas import AskRequest, AskResponse, CitationModel

router = APIRouter()
Q_MIN_LEN = 4
PARTIAL_STATUS = status.HTTP_206_PARTIAL_CONTENT
CLARIFY_MIN_WORDS = 5
PRODUCT_HINTS = {"apeos", "docuprint", "printer", "press", "workflow", "toner", "presses"}


def _ensure_human_question(text: str) -> str:
    stripped = text.strip()
    if len(stripped) < Q_MIN_LEN or stripped.lower() in {"string", "test", "example"}:
        raise HTTPException(status_code=400, detail="Provide a real question (not a placeholder like 'string')")
    return stripped


def _maybe_request_clarification(question: str) -> str | None:
    raw_words = [word for word in re.split(r"\s+", question.strip()) if word]
    lowered = question.lower()
    if len(raw_words) < CLARIFY_MIN_WORDS:
        return "Could you share more context (product, workflow, or scenario) so I can search the right guidance?"
    pronouns = {"it", "this", "that", "they", "them"}
    words = {word.lower().strip(".,!?") for word in raw_words}
    if pronouns.intersection(words) and not any(hint in lowered for hint in PRODUCT_HINTS):
        return "Which product or workflow should I focus on? A model name or process step would help."
    if "which" in lowered and "model" not in lowered and not any(hint in lowered for hint in PRODUCT_HINTS):
        return "Which model or series are you comparing?"
    return None


@router.post("/ask", response_model=AskResponse)
async def ask_endpoint(
    payload: AskRequest,
    request: Request,
    settings: SettingsDep,
    logger: LoggerDep,
) -> JSONResponse:
    start = time.perf_counter()
    question = _ensure_human_question(payload.question)

    request_id = getattr(request.state, "request_id", None) or make_request_id()
    clarification = _maybe_request_clarification(question)
    if clarification:
        request.state.confidence = 0.0
        request.state.escalate = False
        log_event(
            logger,
            "ask_clarification_needed",
            request_id=request_id,
            question=question,
        )
        response_body = AskResponse(
            answer=clarification,
            bullets=None,
            confidence=0.0,
            should_escalate=False,
            citations=[],
            request_id=request_id,
            clarification_needed=True,
            clarification=clarification,
        )
        return JSONResponse(status_code=status.HTTP_200_OK, content=response_body.model_dump(mode="json"))

    answer = answer_question(
        question,
        settings=settings,
        filters=payload.filters,
        logger=logger,
        request_id=request_id,
    )
    elapsed_ms = (time.perf_counter() - start) * 1000

    request.state.confidence = answer.confidence
    request.state.escalate = answer.should_escalate

    citations = [
        CitationModel(
            chunk_id=item.chunk_id,
            source_path=item.source_path,
            page_number=item.page_number,
            heading=item.heading,
            score=item.score,
        )
        for item in answer.citations[:3]
    ]
    source_descriptions = []
    for citation in answer.citations[:3]:
        description = citation.source_path
        if citation.page_number is not None:
            description += f" (page {citation.page_number})"
        if citation.heading:
            description += f" — {citation.heading}"
        source_descriptions.append(description)

    status_code = status.HTTP_200_OK
    escalated = False
    ae_id: str | None = None

    if answer.should_escalate:
        status_code = PARTIAL_STATUS
        escalated = True
        ae_id = next_ae_id(settings.escalation_counter_file)
        category = categorize(f"{question}\n{answer.summary}", settings)
        recipient = select_recipient(category, settings)
        recipients = [recipient] if recipient else []
        certainty_reason = f"Confidence {answer.confidence:.2f} below threshold {settings.confidence_threshold:.2f}"
        record = EscalationRecord(
            ae_id=ae_id,
            category=category,
            request_id=request_id,
            question=question,
            answer=answer.summary,
            bullets=answer.bullets,
            confidence=answer.confidence,
            recipients=recipients,
            cc=settings.escalation_cc,
            citations=as_citation_dicts(answer.citations),
            created_at=datetime.now(tz=settings.tzinfo),
            certainty_reason=certainty_reason,
        )
        log_escalation(record, settings.escalation_log_json, settings.escalation_log_csv)
        email_payload = record.as_email_payload()
        if recipients:
            send_escalation(
                subject=build_email_subject(record),
                body=build_email_body(record),
                to=email_payload["to"],
                cc=email_payload["cc"],
            )
        else:
            log_event(
                logger,
                "escalation_missing_recipient",
                request_id=request_id,
                category=category,
                ae_id=ae_id,
            )

        answer_text = answer.summary
        if not answer_text.lower().startswith("this may be incomplete"):
            answer_text = f"This may be incomplete. {answer_text}".strip()
    else:
        answer_text = answer.summary

    log_event(
        logger,
        "ask_endpoint_complete",
        request_id=request_id,
        confidence=answer.confidence,
        escalate=answer.should_escalate,
        latency_ms=round(elapsed_ms, 2),
        filters=payload.filters or {},
        ae_id=ae_id,
    )

    response_body = AskResponse(
        answer=answer_text,
        bullets=answer.bullets or None,
        confidence=answer.confidence,
        should_escalate=answer.should_escalate,
        citations=citations,
        request_id=request_id,
        sources=source_descriptions or None,
        escalated=escalated or None,
        ae_id=ae_id,
    )

    return JSONResponse(status_code=status_code, content=response_body.model_dump(mode="json"))
