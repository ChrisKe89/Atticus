"""Dataclasses for parsed documents and chunks."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(slots=True)
class ParsedSection:
    text: str
    page_number: int | None = None
    heading: str | None = None
    extra: dict[str, str] = field(default_factory=dict)
    breadcrumbs: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ParsedDocument:
    source_path: Path
    source_type: str
    sections: list[ParsedSection]
    sha256: str | None = None

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
    page_number: int | None
    heading: str | None
    extra: dict[str, str]
    breadcrumbs: list[str] = field(default_factory=list)
