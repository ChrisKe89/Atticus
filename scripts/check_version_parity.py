"""Ensure repository version metadata stays in sync across toolchains."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read_version_file() -> str:
    version_path = ROOT / "VERSION"
    try:
        version = version_path.read_text(encoding="utf-8").strip()
    except OSError as exc:
        raise SystemExit(f"Failed to read VERSION: {exc}") from exc
    if not version:
        raise SystemExit("VERSION file is empty.")
    return version


def read_package_version() -> str:
    package_path = ROOT / "package.json"
    try:
        package_data = json.loads(package_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Failed to parse package.json: {exc}") from exc
    version = package_data.get("version")
    if not isinstance(version, str) or not version:
        raise SystemExit("package.json is missing a version field")
    return version


def read_package_lock_version() -> str:
    lock_path = ROOT / "package-lock.json"
    try:
        lock_data = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Failed to parse package-lock.json: {exc}") from exc
    version = lock_data.get("version")
    if not isinstance(version, str) or not version:
        raise SystemExit("package-lock.json is missing a top-level version")
    return version


def main() -> int:
    repo_version = read_version_file()
    package_version = read_package_version()
    lock_version = read_package_lock_version()

    mismatches: list[str] = []
    if package_version != repo_version:
        mismatches.append(
            f"package.json version {package_version} does not match VERSION {repo_version}"
        )
    if lock_version != repo_version:
        mismatches.append(
            f"package-lock.json version {lock_version} does not match VERSION {repo_version}"
        )

    if mismatches:
        for mismatch in mismatches:
            print(f"❌ {mismatch}")
        return 1

    print(f"✅ Version parity check passed: {repo_version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
