"""Tests for evaluation runner artifact generation."""

from __future__ import annotations


from eval.runner import _write_outputs


def test_write_outputs_creates_csv_json_and_html(tmp_path):
    rows = [
        {
            "query": "What is the toner yield?",
            "nDCG@10": 0.8123,
            "Recall@50": 0.9,
            "MRR": 0.75,
            "top_document": "/docs/ced/toner.pdf",
        }
    ]
    metrics = {"nDCG@10": 0.8123, "Recall@50": 0.9, "MRR": 0.75}

    csv_path, json_path, html_path = _write_outputs(tmp_path, rows, metrics)

    assert csv_path.exists()
    assert json_path.exists()
    assert html_path.exists()

    html = html_path.read_text(encoding="utf-8")
    assert "Atticus Evaluation Summary" in html
    assert "What is the toner yield?" in html
    assert "metrics" in html.lower()
    assert "0.8123" in html
    assert "0.9" in html
