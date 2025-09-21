"""Evaluation harness computing nDCG@10, Recall@50, and MRR."""

from __future__ import annotations

import csv
import json
import math
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from atticus.config import AppSettings
from atticus.logging import configure_logging, log_event
from retriever.vector_store import VectorStore


@dataclass(slots=True)
class GoldExample:
    question: str
    relevant_documents: list[str]
    notes: str | None


@dataclass(slots=True)
class EvaluationResult:
    metrics: dict[str, float]
    deltas: dict[str, float]
    summary_csv: Path
    summary_json: Path


def load_gold_set(path: Path) -> list[GoldExample]:
    examples: list[GoldExample] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            question = row.get("question", "").strip()
            documents = [item.strip() for item in row.get("relevant_documents", "").split(";") if item.strip()]
            notes = row.get("notes") or None
            examples.append(GoldExample(question=question, relevant_documents=documents, notes=notes))
    return examples


def _dcg(relevances: Sequence[int]) -> float:
    return sum(
        ((2 ** rel - 1) / math.log2(idx + 2) for idx, rel in enumerate(relevances)),
        0.0,
    )


def _evaluate_query(results: Sequence[str], relevant_docs: list[str]) -> tuple[float, float, float]:
    if not relevant_docs:
        return 0.0, 0.0, 0.0
    ideal = sorted([1] * min(len(relevant_docs), 10), reverse=True)
    idcg = _dcg(ideal) if ideal else 0.0
    gains = [1 if doc in relevant_docs else 0 for doc in results[:10]]
    dcg = _dcg(gains)
    ndcg = dcg / idcg if idcg else 0.0

    top50 = results[:50]
    hits = sum(1 for doc in top50 if doc in relevant_docs)
    recall = hits / len(relevant_docs)

    mrr = 0.0
    for idx, doc in enumerate(results, start=1):
        if doc in relevant_docs:
            mrr = 1.0 / idx
            break
    return ndcg, recall, mrr


def run_evaluation(
    settings: AppSettings | None = None,
    gold_path: Path | None = None,
    baseline_path: Path | None = None,
    output_dir: Path | None = None,
) -> EvaluationResult:
    settings = settings or AppSettings()
    gold_path = gold_path or settings.gold_set_path
    baseline_path = baseline_path or settings.baseline_path
    output_dir = output_dir or (settings.evaluation_runs_dir / datetime.now(tz=settings.tzinfo).strftime("%Y%m%d"))

    logger = configure_logging(settings)
    store = VectorStore(settings, logger)
    gold_examples = load_gold_set(gold_path)

    ndcg_scores: list[float] = []
    recall_scores: list[float] = []
    mrr_scores: list[float] = []
    per_query_rows: list[dict[str, object]] = []

    for example in gold_examples:
        results = store.search(example.question, top_k=50, filters=None, hybrid=True)
        documents = [result.source_path for result in results]
        ndcg, recall, mrr = _evaluate_query(documents, example.relevant_documents)
        ndcg_scores.append(ndcg)
        recall_scores.append(recall)
        mrr_scores.append(mrr)
        per_query_rows.append(
            {
                "query": example.question,
                "nDCG@10": round(ndcg, 4),
                "Recall@50": round(recall, 4),
                "MRR": round(mrr, 4),
                "top_document": documents[0] if documents else None,
            }
        )

    metrics = {
        "nDCG@10": round(sum(ndcg_scores) / len(ndcg_scores), 4) if ndcg_scores else 0.0,
        "Recall@50": round(sum(recall_scores) / len(recall_scores), 4) if recall_scores else 0.0,
        "MRR": round(sum(mrr_scores) / len(mrr_scores), 4) if mrr_scores else 0.0,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_csv = output_dir / "metrics.csv"
    summary_json = output_dir / "summary.json"

    with summary_csv.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["query", "nDCG@10", "Recall@50", "MRR", "top_document"])
        writer.writeheader()
        writer.writerows(per_query_rows)
        writer.writerow({"query": "AVERAGE", **metrics})

    summary_json.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")

    if baseline_path.exists():
        baseline_metrics = json.loads(baseline_path.read_text(encoding="utf-8"))
    else:
        baseline_metrics = {"nDCG@10": 0.0, "Recall@50": 0.0, "MRR": 0.0}

    deltas = {key: round(metrics[key] - baseline_metrics.get(key, 0.0), 4) for key in metrics}

    log_event(
        logger,
        "evaluation_complete",
        metrics=metrics,
        deltas=deltas,
        gold_examples=len(gold_examples),
        output=str(output_dir),
    )

    return EvaluationResult(metrics=metrics, deltas=deltas, summary_csv=summary_csv, summary_json=summary_json)

