"""Evaluation harness computing nDCG@10, Recall@50, and MRR.

This module lazily imports heavy runtime dependencies so its pure functions
can be unit tested without requiring optional system packages (e.g. FAISS).
"""

from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:  # avoid importing heavy deps at import time
    from atticus.config import AppSettings
    from retriever.vector_store import SearchResult


def _default_output_dir(settings: AppSettings) -> Path:
    return settings.evaluation_runs_dir / datetime.now(tz=settings.tzinfo).strftime("%Y%m%d")


@dataclass(slots=True)
class GoldExample:
    question: str
    relevant_documents: list[str]
    expected_answer: str | None
    notes: str | None


@dataclass(slots=True)
class EvaluationResult:
    metrics: dict[str, object]
    deltas: dict[str, float]
    summary_csv: Path
    summary_json: Path


def load_gold_set(path: Path) -> list[GoldExample]:
    examples: list[GoldExample] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            question = row.get("question", "").strip()

            # Normalize gold document paths for cross-platform comparisons
            def _canon(p: str) -> str:
                try:
                    return Path(p.strip()).as_posix().lower()
                except Exception:
                    return p.strip().replace("\\", "/").lower()

            documents = [_canon(item) for item in row.get("relevant_documents", "").split(";") if item and item.strip()]
            expected = (row.get("expected_answer") or "").strip() or None
            notes = row.get("notes") or None
            examples.append(
                GoldExample(
                    question=question,
                    relevant_documents=documents,
                    expected_answer=expected,
                    notes=notes,
                )
            )
    return examples


def _dcg(relevances: Sequence[int]) -> float:
    return sum(
        ((2**rel - 1) / math.log2(idx + 2) for idx, rel in enumerate(relevances)),
        0.0,
    )


CONFIDENCE_BINS: tuple[tuple[float, float, str], ...] = (
    (0.80, 1.01, ">=0.80"),
    (0.70, 0.80, "0.70-0.79"),
    (0.60, 0.70, "0.60-0.69"),
    (0.0, 0.60, "<0.60"),
)


def _confidence_bucket(confidence: float) -> str:
    for lower, upper, label in CONFIDENCE_BINS:
        if lower <= confidence < upper:
            return label
    return "<0.60"


def _evaluate_query(results_doc_keys: Sequence[str], relevant_docs: list[str]) -> tuple[float, float, float, float]:
    if not relevant_docs:
        return 0.0, 0.0, 0.0, 0.0
    # Build the set of relevant document keys (by basename only)
    relevant_keys: set[str] = {Path(doc).name for doc in relevant_docs}

    ideal = sorted([1] * min(len(relevant_keys), 10), reverse=True)
    idcg = _dcg(ideal) if ideal else 0.0
    gains = [1 if doc_key in relevant_keys else 0 for doc_key in results_doc_keys[:10]]
    dcg = _dcg(gains)
    ndcg = dcg / idcg if idcg else 0.0

    top50 = results_doc_keys[:50]
    hits = sum(1 for key in top50 if key in relevant_keys)
    recall = hits / max(1, len(relevant_keys))

    mrr = 0.0
    for idx, key in enumerate(results_doc_keys, start=1):
        if key in relevant_keys:
            mrr = 1.0 / idx
            break
    hit = 1.0 if any(key in relevant_keys for key in results_doc_keys[:5]) else 0.0
    # Clamp to [0,1]
    return min(ndcg, 1.0), min(recall, 1.0), min(mrr, 1.0), hit


def _canon(p: str) -> str:
    """Canonicalize a path-like string for comparison."""
    try:
        return Path(p).as_posix().lower()
    except Exception:
        return str(p).replace("\\", "/").lower()


@runtime_checkable
class _HasSource(Protocol):
    source_path: str
    metadata: Mapping[str, str] | None


def _build_doc_keys(results: Sequence[SearchResult]) -> tuple[list[str], list[str]]:
    """Produce unique document keys and primary paths from search results."""
    seen_docs: set[str] = set()
    doc_keys: list[str] = []
    documents_primary: list[str] = []
    for result in results:
        primary = _canon(result.source_path)
        meta = getattr(result, "metadata", None)
        src = meta.get("source") if meta else None
        key_source = _canon(src) if src else primary
        doc_key = Path(key_source).name
        if doc_key in seen_docs:
            continue
        seen_docs.add(doc_key)
        doc_keys.append(doc_key)
        documents_primary.append(primary)
    return doc_keys, documents_primary


def _compute_metrics(
    ndcg_scores: Sequence[float],
    recall_scores: Sequence[float],
    mrr_scores: Sequence[float],
    hit_scores: Sequence[float],
) -> dict[str, float]:
    return {
        "nDCG@10": round(sum(ndcg_scores) / len(ndcg_scores), 4) if ndcg_scores else 0.0,
        "Recall@50": round(sum(recall_scores) / len(recall_scores), 4) if recall_scores else 0.0,
        "MRR": round(sum(mrr_scores) / len(mrr_scores), 4) if mrr_scores else 0.0,
        "HitRate@5": round(sum(hit_scores) / len(hit_scores), 4) if hit_scores else 0.0,
    }


def _write_outputs(
    output_dir: Path, rows: Sequence[dict[str, object]], metrics: dict[str, object]
) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_csv = output_dir / "metrics.csv"
    summary_json = output_dir / "summary.json"

    with summary_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "query",
                "nDCG@10",
                "Recall@50",
                "MRR",
                "HitRate@5",
                "confidence",
                "confidence_bin",
                "top_document",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)
        overall = metrics.get("overall", {}) if isinstance(metrics, dict) else {}
        if isinstance(overall, dict):
            writer.writerow({"query": "AVERAGE", **overall})

    summary_json.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")
    return summary_csv, summary_json


def _load_baseline(path: Path) -> dict[str, float]:
    if path.exists():
        raw = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(raw, dict) and "overall" in raw:
            overall = raw.get("overall", {})
            if isinstance(overall, dict):
                return {
                    "nDCG@10": float(overall.get("nDCG@10", 0.0)),
                    "Recall@50": float(overall.get("Recall@50", 0.0)),
                    "MRR": float(overall.get("MRR", 0.0)),
                    "HitRate@5": float(overall.get("HitRate@5", 0.0)),
                }
        if isinstance(raw, dict):
            return {
                "nDCG@10": float(raw.get("nDCG@10", 0.0)),
                "Recall@50": float(raw.get("Recall@50", 0.0)),
                "MRR": float(raw.get("MRR", 0.0)),
                "HitRate@5": float(raw.get("HitRate@5", 0.0)),
            }
    return {"nDCG@10": 0.0, "Recall@50": 0.0, "MRR": 0.0, "HitRate@5": 0.0}


def run_evaluation(
    settings: AppSettings | None = None,
    gold_path: Path | None = None,
    baseline_path: Path | None = None,
    output_dir: Path | None = None,
) -> EvaluationResult:
    # Lazy imports to keep unit tests lightweight
    from atticus.config import load_settings  # noqa: PLC0415
    from atticus.logging import configure_logging, log_event  # noqa: PLC0415
    from retriever.vector_store import VectorStore  # noqa: PLC0415

    settings = settings or load_settings()
    gold_path = gold_path or settings.gold_set_path
    baseline_path = baseline_path or settings.baseline_path
    output_dir = output_dir or _default_output_dir(settings)

    logger = configure_logging(settings)
    store = VectorStore(settings, logger)
    gold_examples = load_gold_set(gold_path)

    ndcg_scores: list[float] = []
    recall_scores: list[float] = []
    mrr_scores: list[float] = []
    hit_scores: list[float] = []
    per_query_rows: list[dict[str, object]] = []
    bin_scores: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: {"ndcg": [], "recall": [], "mrr": [], "hit": []}
    )
    bin_counts: dict[str, int] = defaultdict(int)

    from retriever.service import estimate_confidence  # noqa: PLC0415

    for example in gold_examples:
        results = store.search(example.question, top_k=50, filters=None, hybrid=True)
        # Unique documents by basename (prefer metadata.source)
        doc_keys, documents_primary = _build_doc_keys(results)

        ndcg, recall, mrr, hit = _evaluate_query(doc_keys, example.relevant_documents)
        confidence = estimate_confidence(results, settings)
        bucket = _confidence_bucket(confidence)

        ndcg_scores.append(ndcg)
        recall_scores.append(recall)
        mrr_scores.append(mrr)
        hit_scores.append(hit)

        bucket_scores = bin_scores[bucket]
        bucket_scores["ndcg"].append(ndcg)
        bucket_scores["recall"].append(recall)
        bucket_scores["mrr"].append(mrr)
        bucket_scores["hit"].append(hit)
        bin_counts[bucket] += 1

        per_query_rows.append(
            {
                "query": example.question,
                "nDCG@10": round(ndcg, 4),
                "Recall@50": round(recall, 4),
                "MRR": round(mrr, 4),
                "HitRate@5": round(hit, 4),
                "confidence": round(confidence, 2),
                "confidence_bin": bucket,
                "top_document": documents_primary[0] if documents_primary else None,
            }
        )

    overall_metrics = _compute_metrics(ndcg_scores, recall_scores, mrr_scores, hit_scores)

    confidence_metrics: dict[str, dict[str, float | int]] = {}
    for _, _, label in CONFIDENCE_BINS:
        bucket_values = bin_scores.get(label)
        if bucket_values:
            metrics_value = _compute_metrics(
                bucket_values["ndcg"], bucket_values["recall"], bucket_values["mrr"], bucket_values["hit"]
            )
        else:
            metrics_value = _compute_metrics([], [], [], [])
        metrics_value_with_count: dict[str, float | int] = dict(metrics_value)
        metrics_value_with_count["count"] = bin_counts.get(label, 0)
        confidence_metrics[label] = metrics_value_with_count

    metrics: dict[str, object] = {
        "overall": overall_metrics,
        "confidence_bins": confidence_metrics,
    }

    summary_csv, summary_json = _write_outputs(output_dir, per_query_rows, metrics)

    baseline_metrics = _load_baseline(baseline_path)

    deltas = {key: round(overall_metrics.get(key, 0.0) - baseline_metrics.get(key, 0.0), 4) for key in overall_metrics}

    log_event(
        logger,
        "evaluation_complete",
        metrics=metrics,
        deltas=deltas,
        gold_examples=len(gold_examples),
        output=str(output_dir),
    )

    return EvaluationResult(metrics=metrics, deltas=deltas, summary_csv=summary_csv, summary_json=summary_json)


def main() -> None:
    from atticus.config import load_settings  # noqa: PLC0415

    settings = load_settings()
    result = run_evaluation(settings=settings)
    payload = {
        "metrics": result.metrics,
        "deltas": result.deltas,
        "summary_csv": str(result.summary_csv),
        "summary_json": str(result.summary_json),
    }
    print(json.dumps(payload, indent=2))


if __name__ == "__main__":
    main()
