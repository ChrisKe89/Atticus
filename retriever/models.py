"""Data models for retrieval results."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List


@dataclass(slots=True)
class Citation:
    chunk_id: str
    source_path: str
    page_number: int | None
    heading: str | None
    score: float


@dataclass(slots=True)
class Answer:
    question: str
    response: str
    citations: List[Citation]
    confidence: float
    should_escalate: bool

