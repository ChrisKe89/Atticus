"""DOCX parser."""

from __future__ import annotations

from pathlib import Path

import docx

from ..models import ParsedDocument, ParsedSection


def parse_docx(path: Path) -> ParsedDocument:
    document = docx.Document(str(path))
    paragraphs = [para.text.strip() for para in document.paragraphs if para.text.strip()]
    sections = [ParsedSection(text=text) for text in paragraphs]
    return ParsedDocument(
        source_path=path,
        source_type="docx",
        sections=sections,
    )

