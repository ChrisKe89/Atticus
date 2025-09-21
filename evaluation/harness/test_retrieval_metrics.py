"""Pytest harness for Atticus evaluation (§4)."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import sys
from pathlib import Path as _Path

ROOT = _Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest

from atticus.config import Settings
from atticus.evaluation import evaluate
from atticus.ingestion.pipeline import run_ingestion


@pytest.fixture(scope="session")
def settings() -> Settings:
    return Settings()


@pytest.fixture(scope="session", autouse=True)
def ensure_index(settings: Settings) -> None:
    run_ingestion(settings)


def test_retrieval_metrics_regressions(settings: Settings) -> None:
    today = datetime.now(settings.timezone)
    base_dir = Path("evaluation/runs") / today.strftime("%Y%m%d")
    run_dir = base_dir / today.strftime("%H%M%S")
    result = evaluate(
        settings=settings,
        gold_path=Path("evaluation/gold_set.csv"),
        output_dir=run_dir,
        baseline_path=Path("evaluation/baseline/metrics.json"),
    )

    deltas = result["deltas"]
    regressions = {metric: delta for metric, delta in deltas.items() if delta < 0}
    for metric, delta in regressions.items():
        assert delta >= -0.03, f"{metric} regressed by {delta:.4f}, exceeding 3% threshold"

    assert Path(result["summary_csv"]).exists(), "Metrics CSV not generated"
    assert Path(result["summary_json"]).exists(), "Metrics summary JSON not generated"
