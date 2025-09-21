"""Evaluation helpers for Atticus."""

from __future__ import annotations

import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Sequence, Tuple

import numpy as np

from .config import Settings
from .embedding import EmbeddingClient
from .logging_utils import configure_logging, log_event
from .retrieval import build_vector_store


@dataclass(slots=True)
class GoldExample:
    query: str
    relevant_documents: List[str]
    notes: str | None = None


@dataclass(slots=True)
class EvaluationMetrics:
    ndcg_at_10: float
    recall_at_50: float
    mrr: float

    def to_dict(self) -> Dict[str, float]:
        return {
            "nDCG@10": round(self.ndcg_at_10, 4),
            "Recall@50": round(self.recall_at_50, 4),
            "MRR": round(self.mrr, 4),
        }


def load_gold_set(path: Path) -> List[GoldExample]:
    examples: List[GoldExample] = []
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            relevant = [item.strip() for item in row.get("relevant_documents", "").split(";") if item.strip()]
            notes = row.get("notes") or None
            examples.append(GoldExample(query=row["query"].strip(), relevant_documents=relevant, notes=notes))
    return examples


def _dcg(relevances: Sequence[int]) -> float:
    return sum((2 ** rel - 1) / math.log2(idx + 2) for idx, rel in enumerate(relevances))


def _compute_query_metrics(results: List[Tuple[str, float]], relevant_docs: List[str]) -> Tuple[float, float, float]:
    if not relevant_docs:
        return 0.0, 0.0, 0.0

    relevances = [1 if doc in relevant_docs else 0 for doc, _ in results[:10]]
    dcg_value = _dcg(relevances)
    ideal_relevances = sorted([1] * min(len(relevant_docs), 10), reverse=True)
    idcg = _dcg(ideal_relevances) if ideal_relevances else 0.0
    ndcg = dcg_value / idcg if idcg else 0.0

    top50_docs = [doc for doc, _ in results[:50]]
    hits = sum(1 for doc in top50_docs if doc in relevant_docs)
    recall = hits / len(relevant_docs)

    mrr = 0.0
    for idx, (doc, _) in enumerate(results, start=1):
        if doc in relevant_docs:
            mrr = 1.0 / idx
            break

    return ndcg, recall, mrr


def evaluate(settings: Settings, gold_path: Path, output_dir: Path, baseline_path: Path) -> Dict[str, object]:
    logger = configure_logging(settings)
    store = build_vector_store(settings)
    client = EmbeddingClient(settings, logger=logger)
    gold_examples = load_gold_set(gold_path)

    ndcg_scores: List[float] = []
    recall_scores: List[float] = []
    mrr_scores: List[float] = []
    per_query_rows: List[Dict[str, object]] = []

    for example in gold_examples:
        embedding = np.array(client.embed_texts([example.query])[0], dtype=np.float32)
        results = store.query(embedding, top_k=50)
        result_docs = [(item.document_path, item.score) for item in results]
        ndcg, recall, mrr = _compute_query_metrics(result_docs, example.relevant_documents)
        ndcg_scores.append(ndcg)
        recall_scores.append(recall)
        mrr_scores.append(mrr)
        per_query_rows.append(
            {
                "query": example.query,
                "nDCG@10": round(ndcg, 4),
                "Recall@50": round(recall, 4),
                "MRR": round(mrr, 4),
                "top_document": result_docs[0][0] if result_docs else None,
            }
        )

    metrics = EvaluationMetrics(
        ndcg_at_10=sum(ndcg_scores) / len(ndcg_scores) if ndcg_scores else 0.0,
        recall_at_50=sum(recall_scores) / len(recall_scores) if recall_scores else 0.0,
        mrr=sum(mrr_scores) / len(mrr_scores) if mrr_scores else 0.0,
    )

    output_dir.mkdir(parents=True, exist_ok=True)
    summary_path = output_dir / "metrics.csv"
    with summary_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["query", "nDCG@10", "Recall@50", "MRR", "top_document"])
        writer.writeheader()
        writer.writerows(per_query_rows)
        writer.writerow({"query": "AVERAGE", **metrics.to_dict()})

    overall_path = output_dir / "summary.json"
    overall_path.write_text(json.dumps(metrics.to_dict(), indent=2) + "\n", encoding="utf-8")

    baseline_metrics = json.loads(baseline_path.read_text(encoding="utf-8"))
    deltas = {
        key: metrics.to_dict()[key] - baseline_metrics.get(key, 0.0) for key in metrics.to_dict()
    }

    log_event(
        logger,
        "evaluation_complete",
        metrics=metrics.to_dict(),
        deltas=deltas,
        baseline=str(baseline_path),
        output=str(output_dir),
    )

    return {
        "metrics": metrics.to_dict(),
        "deltas": deltas,
        "summary_csv": summary_path,
        "summary_json": overall_path,
    }
