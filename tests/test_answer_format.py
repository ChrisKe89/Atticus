from types import SimpleNamespace

from retriever import answer_format


def test_strip_inline_citation_tails_removes_markdown() -> None:
    text = "Finding ([source](#3)).\nAnother line (p. 2-3)."
    cleaned = answer_format._strip_inline_citation_tails(text)
    assert "source" not in cleaned
    assert "(p. 2-3)" not in cleaned


def test_strip_existing_sources_section() -> None:
    body = "Summary\n\n---\nSources\n- doc.pdf"
    trimmed = answer_format._strip_existing_sources_section(body)
    assert "Sources" not in trimmed
    assert trimmed.strip() == "Summary"


def test_to_numbered_list_handles_inline_items() -> None:
    text = "Here are steps 1. Turn on 2. Calibrate"
    numbered = answer_format._to_numbered_list(text)
    assert "1. Turn on" in numbered
    assert "2. Calibrate" in numbered


def test_fmt_source_line_with_page_collection() -> None:
    citation = SimpleNamespace(source_path="content/manual.pdf", page_range=[3, 1, 3])
    line = answer_format._fmt_source_line(citation)
    assert line.startswith("manual.pdf")
    assert "(p. 1, 3)" in line


def test_format_answer_markdown_with_intro_and_bullets() -> None:
    raw = "Intro summary: - item one - item two\n\nSources:\n- doc.pdf"
    result = answer_format.format_answer_markdown(raw, [])
    assert "Sources" not in result
    assert result.startswith("Intro summary:")
