"""Utilities for escalation routing, logging, and identifiers."""

from __future__ import annotations

import csv
import json
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, TypedDict

from .config import AppSettings

AE_PREFIX = "AE"
MAX_EMAIL_CITATIONS = 3


class EmailBody(TypedDict, total=False):
    header: str
    question: str
    answer: str
    certainty_score: float
    certainty_reason: str
    citations: list[dict[str, Any]]
    bullets: list[str]


class EmailMetadata(TypedDict):
    ae_id: str
    request_id: str
    timestamp: str
    category: str


class EmailPayload(TypedDict):
    to: list[str]
    cc: list[str]
    subject: str
    body: EmailBody
    metadata: EmailMetadata


@dataclass(slots=True)
class EscalationRecord:
    ae_id: str
    category: str
    request_id: str
    question: str
    answer: str
    bullets: list[str]
    confidence: float
    recipients: list[str]
    cc: list[str]
    citations: list[dict[str, Any]]
    created_at: datetime
    certainty_reason: str

    def as_email_payload(self) -> EmailPayload:
        header = f"Escalation from Atticus: {self.ae_id}."
        subject = f"Escalation from Atticus: {self.ae_id}"
        if self.request_id:
            subject = f"{subject} · {self.request_id}"
        timestamp = self.created_at.isoformat(timespec="seconds")
        return {
            "to": list(self.recipients),
            "cc": list(self.cc),
            "subject": subject,
            "body": {
                "header": header,
                "question": self.question,
                "answer": self.answer,
                "certainty_score": round(self.confidence, 2),
                "certainty_reason": self.certainty_reason,
                "citations": self.citations[:MAX_EMAIL_CITATIONS],
                "bullets": list(self.bullets[:5]),
            },
            "metadata": {
                "ae_id": self.ae_id,
                "request_id": self.request_id,
                "timestamp": timestamp,
                "category": self.category,
            },
        }

    def to_csv_row(self) -> dict[str, object]:
        return {
            "ae_id": self.ae_id,
            "timestamp": self.created_at.isoformat(timespec="seconds"),
            "category": self.category,
            "certainty_score": f"{self.confidence:.2f}",
            "question": self.question,
            "answer_preview": self.answer[:160],
            "to": ";".join(self.recipients),
            "cc": ";".join(self.cc),
            "request_id": self.request_id,
        }


def next_ae_id(counter_path: Path) -> str:
    counter_path.parent.mkdir(parents=True, exist_ok=True)
    if counter_path.exists():
        try:
            current = int(counter_path.read_text(encoding="utf-8").strip() or "100")
        except ValueError:
            current = 100
    else:
        current = 100

    next_value = current + 1
    temp_path = counter_path.with_suffix(counter_path.suffix + ".tmp")
    temp_path.write_text(f"{next_value}\n", encoding="utf-8")
    temp_path.replace(counter_path)
    return f"{AE_PREFIX}{current}"


def categorize(text: str, settings: AppSettings) -> str:
    lowered = (text or "").lower()
    for name, terms in settings.escalation_terms.items():
        if any(term in lowered for term in terms):
            return name
    return "unsure"


def select_recipient(category: str, settings: AppSettings) -> str:
    return settings.team_emails.get(category) or next(iter(settings.team_emails.values()), settings.contact_email or "")


def log_escalation(record: EscalationRecord, json_path: Path, csv_path: Path) -> None:
    json_path.parent.mkdir(parents=True, exist_ok=True)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with json_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record.as_email_payload(), ensure_ascii=False) + "\n")

    write_header = not csv_path.exists()
    with csv_path.open("a", newline="", encoding="utf-8") as handle:
        fieldnames = [
            "ae_id",
            "timestamp",
            "category",
            "certainty_score",
            "question",
            "answer_preview",
            "to",
            "cc",
            "request_id",
        ]
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        writer.writerow(record.to_csv_row())


def build_email_subject(record: EscalationRecord) -> str:
    payload = record.as_email_payload()
    return str(payload.get("subject", ""))


def build_email_body(record: EscalationRecord) -> str:
    payload = record.as_email_payload()
    body = payload["body"]
    header = body.get("header", "")
    lines = [header]
    if header:
        lines.append("")
    score = body.get("certainty_score", 0.0)
    if isinstance(score, (int, float)):
        score_str = f"{score:.2f}"
    else:
        score_str = str(score)
    lines.extend(
        [
            f"Question: {body.get('question', '')}",
            f"Answer: {body.get('answer', '')}",
            f"Certainty Score: {score_str}",
            f"Certainty Reason: {body.get('certainty_reason', '')}",
        ]
    )
    bullets = body.get("bullets", [])
    if isinstance(bullets, list) and bullets:
        lines.append("")
        lines.append("Key Points:")
        for idx, bullet in enumerate(bullets[:5], start=1):
            lines.append(f"({idx}) {bullet}")
    citations = body.get("citations", [])
    if isinstance(citations, list) and citations:
        lines.append("")
        lines.append("Citations:")
        for idx, cite in enumerate(citations, start=1):
            lines.append(f"[{idx}] {json.dumps(cite, ensure_ascii=False)}")
    metadata = payload["metadata"]
    lines.append("")
    lines.append(f"Request ID: {metadata.get('request_id', record.request_id)}")
    return "\n".join(lines)


def as_citation_dicts(citations: Iterable[object]) -> list[dict[str, Any]]:
    payload: list[dict[str, Any]] = []
    for citation in citations:
        data = {
            "chunk_id": getattr(citation, "chunk_id", None),
            "source_path": getattr(citation, "source_path", None),
            "page_number": getattr(citation, "page_number", None),
            "heading": getattr(citation, "heading", None),
            "score": getattr(citation, "score", None),
        }
        payload.append({key: value for key, value in data.items() if value is not None})
    return payload
