#!/usr/bin/env python3
"""Inspect Atticus environment configuration without leaking secrets."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from atticus.config import environment_diagnostics, reset_settings_cache  # noqa: E402


def main() -> int:
    diagnostics = environment_diagnostics()
    diagnostics["repo_root"] = str(ROOT)
    print(json.dumps(diagnostics, indent=2, sort_keys=True))
    reset_settings_cache()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
