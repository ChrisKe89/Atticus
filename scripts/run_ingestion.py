#!/usr/bin/env python3
"""Run the Atticus ingestion pipeline."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from dataclasses import asdict

from atticus.config import AppSettings
from atticus.ingestion.pipeline import IngestionOptions, ingest_corpus


def main() -> None:
    settings = AppSettings()
    options = IngestionOptions()
    summary = ingest_corpus(settings=settings, options=options)
    print(json.dumps(asdict(summary), indent=2))


if __name__ == "__main__":
    main()
