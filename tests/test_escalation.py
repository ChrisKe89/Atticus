from __future__ import annotations

import csv
import json
from datetime import UTC, datetime

from atticus.escalation import (
    EscalationRecord,
    as_citation_dicts,
    build_email_body,
    build_email_subject,
    log_escalation,
    next_ae_id,
)


def _sample_record(ae_id: str = "AE200") -> EscalationRecord:
    now = datetime.now(tz=UTC)
    citations = as_citation_dicts(
        [type("Cite", (), {"chunk_id": "c1", "source_path": "content/doc.pdf", "page_number": 2, "heading": "Specs"})]
    )
    return EscalationRecord(
        ae_id=ae_id,
        category="technical",
        request_id="req-123",
        question="What is the DPI of model X?",
        answer="Model X ships with 1200 DPI optical resolution.",
        bullets=["Supports 1200 x 1200 dpi."],
        confidence=0.61,
        recipients=["nts@example.com"],
        cc=["ops@example.com"],
        citations=citations,
        created_at=now,
        certainty_reason="Confidence 0.61 below threshold 0.70",
    )


def test_next_ae_id_starts_at_100(tmp_path) -> None:
    counter = tmp_path / "escalations.counter"
    first = next_ae_id(counter)
    assert first == "AE100"
    assert counter.read_text(encoding="utf-8").strip() == "101"

    second = next_ae_id(counter)
    assert second == "AE101"
    assert counter.read_text(encoding="utf-8").strip() == "102"


def test_log_escalation_emits_schema(tmp_path) -> None:
    record = _sample_record()
    json_path = tmp_path / "logs.jsonl"
    csv_path = tmp_path / "logs.csv"

    log_escalation(record, json_path, csv_path)

    data = json.loads(json_path.read_text(encoding="utf-8").splitlines()[0])
    subject = build_email_subject(record)
    assert data["subject"] == subject
    assert record.request_id in subject
    assert data["body"]["certainty_reason"] == record.certainty_reason
    assert data["metadata"]["ae_id"] == record.ae_id
    assert data["body"]["bullets"] == record.bullets

    with csv_path.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    row = rows[0]
    assert row["ae_id"] == record.ae_id
    assert row["to"] == ";".join(record.recipients)
    assert row["cc"] == ";".join(record.cc)
    assert row["request_id"] == record.request_id


def test_build_email_body_contains_reason_and_request_id() -> None:
    record = _sample_record()
    body = build_email_body(record)
    assert "Certainty Reason: Confidence 0.61 below threshold 0.70" in body
    assert "Request ID: req-123" in body
    assert "Key Points:" in body
