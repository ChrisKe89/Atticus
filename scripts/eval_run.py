#!/usr/bin/env python3
"""Run the Atticus evaluation harness from the command line."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from atticus.config import load_settings  # noqa: E402
from atticus.logging_utils import get_logger  # noqa: E402
from eval.runner import run_evaluation  # noqa: E402

log = get_logger("eval_run")


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
    parser.add_argument(
        "--mode",
        dest="modes",
        action="append",
        choices=["hybrid", "vector", "lexical"],
        help="Retrieval mode to evaluate (may be passed multiple times)",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.config:
        os.environ["CONFIG_PATH"] = str(args.config)

    settings = load_settings()
    log.info(
        "eval_start",
        gold_override=bool(args.gold_set),
        baseline_override=bool(args.baseline),
        output_dir=str(args.output_dir) if args.output_dir else None,
    )
    result = run_evaluation(
        settings=settings,
        gold_path=args.gold_set,
        baseline_path=args.baseline,
        output_dir=args.output_dir,
        modes=args.modes,
    )

    payload = {
        "metrics": result.metrics,
        "deltas": result.deltas,
        "summary_csv": str(result.summary_csv),
        "summary_json": str(result.summary_json),
        "summary_html": str(result.summary_html),
        "thresholds": result.thresholds,
        "threshold_failures": result.threshold_failures,
        "modes": [
            {
                "mode": mode.mode,
                "metrics": mode.metrics,
                "deltas": mode.deltas,
                "summary_csv": str(mode.summary_csv),
                "summary_json": str(mode.summary_json),
                "summary_html": str(mode.summary_html),
            }
            for mode in result.modes
        ],
        "modes_summary": str(result.modes_summary) if result.modes_summary else None,
    }

    if args.json or not args.output_dir:
        log.info("eval_result", **payload)
    else:
        summary_path = args.output_dir / "run_summary.json"
        summary_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        log.info("eval_summary_written", path=str(summary_path))

    threshold = settings.eval_regression_threshold / 100.0
    if result.threshold_failures:
        log.error(
            "eval_threshold_breach",
            thresholds=result.thresholds,
            failures=result.threshold_failures,
        )
        raise SystemExit(1)
    if any(delta < -threshold for delta in result.deltas.values()):
        log.error("eval_regression_detected", threshold=threshold, deltas=result.deltas)
        raise SystemExit(1)
    log.info("eval_ok")


if __name__ == "__main__":
    main()
