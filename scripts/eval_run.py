#!/usr/bin/env python3
"""Run the Atticus evaluation harness from the command line."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
for candidate in (SRC, ROOT):
    candidate_str = str(candidate)
    if candidate_str not in sys.path:
        sys.path.insert(0, candidate_str)

from atticus.config import load_settings  # noqa: E402
from eval.runner import run_evaluation  # noqa: E402


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Execute the retrieval evaluation harness")
    parser.add_argument(
        "--gold-set",
        type=Path,
        help="Optional path to override the default gold set",
    )
    parser.add_argument(
        "--baseline",
        type=Path,
        help="Optional path to override the baseline metrics JSON",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        help="Directory for storing evaluation outputs",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to an alternate config.yaml file",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print results as JSON to stdout",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.config:
        os.environ["CONFIG_PATH"] = str(args.config)

    settings = load_settings()
    result = run_evaluation(
        settings=settings,
        gold_path=args.gold_set,
        baseline_path=args.baseline,
        output_dir=args.output_dir,
    )

    payload = {
        "metrics": result.metrics,
        "deltas": result.deltas,
        "summary_csv": str(result.summary_csv),
        "summary_json": str(result.summary_json),
    }

    if args.json or not args.output_dir:
        print(json.dumps(payload, indent=2))
    else:
        (args.output_dir / "run_summary.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")

    threshold = settings.eval_regression_threshold / 100.0
    if any(delta < -threshold for delta in result.deltas.values()):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
