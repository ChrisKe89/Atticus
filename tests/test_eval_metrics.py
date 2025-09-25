from __future__ import annotations

from eval.runner import _confidence_bucket, _compute_metrics, CONFIDENCE_BINS


def test_confidence_bucket_matches_ranges() -> None:
    bounds = {label: (lower, upper) for (lower, upper, label) in CONFIDENCE_BINS}
    assert _confidence_bucket(0.85) == ">=0.80"
    assert _confidence_bucket(0.705) == "0.70-0.79"
    assert _confidence_bucket(0.61) == "0.60-0.69"
    assert _confidence_bucket(0.1) == "<0.60"
    # inclusive upper edge
    lower, upper = bounds[">=0.80"]
    assert lower == 0.80
    assert upper > 1.0 - 1e-6


def test_compute_metrics_includes_hit_rate() -> None:
    metrics = _compute_metrics([0.9, 0.8], [0.7, 0.6], [0.5, 0.4], [1.0, 0.0])
    assert metrics["HitRate@5"] == 0.5
    assert metrics["nDCG@10"] == 0.85
