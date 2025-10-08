#!/usr/bin/env python3
"""Unified CLI dispatcher for Atticus utilities."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from atticus.logging_utils import get_logger

log = get_logger("atticus_cli")

COMMANDS = {
    "ingest": [sys.executable, str(ROOT / "scripts" / "ingest_cli.py")],
    "eval": [sys.executable, str(ROOT / "scripts" / "eval_run.py")],
    "qa": [sys.executable, str(ROOT / "scripts" / "eval_qa.py")],
    "chunk-ced": [sys.executable, str(ROOT / "scripts" / "chunk_ced.py")],
    "db-verify": [sys.executable, str(ROOT / "scripts" / "db_verify.py")],
    "openapi": [sys.executable, str(ROOT / "scripts" / "generate_api_docs.py")],
    "audit-unused": [sys.executable, str(ROOT / "scripts" / "audit_unused.py")],
    "env": [sys.executable, str(ROOT / "scripts" / "generate_env.py")],
    "e2e-smoke": [sys.executable, str(ROOT / "scripts" / "e2e_smoke.py")],
    "debug-env": [sys.executable, str(ROOT / "scripts" / "debug_env.py")],
}


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)

    parser = argparse.ArgumentParser(prog="atticus", description="Atticus unified CLI")
    parser.add_argument(
        "command", nargs="?", choices=sorted(COMMANDS.keys()), help="subcommand to run"
    )
    parser.add_argument(
        "args", nargs=argparse.REMAINDER, help="arguments passed to subcommand (prefix with --)"
    )
    if not argv:
        parser.print_help()
        return 0

    ns = parser.parse_args(argv)
    if ns.command is None:
        parser.print_help()
        return 0

    cmd = COMMANDS[ns.command] + ns.args
    log.info("dispatch", command=ns.command, args=ns.args)
    try:
        return subprocess.call(cmd)
    except KeyboardInterrupt:
        log.warning("interrupt")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
