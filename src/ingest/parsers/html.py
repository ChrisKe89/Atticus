"""HTML parser using BeautifulSoup."""

from __future__ import annotations

from pathlib import Path

from bs4 import BeautifulSoup

from ..models import ParsedDocument, ParsedSection


def parse_html(path: Path) -> ParsedDocument:
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    texts = []
    for heading in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6"]):
        heading_text = heading.get_text(strip=True)
        sibling_text = []
        for sibling in heading.next_siblings:
            if getattr(sibling, "name", None) in {"h1", "h2", "h3", "h4", "h5", "h6"}:
                break
            if isinstance(sibling, str):
                content = sibling.strip()
            else:
                content = sibling.get_text(" ", strip=True)
            if content:
                sibling_text.append(content)
        texts.append((heading_text, "\n".join(sibling_text)))

    if not texts:
        body_text = soup.get_text("\n", strip=True)
        texts.append(("", body_text))

    sections = [
        ParsedSection(text=content, heading=heading or None, breadcrumbs=[heading] if heading else [])
        for heading, content in texts
        if content
    ]
    return ParsedDocument(
        source_path=path,
        source_type="html",
        sections=sections,
    )
