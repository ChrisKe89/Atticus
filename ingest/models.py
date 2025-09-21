"""Dataclasses for parsed documents and chunks."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional


@dataclass(slots=True)
class ParsedSection:
    text: str
    page_number: Optional[int] = None
    heading: Optional[str] = None
    extra: Dict[str, str] = field(default_factory=dict)


@dataclass(slots=True)
class ParsedDocument:
    source_path: Path
    source_type: str
    sections: List[ParsedSection]
    sha256: Optional[str] = None

    @property
    def document_id(self) -> str:
        return str(self.source_path)


@dataclass(slots=True)
class Chunk:
    chunk_id: str
    document_id: str
    source_path: str
    text: str
    start_token: int
    end_token: int
    page_number: Optional[int]
    heading: Optional[str]
    extra: Dict[str, str]

