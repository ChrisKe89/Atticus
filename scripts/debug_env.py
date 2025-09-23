#!/usr/bin/env python3
"""Inspect Atticus environment configuration without leaking secrets."""

from __future__ import annotations

import json
from pathlib import Path

from atticus.config import environment_diagnostics, reset_settings_cache


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    diagnostics = environment_diagnostics()
    diagnostics["repo_root"] = str(root)
    print(json.dumps(diagnostics, indent=2, sort_keys=True))
    reset_settings_cache()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
