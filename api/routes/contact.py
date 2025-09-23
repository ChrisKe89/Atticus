"""Contact escalation endpoint.

POST /contact accepts JSON payload and sends an escalation email via SMTP.
"""

from __future__ import annotations

from fastapi import APIRouter, Request, status
from pydantic import BaseModel, Field

from atticus.config import load_settings
from atticus.logging import configure_logging, log_event
from atticus.notify.mailer import send_escalation

router = APIRouter()


class ContactRequest(BaseModel):
    reason: str = Field(description="Reason for contacting support/escalation")
    transcript: list[str] | str | None = Field(
        default=None,
        description="Optional chat transcript (list of lines) or a single string",
    )


@router.post("/contact", status_code=status.HTTP_202_ACCEPTED)
async def contact(payload: ContactRequest, request: Request) -> dict[str, str]:
    settings = load_settings()
    logger = configure_logging(settings)

    request_id = getattr(request.state, "request_id", "unknown")
    body_lines = [f"Reason: {payload.reason}"]
    if payload.transcript:
        body_lines.append("")
        body_lines.append("Transcript:")
        if isinstance(payload.transcript, list):
            body_lines.extend(str(x) for x in payload.transcript)
        else:
            body_lines.append(str(payload.transcript))
    body = "\n".join(body_lines)

    subject = f"Atticus escalation: {payload.reason}"[:200]
    send_escalation(subject=subject, body=body)

    log_event(
        logger,
        "contact_escalation_sent",
        request_id=request_id,
        has_transcript=bool(payload.transcript),
    )
    return {"status": "accepted"}
