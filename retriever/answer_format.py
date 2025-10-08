from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Iterable

_TRAILING_MD_ANCHOR = re.compile(r"\s*\(\[[^\]]+\]\(#\d+\)\)\.?\s*$")
_TRAILING_PG_PAREN = re.compile(r"\s*\(\s*p{1,2}\.?\s*[\d\-\u2013, ]+\s*\)\.?\s*$", re.IGNORECASE)
_TRAILING_SOURCEY = re.compile(
    r"\s*\([\w\s\-,&]+p{0,2}\.?\s*[\d\-\u2013, ]+\)\.?\s*$", re.IGNORECASE
)
_INLINE_BULLET = re.compile(r"\s(?P<bullet>-|\u2022|\u2013|\u2014)\s+")
_NUMBERED_ITEM_RE = re.compile(r"(?m)^\s*\d+\.\s+")
# Find " 2. " / " 3. " even mid-paragraph (avoid years by requiring a period + space)
# We will insert TWO newlines so Markdown renderers reliably break paragraphs.
# Insert a single newline before mid-paragraph numbers (ReactMarkdown handles lists fine)
_MIDPARA_NUMBERED = re.compile(r"(?<!^)\s+(\d+)\.\s+")
_SOURCES_SECTION = re.compile(r"(?is)\n+[-*_]{3,}\s*\n*[*_]*sources?[*_]*\s*\n.*\Z")
_SOURCES_LABEL = re.compile(r"(?im)^\s*sources?\s*:?\s*$")
_INLINE_SOURCES_TOKEN = re.compile(r"(?i)\*{0,2}sources\*{0,2}\s*:?\s*")
_INTRO_RE = re.compile(r"^(?P<intro>[^:\n]+:)\s*(?P<body>.+)$", re.DOTALL)


def _strip_inline_citation_tails(text: str) -> str:
    overall = _TRAILING_MD_ANCHOR.sub("", text)
    overall = _TRAILING_PG_PAREN.sub("", overall)
    overall = _TRAILING_SOURCEY.sub("", overall)

    cleaned_lines: list[str] = []
    for raw_line in overall.splitlines():
        tmp = _TRAILING_MD_ANCHOR.sub("", raw_line)
        tmp = _TRAILING_PG_PAREN.sub("", tmp)
        tmp = _TRAILING_SOURCEY.sub("", tmp)
        cleaned_lines.append(tmp.rstrip())
    return "\n".join(cleaned_lines).strip()


def _strip_existing_sources_section(text: str) -> str:
    trimmed = _SOURCES_SECTION.sub("", text)
    trimmed = _INLINE_SOURCES_TOKEN.sub("\n\n", trimmed)
    lines = [ln for ln in trimmed.splitlines() if not _SOURCES_LABEL.match(ln)]
    return "\n".join(lines).rstrip()


def _normalize_bullets(body: str) -> str:
    normalized: list[str] = []
    for line in body.splitlines():
        bullet_match = re.match(r"^\s*(?:-|\u2022|\u2013|\u2014)\s+", line)
        if bullet_match:
            bullet = bullet_match.group(0)
            text = re.sub(r"\s+", " ", line[len(bullet) :]).strip()
            normalized.append(f"{bullet}{text}")
        else:
            normalized.append(line.rstrip())
    return "\n".join(normalized).strip()


def _to_numbered_list(text: str) -> str:
    body = text.strip()

    if re.search(r"(?m)^\s*(?:-|\u2022|\u2013|\u2014)\s+", body):
        return _normalize_bullets(body)

    if _INLINE_BULLET.search(body):

        def _replace(match: re.Match[str]) -> str:
            return f"\n{match.group('bullet')} "

        return _normalize_bullets(_INLINE_BULLET.sub(_replace, body))

    body = _MIDPARA_NUMBERED.sub(r"\n\1. ", body)

    starts = [m.start() for m in _NUMBERED_ITEM_RE.finditer(body)]
    if not starts:
        body = re.sub(r"\s+(?=[2-9]\.\s)", "\n", body)
        return body
    starts.append(len(body))

    items: list[str] = []
    for idx in range(len(starts) - 1):
        segment = body[starts[idx] : starts[idx + 1]].strip()
        segment = re.sub(r"\s+", " ", segment)
        items.append(segment)
    return "\n\n".join(items)


def _fmt_source_line(item: Any) -> str:
    source_path = getattr(item, "source_path", None)
    if source_path is None and isinstance(item, dict):
        source_path = item.get("source_path", "")
    source_path = str(source_path or "")

    page_data = (
        getattr(item, "page_range", None)
        or getattr(item, "pages", None)
        or (item.get("page_range") if isinstance(item, dict) else None)
        or (item.get("pages") if isinstance(item, dict) else None)
    )

    basename = Path(source_path).name
    suffix = ""
    if isinstance(page_data, (list, tuple, set)) and page_data:
        ints = sorted({int(str(p)) for p in page_data if str(p).isdigit()})
        if ints:
            suffix = f" (p. {', '.join(str(p) for p in ints)})"

    return f"{basename}{suffix} — {source_path}"


def format_answer_markdown(answer_text: str, citations: Iterable[Any]) -> str:  # noqa: ARG001
    sans_sources = _strip_existing_sources_section(answer_text)
    cleaned = _strip_inline_citation_tails(sans_sources)

    intro: str | None = None
    match = _INTRO_RE.match(cleaned.strip())
    if match:
        intro = match.group("intro").strip()
        body_text = match.group("body").strip()
    else:
        body_text = cleaned.strip()

    body = _to_numbered_list(body_text)

    if intro:
        return f"{intro}\n\n{body}"
    return body
