"""Utility helpers for API operations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List


def load_dictionary(path: Path) -> List[Dict[str, object]]:
    if not path.exists():
        return []
    payload = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(payload, list):
        return payload
    raise ValueError("Dictionary file is malformed; expected a list of entries")


def save_dictionary(path: Path, entries: List[Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(entries, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def load_error_logs(path: Path, limit: int = 50) -> List[Dict[str, object]]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    tail = lines[-limit:]
    entries: List[Dict[str, object]] = []
    for line in tail:
        try:
            entries.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return entries

