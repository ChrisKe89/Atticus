"""Plain text parser."""

from __future__ import annotations

from pathlib import Path

from ..models import ParsedDocument, ParsedSection


def parse_text(path: Path) -> ParsedDocument:
    text = path.read_text(encoding="utf-8")
    section = ParsedSection(text=text)
    return ParsedDocument(
        source_path=path,
        source_type="text",
        sections=[section],
    )

