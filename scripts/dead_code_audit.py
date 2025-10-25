from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Callable, Sequence

BASE_DIR = Path(__file__).resolve().parent.parent
REPORT_DIR = BASE_DIR / "reports" / "quality"
REPORT_DIR.mkdir(parents=True, exist_ok=True)

Command = Sequence[str]
Transform = Callable[[str], str]


def _write_output(path: Path, content: str) -> None:
    if not content.endswith("\n"):
        content = f"{content}\n"
    path.write_text(content, encoding="utf-8")


def run_command(
    command: Command,
    stdout_path: Path,
    stderr_path: Path,
    *,
    json_output: bool = False,
    transform: Transform | None = None,
) -> dict:
    resolved = list(command)
    if os.name == "nt" and resolved and resolved[0] == "pnpm":
        resolved[0] = "pnpm.cmd"

    process = subprocess.run(
        resolved,
        cwd=BASE_DIR,
        capture_output=True,
        text=True,
        check=False,
    )
    stdout = process.stdout
    if transform is not None:
        stdout = transform(stdout)
        _write_output(stdout_path, stdout)
    elif json_output:
        try:
            parsed = json.loads(stdout or "null")
        except json.JSONDecodeError:
            _write_output(stdout_path, stdout)
        else:
            _write_output(stdout_path, json.dumps(parsed, indent=2))
    else:
        _write_output(stdout_path, stdout)
    _write_output(stderr_path, process.stderr)
    return {
        "command": list(command),
        "returncode": process.returncode,
        "stdout": str(stdout_path.relative_to(BASE_DIR)),
        "stderr": str(stderr_path.relative_to(BASE_DIR)),
    }


def main() -> None:
    summary: list[dict] = []

    summary.append(
        run_command(
            ["pnpm", "exec", "knip", "--reporter", "json"],
            REPORT_DIR / "knip-report.json",
            REPORT_DIR / "knip-report.stderr.log",
            json_output=True,
        )
    )

    def _ts_prune_transform(output: str) -> str:
        pattern = re.compile(r"^(?P<file>[^:]+):(?P<line>\d+)\s+-\s+(?P<symbol>.+)$")
        items: list[dict[str, object]] = []
        for raw_line in output.splitlines():
            line = raw_line.strip()
            if not line:
                continue
            match = pattern.match(line)
            if not match:
                items.append({"raw": line})
                continue
            symbol = match.group("symbol")
            name, note = symbol, None
            if " (" in symbol:
                name, _, trailing = symbol.partition(" (")
                note = trailing.rstrip(")")
            entry: dict[str, object] = {
                "file": match.group("file"),
                "line": int(match.group("line")),
                "symbol": name.strip(),
            }
            if note:
                entry["note"] = note
            items.append(entry)
        return json.dumps(items, indent=2)

    summary.append(
        run_command(
            ["pnpm", "exec", "ts-prune", "--json"],
            REPORT_DIR / "ts-prune-report.json",
            REPORT_DIR / "ts-prune-report.stderr.log",
            transform=_ts_prune_transform,
        )
    )

    _write_output(REPORT_DIR / "summary.json", json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
