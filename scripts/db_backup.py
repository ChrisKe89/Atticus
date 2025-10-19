"""Create a pg_dump backup for the configured DATABASE_URL."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Create a pg_dump backup for Atticus.")
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Path to write the backup. Defaults to backups/atticus-YYYYmmdd-HHMMSS.dump",
    )
    parser.add_argument(
        "--database-url",
        dest="database_url",
        default=None,
        help="Override DATABASE_URL",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    database_url = args.database_url or os.environ.get("DATABASE_URL")
    if not database_url:
        print("DATABASE_URL must be set to run db_backup", flush=True)
        return 1

    pg_dump = shutil.which("pg_dump")
    if not pg_dump:
        print("pg_dump not found on PATH", flush=True)
        return 1

    output_path: Path
    if args.output is None:
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        output_path = Path("backups") / f"atticus-{timestamp}.dump"
    else:
        output_path = args.output

    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        pg_dump,
        "--format=custom",
        "--no-owner",
        "--no-acl",
        "--file",
        str(output_path),
        database_url,
    ]

    subprocess.run(cmd, check=True)
    print(f"Backup written to {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
