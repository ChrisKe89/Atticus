#!/usr/bin/env python3
"""Generate the next Atticus escalation identifier."""

from __future__ import annotations

import argparse
from pathlib import Path

from atticus.config import load_settings
from atticus.escalation import next_ae_id


def main() -> int:
    parser = argparse.ArgumentParser(description="Emit the next escalation identifier")
    parser.add_argument(
        "--counter",
        type=Path,
        default=None,
        help="Override counter file location (defaults to settings.escalation_counter_file)",
    )
    args = parser.parse_args()

    settings = load_settings()
    counter_path = args.counter or settings.escalation_counter_file
    ae_id = next_ae_id(counter_path)
    print(ae_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
