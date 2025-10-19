"""Tests for evaluation runner artifact generation."""

from __future__ import annotations


import json
from types import SimpleNamespace

import pytest

from eval.runner import (
    EvaluationMode,
    _load_baseline,
    _resolve_modes,
    _write_modes_summary,
    _write_outputs,
)
from retriever.vector_store import RetrievalMode
from scripts import eval_run


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


def test_resolve_modes_handles_duplicates():
    modes = _resolve_modes(["HYBRID", "vector", "hybrid"], ["lexical"])
    assert modes[0] is RetrievalMode.HYBRID
    assert modes[1] is RetrievalMode.VECTOR
    assert len(modes) == 2


def test_load_baseline_supports_multi_schema(tmp_path):
    payload = {
        "hybrid": {"nDCG@10": 0.91, "Recall@50": 0.87, "MRR": 0.74},
        "vector": {"nDCG@10": 0.84, "Recall@50": 0.76, "MRR": 0.62},
    }
    path = tmp_path / "baseline.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    metrics = _load_baseline(path)
    assert metrics["hybrid"]["nDCG@10"] == pytest.approx(0.91)
    assert metrics["vector"]["MRR"] == pytest.approx(0.62)


def test_write_modes_summary_creates_overview(tmp_path):
    mode = EvaluationMode(
        mode="hybrid",
        metrics={"nDCG@10": 0.9, "Recall@50": 0.8, "MRR": 0.7},
        deltas={"nDCG@10": 0.1, "Recall@50": 0.2, "MRR": 0.3},
        summary_csv=tmp_path / "hybrid" / "metrics.csv",
        summary_json=tmp_path / "hybrid" / "summary.json",
        summary_html=tmp_path / "hybrid" / "metrics.html",
    )
    summary_path = _write_modes_summary(tmp_path, [mode])
    assert summary_path.exists()
    data = json.loads(summary_path.read_text(encoding="utf-8"))
    assert data["hybrid"]["metrics"]["MRR"] == 0.7


def test_eval_run_writes_ci_index(tmp_path):
    output_dir = tmp_path / "ci"
    metrics_dir = output_dir / "mode-hybrid"
    metrics_dir.mkdir(parents=True)
    summary_html = metrics_dir / "metrics.html"
    summary_html.write_text("<html></html>", encoding="utf-8")
    result = SimpleNamespace(
        metrics={"nDCG@10": 0.92, "Recall@50": 0.88},
        modes=[SimpleNamespace(mode="hybrid", summary_html=summary_html)],
    )

    eval_run._write_ci_index(output_dir, result)

    index_path = output_dir / "index.html"
    assert index_path.exists()
    html = index_path.read_text(encoding="utf-8")
    assert "hybrid" in html.lower()
    assert "0.92" in html
