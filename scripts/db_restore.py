"""Restore a pg_dump archive into the configured DATABASE_URL."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Restore an Atticus pg_dump archive.")
    parser.add_argument(
        "input", type=Path, help="Path to the pg_dump archive produced by db_backup"
    )
    parser.add_argument(
        "--database-url",
        dest="database_url",
        default=None,
        help="Override DATABASE_URL",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Skip confirmation prompt before restoring (dangerous in production).",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    database_url = args.database_url or os.environ.get("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL must be set to run db_restore", flush=True)
        return 1

    archive = args.input
    if not archive.exists():
        print(f"Backup {archive} not found", flush=True)
        return 1

    if not args.force:
        confirmation = input(
            f"About to restore {archive} into {database_url}. This will overwrite existing data. Continue? [y/N] "
        ).strip()
        if confirmation.lower() not in {"y", "yes"}:
            print("Restore aborted")
            return 1

    pg_restore = shutil.which("pg_restore")
    if not pg_restore:
        print("pg_restore not found on PATH", flush=True)
        return 1

    cmd = [
        pg_restore,
        "--clean",
        "--if-exists",
        "--no-owner",
        "--no-acl",
        "--dbname",
        database_url,
        str(archive),
    ]
    subprocess.run(cmd, check=True)
    print(f"Restore completed from {archive}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
