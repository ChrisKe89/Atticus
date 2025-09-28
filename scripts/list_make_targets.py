"""List unique make targets defined in provided makefiles."""

from __future__ import annotations

import pathlib
import re
import sys


def collect_targets(paths: list[str]) -> list[str]:
    pattern = re.compile(r"^[A-Za-z0-9_.-]+:")
    targets: set[str] = set()
    for raw_path in paths:
        path = pathlib.Path(raw_path)
        if not path.exists():
            continue
        for line in path.read_text().splitlines():
            if pattern.match(line):
                name = line.split(":", 1)[0]
                if name != ".PHONY":
                    targets.add(name)
    return sorted(targets)


def main(argv: list[str]) -> int:
    targets = collect_targets(argv or ["Makefile"])
    for name in targets:
        print(name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
