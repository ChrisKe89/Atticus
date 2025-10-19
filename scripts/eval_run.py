#!/usr/bin/env python3
"""Run the Atticus evaluation harness from the command line."""

from __future__ import annotations

import argparse
import json
import os
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from atticus.logging_utils import get_logger  # noqa: E402
from core.config import load_settings  # noqa: E402
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


def _relative_href(base: Path, target: Path) -> str:
    try:
        rel = target.relative_to(base)
    except ValueError:
        rel = target
    return rel.as_posix()


def _format_metric(value: object) -> str:
    try:
        return f"{float(value):.4f}"
    except (TypeError, ValueError):
        return "—"


def _write_ci_index(output_dir: Path, result) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    metrics_rows = "".join(
        f"<tr><th>{escape(name)}</th><td>{_format_metric(val)}</td></tr>"
        for name, val in (result.metrics or {}).items()
    )
    mode_links = "".join(
        f'<li><a href="{escape(_relative_href(output_dir, Path(mode.summary_html)))}">'
        f"{escape(mode.mode.title())}</a></li>"
        for mode in getattr(result, "modes", [])
    )
    index_html = f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
<meta charset=\"utf-8\">
<title>Atticus Evaluation Dashboard</title>
<style>
body{{font-family:Inter,Arial,sans-serif;background:#0f172a;color:#e2e8f0;margin:0;padding:2rem;}}
h1{{margin-top:0;font-size:1.75rem;}}
h2{{margin-top:2rem;font-size:1.25rem;}}
table{{border-collapse:collapse;width:100%;max-width:480px;background:#1e293b;border-radius:0.75rem;overflow:hidden;}}
th,td{{padding:0.75rem 1rem;text-align:left;border-bottom:1px solid rgba(148,163,184,0.25);}}
th{{width:16rem;font-weight:600;}}
tbody tr:last-child td{{border-bottom:none;}}
ul{{margin-top:1.5rem;padding-left:1.25rem;}}
a{{color:#38bdf8;text-decoration:none;}}
a:hover{{text-decoration:underline;}}
.sr-only{{position:absolute;width:1px;height:1px;padding:0;margin:-1px;overflow:hidden;clip:rect(0,0,0,0);border:0;}}
</style>
</head>
<body>
<h1>Atticus Evaluation Dashboard</h1>
<p>Artifacts below include interactive HTML dashboards for each retrieval mode.</p>
<table><caption class=\"sr-only\">Aggregate Metrics</caption><tbody>
{metrics_rows or '<tr><td colspan="2">No metrics available.</td></tr>'}
</tbody></table>
<h2>Dashboards</h2>
<ul>{mode_links or "<li>No evaluation modes recorded.</li>"}</ul>
</body></html>
"""
    (output_dir / "index.html").write_text(index_html, encoding="utf-8")


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

    if args.output_dir:
        _write_ci_index(args.output_dir, result)

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
