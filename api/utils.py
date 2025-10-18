"""Utility helpers for API operations."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any


def load_dictionary(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return payload
    raise ValueError("Dictionary file is malformed; expected a list of entries")


def save_dictionary(path: Path, entries: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_eval_seeds(path: Path) -> list[dict[str, object]]:
    if not path.exists():
        return []
    seeds: list[dict[str, object]] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            question = (row.get("question") or "").strip()
            documents_raw = row.get("relevant_documents") or ""
            documents = [
                item.strip() for item in str(documents_raw).split(";") if item and item.strip()
            ]
            expected = (row.get("expected_answer") or "").strip() or None
            notes = (row.get("notes") or "").strip() or None
            seeds.append(
                {
                    "question": question,
                    "relevant_documents": documents,
                    "expected_answer": expected,
                    "notes": notes,
                }
            )
    return seeds


def save_eval_seeds(path: Path, seeds: list[dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["question", "relevant_documents", "expected_answer", "notes"]
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for seed in seeds:
            raw_documents = seed.get("relevant_documents", [])
            documents: list[str]
            if isinstance(raw_documents, (list, tuple)):
                documents = [str(item).strip() for item in raw_documents if str(item).strip()]
            elif raw_documents is None:
                documents = []
            else:
                value = str(raw_documents).strip()
                documents = [value] if value else []
            writer.writerow(
                {
                    "question": str(seed.get("question", "")).strip(),
                    "relevant_documents": ";".join(documents),
                    "expected_answer": (str(seed.get("expected_answer", "")).strip() or None),
                    "notes": (str(seed.get("notes", "")).strip() or None),
                }
            )


def load_error_logs(path: Path, limit: int = 50) -> list[dict[str, object]]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    tail = lines[-limit:]
    entries: list[dict[str, object]] = []
    for line in tail:
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries


def load_session_logs(path: Path, limit: int = 20) -> list[dict[str, Any]]:  # noqa: PLR0912
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    sessions: list[dict[str, Any]] = []
    ask_metadata: dict[str, dict[str, Any]] = {}
    for line in reversed(lines):
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        message = str(record.get("message", ""))
        payload = record.copy()
        payload.pop("message", None)
        if message == "ask_endpoint_complete":
            request_id = str(payload.get("request_id", ""))
            if request_id:
                meta = ask_metadata.setdefault(request_id, {})
                for key in ("confidence", "escalate", "filters"):
                    if key in payload:
                        meta[key] = payload[key]
        if message == "chat_turn":
            request_id = str(payload.get("request_id", ""))
            if request_id:
                meta = ask_metadata.setdefault(request_id, {})
                for key in ("confidence", "tokens", "trace"):
                    if key in payload and payload[key] is not None:
                        meta[key] = payload[key]
        if message == "request_complete":
            request_id = str(payload.get("request_id", ""))
            entry: dict[str, Any] = {
                "request_id": request_id,
                "method": payload.get("method"),
                "path": payload.get("path"),
                "status": payload.get("status"),
                "latency_ms": payload.get("latency_ms"),
                "time": record.get("time"),
            }
            if request_id in ask_metadata:
                entry.update(ask_metadata[request_id])
            sessions.append(entry)
            if len(sessions) >= limit:
                break
    sessions.reverse()
    return sessions
