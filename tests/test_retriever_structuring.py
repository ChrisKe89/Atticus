from __future__ import annotations

from atticus.config import AppSettings
from retriever.service import _structure_answer, estimate_confidence
from retriever.vector_store import SearchResult


def _make_result(score: float) -> SearchResult:
    return SearchResult(
        chunk_id="c1",
        source_path="content/doc.pdf",
        text="Sample text",
        score=score,
        page_number=1,
        heading="Specs",
        metadata={},
        chunk_index=0,
        vector_score=score,
        lexical_score=score,
        fuzz_score=score,
    )


def test_structure_answer_limits_sentences_and_bullets() -> None:
    text = "First sentence. Second sentence! Third sentence?\n- detail one\n- detail two\n- detail three\n- detail four"
    summary, bullets = _structure_answer(text)
    assert summary == "First sentence. Second sentence!"
    assert bullets == ["detail one.", "detail two.", "detail three."]


def test_estimate_confidence_clamps_and_combines() -> None:
    settings = AppSettings()
    results = [_make_result(0.95), _make_result(0.85), _make_result(0.1)]
    confidence = estimate_confidence(results, settings, llm_confidence=0.6)
    assert 0.0 <= confidence <= 1.0
    assert confidence >= 0.5
