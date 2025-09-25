#!/usr/bin/env python3
"""Run simple end-to-end QA evaluation using expected answers.

For each gold example with an `expected_answer`, this script:
- calls the retrieval+generation pipeline (`answer_question`)
- computes token-level F1 between model response and expected
- computes embedding cosine similarity between response and expected

Outputs a CSV and JSON summary alongside the retrieval metrics outputs for the same day.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from collections import Counter
from collections.abc import Iterable
from pathlib import Path

import numpy as np

# Ensure repository root on sys.path for local imports
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
for candidate in (SRC, ROOT):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)

from atticus.config import AppSettings, load_settings  # noqa: E402
from atticus.embeddings import EmbeddingClient  # noqa: E402
from eval.runner import _default_output_dir, load_gold_set  # noqa: E402
from retriever.service import answer_question  # noqa: E402


def _tokens(text: str) -> list[str]:
    return [t for t in "".join(c.lower() if c.isalnum() else " " for c in text).split() if t]


def _f1(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    set_a = ta
    set_b = tb
    ca, cb = Counter(set_a), Counter(set_b)
    common = sum((ca & cb).values())
    if common == 0:
        return 0.0
    precision = common / max(1, sum(cb.values()))
    recall = common / max(1, sum(ca.values()))
    if precision + recall == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def _cosine(a: Iterable[float], b: Iterable[float]) -> float:
    va = np.array(list(a), dtype=float)
    vb = np.array(list(b), dtype=float)
    na = np.linalg.norm(va)
    nb = np.linalg.norm(vb)
    if na == 0 or nb == 0:
        return 0.0
    return float(va.dot(vb) / (na * nb))


def run_qa_eval(
    settings: AppSettings, gold_path: Path | None = None, output_dir: Path | None = None
) -> dict[str, object]:
    gold_path = gold_path or settings.gold_set_path
    output_dir = output_dir or _default_output_dir(settings)
    examples = [g for g in load_gold_set(gold_path) if g.expected_answer]

    output_dir.mkdir(parents=True, exist_ok=True)
    csv_path = output_dir / "qa_metrics.csv"
    json_path = output_dir / "qa_summary.json"

    if not examples:
        payload = {"count": 0, "avg_f1": 0.0, "avg_cosine": 0.0}
        json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
        return payload

    embed = EmbeddingClient(settings)
    f1_scores: list[float] = []
    cos_scores: list[float] = []
    rows: list[dict[str, object]] = []

    for ex in examples:
        ans = answer_question(ex.question, settings=settings)
        f1 = _f1(ans.response, ex.expected_answer or "")
        v_expected, v_response = embed.embed_texts([ex.expected_answer or "", ans.response])
        cos = _cosine(v_expected, v_response)
        top_doc = ans.citations[0].source_path if ans.citations else None
        f1_scores.append(f1)
        cos_scores.append(cos)
        rows.append(
            {
                "question": ex.question,
                "top_document": top_doc,
                "confidence": ans.confidence,
                "f1": round(f1, 4),
                "cosine": round(cos, 4),
            }
        )

    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=["question", "top_document", "confidence", "f1", "cosine"])
        writer.writeheader()
        writer.writerows(rows)
        writer.writerow(
            {
                "question": "AVERAGE",
                "top_document": "",
                "confidence": round(sum(r.get("confidence", 0.0) for r in rows) / len(rows), 4),
                "f1": round(sum(f1_scores) / len(f1_scores), 4),
                "cosine": round(sum(cos_scores) / len(cos_scores), 4),
            }
        )

    payload = {
        "count": len(rows),
        "avg_f1": round(sum(f1_scores) / len(f1_scores), 4),
        "avg_cosine": round(sum(cos_scores) / len(cos_scores), 4),
        "summary_csv": str(csv_path),
        "summary_json": str(json_path),
    }
    json_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return payload


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Run QA eval using expected answers in the gold set")
    p.add_argument("--gold-set", type=Path, help="Optional path to override the default gold set")
    p.add_argument("--output-dir", type=Path, help="Directory for storing QA eval outputs")
    p.add_argument("--config", type=Path, help="Path to an alternate config.yaml file")
    p.add_argument("--json", action="store_true", help="Print results as JSON to stdout")
    return p


def main() -> None:
    args = build_parser().parse_args()
    if args.config:
        os.environ["CONFIG_PATH"] = str(args.config)

    settings = load_settings()
    result = run_qa_eval(settings, gold_path=args.gold_set, output_dir=args.output_dir)
    if args.json or not args.output_dir:
        print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
