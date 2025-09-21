#!/usr/bin/env python3
"""Run the Atticus ingestion pipeline."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from atticus.config import Settings
from atticus.ingestion.pipeline import run_ingestion


def main() -> None:
    settings = Settings()
    summary = run_ingestion(settings)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
