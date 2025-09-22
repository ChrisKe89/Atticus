#!/usr/bin/env python3
"""CLI entrypoint for the Atticus ingestion pipeline."""

from __future__ import annotations

import argparse
import json
import os
from collections.abc import Sequence
from dataclasses import asdict
from pathlib import Path

from atticus.config import load_settings
from ingest.pipeline import IngestionOptions, ingest_corpus


def _paths(value: Sequence[str] | None) -> list[Path] | None:
    if not value:
        return None
    return [Path(item).expanduser().resolve() for item in value]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the Atticus ingestion pipeline")
    parser.add_argument(
        "--paths",
        nargs="*",
        help="Optional subset of files or directories to ingest",
    )
    parser.add_argument(
        "--full-refresh",
        action="store_true",
        help="Force reprocessing of all documents even if unchanged",
    )
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to an alternate config.yaml file",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Optional path to write the ingestion summary JSON",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.config:
        os.environ["CONFIG_PATH"] = str(args.config)

    settings = load_settings()
    options = IngestionOptions(full_refresh=bool(args.full_refresh), paths=_paths(args.paths))
    summary = ingest_corpus(settings=settings, options=options)
    payload = asdict(summary)

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    else:
        print(json.dumps(payload, indent=2, default=str))


if __name__ == "__main__":
    main()
