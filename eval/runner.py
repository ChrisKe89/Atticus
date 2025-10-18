"""Evaluation harness computing nDCG@10, Recall@50, and MRR.

This module lazily imports heavy runtime dependencies so its pure functions
can be unit tested without requiring optional system packages (e.g. pgvector server extension).
"""

from __future__ import annotations

import csv
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import UTC, datetime
from html import escape
from pathlib import Path
from typing import TYPE_CHECKING, Protocol, cast, runtime_checkable

if TYPE_CHECKING:  # avoid importing heavy deps at import time
    from core.config import AppSettings
    from retriever.vector_store import RetrievalMode, SearchResult


def _default_output_dir(settings: AppSettings) -> Path:
    return settings.evaluation_runs_dir / datetime.now(tz=settings.tzinfo).strftime("%Y%m%d")


@dataclass(slots=True)
class GoldExample:
    question: str
    relevant_documents: list[str]
    expected_answer: str | None
    notes: str | None


@dataclass(slots=True)
class EvaluationMode:
    mode: str
    metrics: dict[str, float]
    deltas: dict[str, float]
    summary_csv: Path
    summary_json: Path
    summary_html: Path


@dataclass(slots=True)
class EvaluationResult:
    metrics: dict[str, float]
    deltas: dict[str, float]
    summary_csv: Path
    summary_json: Path
    summary_html: Path
    modes: list[EvaluationMode]
    modes_summary: Path | None
    thresholds: dict[str, float]
    threshold_failures: dict[str, dict[str, float]]


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

            documents = [
                _canon(item)
                for item in row.get("relevant_documents", "").split(";")
                if item and item.strip()
            ]
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


def _evaluate_query(
    results_doc_keys: Sequence[str], relevant_docs: list[str]
) -> tuple[float, float, float]:
    if not relevant_docs:
        return 0.0, 0.0, 0.0
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
    # Clamp to [0,1]
    return min(ndcg, 1.0), min(recall, 1.0), min(mrr, 1.0)


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
    ndcg_scores: Sequence[float], recall_scores: Sequence[float], mrr_scores: Sequence[float]
) -> dict[str, float]:
    return {
        "nDCG@10": round(sum(ndcg_scores) / len(ndcg_scores), 4) if ndcg_scores else 0.0,
        "Recall@50": round(sum(recall_scores) / len(recall_scores), 4) if recall_scores else 0.0,
        "MRR": round(sum(mrr_scores) / len(mrr_scores), 4) if mrr_scores else 0.0,
    }


def _format_float(value: object) -> str:
    try:
        return f"{float(value):.4f}"
    except (TypeError, ValueError):
        return ""


def _write_outputs(
    output_dir: Path, rows: Sequence[dict[str, object]], metrics: dict[str, float]
) -> tuple[Path, Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    summary_csv = output_dir / "metrics.csv"
    summary_json = output_dir / "summary.json"
    summary_html = output_dir / "metrics.html"

    with summary_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=["query", "nDCG@10", "Recall@50", "MRR", "top_document"]
        )
        writer.writeheader()
        writer.writerows(rows)
        writer.writerow({"query": "AVERAGE", **metrics})

    summary_json.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")

    generated_at = datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%SZ")
    metrics_rows = "".join(
        f'<tr><th scope="row">{escape(name)}</th><td>{_format_float(value)}</td></tr>'
        for name, value in metrics.items()
    )
    query_rows = "".join(
        "<tr>"
        f"<td>{escape(str(row.get('query', '')))}</td>"
        f"<td>{_format_float(row.get('nDCG@10'))}</td>"
        f"<td>{_format_float(row.get('Recall@50'))}</td>"
        f"<td>{_format_float(row.get('MRR'))}</td>"
        f"<td>{escape(str(row.get('top_document') or ''))}</td>"
        "</tr>"
        for row in rows
    )

    html_report = (
        "<!DOCTYPE html>"
        '<html lang="en">'
        "<head>"
        '<meta charset="utf-8">'
        "<title>Atticus Evaluation Summary</title>"
        "<style>"
        "body{font-family:Inter,Arial,sans-serif;background:#0f172a;color:#e2e8f0;margin:0;padding:2rem;}"
        "h1{margin-top:0;font-size:1.75rem;}"
        "table{border-collapse:collapse;width:100%;margin-top:1.5rem;background:#1e293b;border-radius:0.5rem;overflow:hidden;}"
        "th,td{padding:0.75rem 1rem;text-align:left;border-bottom:1px solid rgba(148,163,184,0.25);}"
        "th{width:18rem;font-weight:600;}"
        "tbody tr:last-child td{border-bottom:none;}"
        "section + section{margin-top:2rem;}"
        "caption{caption-side:top;font-weight:600;font-size:1.1rem;margin-bottom:0.5rem;color:#f8fafc;}"
        "</style>"
        "</head>"
        "<body>"
        "<h1>Atticus Evaluation Summary</h1>"
        f"<p>Generated at <strong>{escape(generated_at)}</strong>. Metrics compare retrieval output against the configured gold set.</p>"
        "<section>"
        "<table>"
        "<caption>Aggregate Metrics</caption>"
        "<tbody>"
        f"{metrics_rows}"
        "</tbody>"
        "</table>"
        "</section>"
        "<section>"
        "<table>"
        "<caption>Per-query Breakdown</caption>"
        "<thead><tr><th>Query</th><th>nDCG@10</th><th>Recall@50</th><th>MRR</th><th>Top Document</th></tr></thead>"
        f"<tbody>{query_rows}</tbody>"
        "</table>"
        "</section>"
        "</body></html>"
    )

    summary_html.write_text(html_report, encoding="utf-8")
    return summary_csv, summary_json, summary_html


def _write_modes_summary(output_dir: Path, modes: Sequence[EvaluationMode]) -> Path:
    payload = {
        item.mode: {
            "metrics": item.metrics,
            "deltas": item.deltas,
            "summary_csv": str(item.summary_csv),
            "summary_json": str(item.summary_json),
            "summary_html": str(item.summary_html),
        }
        for item in modes
    }
    summary_path = output_dir / "retrieval_modes.json"
    summary_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return summary_path


def _load_baseline(path: Path) -> dict[str, dict[str, float]]:
    if not path.exists():
        return {}

    data = cast(dict[str, object], json.loads(path.read_text(encoding="utf-8")))
    if not data:
        return {}

    # Support legacy single-mode baseline schema.
    if all(isinstance(value, (int, float)) for value in data.values()):
        return {"hybrid": {key: float(value) for key, value in data.items()}}

    metrics_map: dict[str, dict[str, float]] = {}
    for mode, metrics in data.items():
        if not isinstance(metrics, Mapping):
            continue
        metrics_map[str(mode)] = {
            key: float(metrics.get(key, 0.0)) for key in ("nDCG@10", "Recall@50", "MRR")
        }
    return metrics_map


def _resolve_modes(
    requested: Sequence[str] | None, fallback: Sequence[str]
) -> list["RetrievalMode"]:  # noqa: UP037
    from retriever.vector_store import RetrievalMode  # noqa: PLC0415

    options = {mode.value: mode for mode in RetrievalMode}
    selected: list[RetrievalMode] = []
    for item in requested or fallback:
        key = item.lower()
        if key not in options:
            raise ValueError(
                f"Unsupported evaluation mode '{item}'. Choose from {sorted(options)}."
            )
        mode = options[key]
        if mode not in selected:
            selected.append(mode)
    if not selected:
        selected.append(RetrievalMode.HYBRID)
    return selected


def run_evaluation(
    settings: AppSettings | None = None,
    gold_path: Path | None = None,
    baseline_path: Path | None = None,
    output_dir: Path | None = None,
    modes: Sequence[str] | None = None,
) -> EvaluationResult:
    # Lazy imports to keep unit tests lightweight
    from core.config import load_settings  # noqa: PLC0415
    from atticus.logging import configure_logging, log_event  # noqa: PLC0415
    from retriever.vector_store import VectorStore  # noqa: PLC0415

    settings = settings or load_settings()
    gold_path = gold_path or settings.gold_set_path
    baseline_path = baseline_path or settings.baseline_path
    output_dir = output_dir or _default_output_dir(settings)

    logger = configure_logging(settings)
    store = VectorStore(settings, logger)
    gold_examples = load_gold_set(gold_path)

    baseline_metrics = _load_baseline(baseline_path)
    configured_modes = getattr(settings, "evaluation_modes", ["hybrid"])
    resolved_modes = _resolve_modes(modes, configured_modes)

    mode_results: list[EvaluationMode] = []

    for retrieval_mode in resolved_modes:
        ndcg_scores: list[float] = []
        recall_scores: list[float] = []
        mrr_scores: list[float] = []
        per_query_rows: list[dict[str, object]] = []

        for example in gold_examples:
            results = store.search(
                example.question,
                top_k=50,
                filters=None,
                mode=retrieval_mode,
            )
            doc_keys, documents_primary = _build_doc_keys(results)

            ndcg, recall, mrr = _evaluate_query(doc_keys, example.relevant_documents)
            ndcg_scores.append(ndcg)
            recall_scores.append(recall)
            mrr_scores.append(mrr)
            per_query_rows.append(
                {
                    "query": example.question,
                    "nDCG@10": round(ndcg, 4),
                    "Recall@50": round(recall, 4),
                    "MRR": round(mrr, 4),
                    "top_document": documents_primary[0] if documents_primary else None,
                }
            )

        metrics = _compute_metrics(ndcg_scores, recall_scores, mrr_scores)
        mode_dir = output_dir
        if len(resolved_modes) > 1:
            mode_dir = output_dir / f"mode-{retrieval_mode.value}"
        summary_csv, summary_json, summary_html = _write_outputs(mode_dir, per_query_rows, metrics)

        baseline = baseline_metrics.get(retrieval_mode.value) or baseline_metrics.get("hybrid", {})
        deltas = {key: round(metrics[key] - baseline.get(key, 0.0), 4) for key in metrics}

        mode_results.append(
            EvaluationMode(
                mode=retrieval_mode.value,
                metrics=metrics,
                deltas=deltas,
                summary_csv=summary_csv,
                summary_json=summary_json,
                summary_html=summary_html,
            )
        )

    summary_path: Path | None = None
    if len(mode_results) > 1:
        summary_path = _write_modes_summary(output_dir, mode_results)

    primary = mode_results[0]

    thresholds = dict(getattr(settings, "evaluation_thresholds", {}))
    threshold_failures: dict[str, dict[str, float]] = {}
    if thresholds:
        for mode in mode_results:
            failing: dict[str, float] = {}
            for metric, minimum in thresholds.items():
                value = mode.metrics.get(metric, 0.0)
                if value < minimum:
                    failing[metric] = value
            if failing:
                threshold_failures[mode.mode] = failing

    log_event(
        logger,
        "evaluation_complete",
        metrics=primary.metrics,
        deltas=primary.deltas,
        gold_examples=len(gold_examples),
        output=str(output_dir),
        modes=[mode.mode for mode in mode_results],
    )

    return EvaluationResult(
        metrics=primary.metrics,
        deltas=primary.deltas,
        summary_csv=primary.summary_csv,
        summary_json=primary.summary_json,
        summary_html=primary.summary_html,
        modes=mode_results,
        modes_summary=summary_path,
        thresholds=thresholds,
        threshold_failures=threshold_failures,
    )


def main() -> None:
    from core.config import load_settings  # noqa: PLC0415

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
