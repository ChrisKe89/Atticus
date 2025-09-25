#!/usr/bin/env python3
"""Lightweight UI sanity check used by `make e2e`."""

from __future__ import annotations

import sys
from pathlib import Path

REQUIRED_SNIPPETS = [
    "Atticus",
    'id="escalation-banner"',
    'id="chat-stream"',
]


def main() -> int:
    template = Path("web/templates/main.html")
    if not template.exists():
        print(f"[ui_ping] missing template: {template}", file=sys.stderr)
        return 1

    contents = template.read_text(encoding="utf-8")
    missing = [snippet for snippet in REQUIRED_SNIPPETS if snippet not in contents]
    if missing:
        print(f"[ui_ping] template missing snippets: {', '.join(missing)}", file=sys.stderr)
        return 1

    print("[ui_ping] UI template contains required escalation banner elements.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
