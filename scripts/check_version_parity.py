from __future__ import annotations

import json
import sys
from pathlib import Path


def main() -> int:
    pkg_path = Path("package.json")
    ver_path = Path("VERSION")
    if not pkg_path.exists() or not ver_path.exists():
        print("ERROR: Missing package.json or VERSION file", file=sys.stderr)
        return 2
    try:
        pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"ERROR: Failed to read package.json: {exc}", file=sys.stderr)
        return 2
    version_pkg = str(pkg.get("version", "")).strip()
    version_file = ver_path.read_text(encoding="utf-8").strip()
    if version_pkg != version_file:
        print(
            f"ERROR: Version mismatch (package.json={version_pkg!r} vs VERSION={version_file!r})",
            file=sys.stderr,
        )
        return 1
    print("Version parity OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
