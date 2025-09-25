#!/usr/bin/env python3
"""Log an escalation record using the shared helpers."""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from atticus.config import load_settings
from atticus.escalation import EscalationRecord, log_escalation


def _load_citations(path: Path | None) -> list[dict[str, object]]:
    if path is None or not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("Citations JSON must be a list of dicts")
    result: list[dict[str, object]] = []
    for item in data:
        if isinstance(item, dict):
            result.append(dict(item))
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Append an escalation record to log files")
    parser.add_argument("--ae-id", required=True, help="Escalation identifier")
    parser.add_argument("--category", required=True, help="Routing category")
    parser.add_argument("--question", required=True, help="User question")
    parser.add_argument("--answer", required=True, help="Generated answer text")
    parser.add_argument("--confidence", type=float, required=True, help="Confidence score")
    parser.add_argument("--request-id", required=True, help="Request identifier")
    parser.add_argument("--recipients", nargs="*", default=[], help="Primary recipients")
    parser.add_argument("--cc", nargs="*", default=None, help="Override CC recipients")
    parser.add_argument(
        "--bullet",
        dest="bullets",
        action="append",
        default=None,
        help="Optional bullet point to include (can be repeated)",
    )
    parser.add_argument(
        "--certainty-reason",
        default=None,
        help="Reason recorded when confidence is low",
    )
    parser.add_argument("--citations", type=Path, help="JSON file containing citation dictionaries")
    args = parser.parse_args()

    settings = load_settings()
    citations = _load_citations(args.citations)
    cc_values = list(args.cc) if args.cc is not None else settings.escalation_cc
    reason = args.certainty_reason or (
        f"Confidence {args.confidence:.2f} below threshold {settings.confidence_threshold:.2f}"
    )
    record = EscalationRecord(
        ae_id=args.ae_id,
        category=args.category,
        request_id=args.request_id,
        question=args.question,
        answer=args.answer,
        bullets=list(args.bullets or []),
        confidence=args.confidence,
        recipients=list(args.recipients),
        cc=cc_values,
        citations=citations,
        created_at=datetime.now(tz=settings.tzinfo),
        certainty_reason=reason,
    )
    log_escalation(record, settings.escalation_log_json, settings.escalation_log_csv)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
