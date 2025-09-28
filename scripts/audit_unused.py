#!/usr/bin/env python3
"""Audit script for unused Python modules and dead code.

Runs vulture (if installed) against default project paths and prints a JSON
summary. The script degrades gracefully when optional tools are missing.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
DEFAULT_PATHS: list[str] = [
    "atticus",
    "api",
    "ingest",
    "retriever",
    "eval",
    "scripts",
    "tests",
]


def run_vulture(paths: list[str], min_confidence: int) -> dict[str, object]:
    executable = shutil.which("vulture")
    if executable is None:
        return {
            "tool": "vulture",
            "error": "vulture not installed. Install with `pip install vulture` or add to dev dependencies.",
        }

    cmd: list[str] = [executable, *paths, "--min-confidence", str(min_confidence), "--sort-by-size"]
    result = subprocess.run(cmd, capture_output=True, text=True, check=False)
    return {
        "tool": "vulture",
        "returncode": result.returncode,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip(),
    }


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Audit unused Python code via vulture")
    parser.add_argument("paths", nargs="*", default=DEFAULT_PATHS, help="Paths to inspect")
    parser.add_argument("--min-confidence", type=int, default=80, help="Minimum confidence threshold for vulture")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON output")
    args = parser.parse_args(argv)

    resolved_paths: list[str] = []
    for path in args.paths:
        candidate = Path(path)
        if candidate.exists():
            resolved_paths.append(str(candidate))
    if not resolved_paths:
        resolved_paths = DEFAULT_PATHS

    report = {"vulture": run_vulture(resolved_paths, args.min_confidence)}

    if args.json:
        json.dump(report, sys.stdout, indent=2)
        sys.stdout.write("\n")
    else:
        sys.stdout.write(json.dumps(report, indent=2))
        sys.stdout.write("\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
