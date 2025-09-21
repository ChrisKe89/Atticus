"""Image OCR parser."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

from PIL import Image

from ..models import ParsedDocument, ParsedSection

try:  # pragma: no cover - optional dependency
    import pytesseract as _pytesseract  # type: ignore[import-untyped]
except Exception:  # pragma: no cover - runtime fallback
    _pytesseract = None

pytesseract: Any | None = _pytesseract


def parse_image(path: Path) -> ParsedDocument:
    text = ""
    if pytesseract is not None:  # pragma: no cover - requires external binary
        with Image.open(str(path)) as image:
            text = cast(str, pytesseract.image_to_string(image))
    section = ParsedSection(text=text.strip(), breadcrumbs=["Image"])
    return ParsedDocument(
        source_path=path,
        source_type="image",
        sections=[section],
    )

