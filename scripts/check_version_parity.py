"""Ensure repo, packages, and lockfiles share the same version metadata."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

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


def read_package_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Failed to parse {path.name}: {exc}") from exc


def read_package_lock_version(lock_path: Path) -> str:
    try:
        lock_data = json.loads(lock_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SystemExit(f"Failed to parse {lock_path.name}: {exc}") from exc
    version = lock_data.get("version")
    if not isinstance(version, str) or not version:
        raise SystemExit(f"{lock_path.name} is missing a top-level version")
    return version


def read_pnpm_lock() -> dict:
    lock_path = ROOT / "pnpm-lock.yaml"
    try:
        raw = lock_path.read_text(encoding="utf-8")
    except OSError as exc:
        raise SystemExit(f"Failed to read pnpm-lock.yaml: {exc}") from exc
    try:
        data = yaml.safe_load(raw) or {}
    except yaml.YAMLError as exc:
        raise SystemExit(f"Failed to parse pnpm-lock.yaml: {exc}") from exc
    if not isinstance(data, dict):
        raise SystemExit("pnpm-lock.yaml must deserialize into a mapping")
    return data


def ensure_pnpm_importer(lock_data: dict, importer: str, package_data: dict) -> None:
    importers = lock_data.get("importers")
    if not isinstance(importers, dict):
        raise SystemExit("pnpm-lock.yaml is missing the `importers` mapping")

    importer_data = importers.get(importer)
    if not isinstance(importer_data, dict):
        raise SystemExit(f"pnpm-lock.yaml is missing importer `{importer}`")

    for section in ("dependencies", "devDependencies", "optionalDependencies"):
        declared = package_data.get(section) or {}
        if not declared:
            continue
        lock_section = importer_data.get(section)
        if not isinstance(lock_section, dict):
            raise SystemExit(f"pnpm-lock.yaml importer `{importer}` is missing `{section}` entries")
        for name, spec in declared.items():
            lock_entry = lock_section.get(name)
            if not isinstance(lock_entry, dict):
                raise SystemExit(
                    f"pnpm-lock.yaml importer `{importer}` is missing `{section}` entry for `{name}`"
                )
            lock_spec = lock_entry.get("specifier")
            if lock_spec != spec:
                raise SystemExit(
                    f"pnpm-lock.yaml importer `{importer}` has specifier `{lock_spec}` for `{name}` but package.json specifies `{spec}`"
                )


def main() -> int:
    repo_version = read_version_file()
    package_data = read_package_json(ROOT / "package.json")
    package_version = package_data.get("version")
    if not isinstance(package_version, str) or not package_version:
        raise SystemExit("package.json is missing a version field")

    admin_package = read_package_json(ROOT / "admin" / "package.json")
    admin_version = admin_package.get("version")
    if not isinstance(admin_version, str) or not admin_version:
        raise SystemExit("admin/package.json is missing a version field")

    mismatches: list[str] = []
    if package_version != repo_version:
        mismatches.append(
            f"package.json version {package_version} does not match VERSION {repo_version}"
        )
    if admin_version != repo_version:
        mismatches.append(
            f"admin/package.json version {admin_version} does not match VERSION {repo_version}"
        )

    pnpm_lock = ROOT / "pnpm-lock.yaml"
    package_lock = ROOT / "package-lock.json"

    if pnpm_lock.exists():
        lock_data = read_pnpm_lock()
        ensure_pnpm_importer(lock_data, ".", package_data)
        ensure_pnpm_importer(lock_data, "admin", admin_package)
    elif package_lock.exists():
        lock_version = read_package_lock_version(package_lock)
        if lock_version != repo_version:
            mismatches.append(
                f"{package_lock.name} version {lock_version} does not match VERSION {repo_version}"
            )
    else:
        raise SystemExit("Missing lockfile: pnpm-lock.yaml or package-lock.json must exist")

    if mismatches:
        for mismatch in mismatches:
            print(f"[WARN] {mismatch}")
        return 1

    print(f"[OK] Version parity check passed: {repo_version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
