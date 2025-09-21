#!/usr/bin/env python3
"""Legacy wrapper for the Atticus ingestion CLI."""

from __future__ import annotations

import runpy
from pathlib import Path


def main() -> None:
    target = Path(__file__).with_name("ingest.py")
    runpy.run_path(str(target), run_name="__main__")


if __name__ == "__main__":
    main()
