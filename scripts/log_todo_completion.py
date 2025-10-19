"""Mark TODO items as complete and log entries in TODO_COMPLETE.md.

Each invocation searches `TODO.md` for matching tasks, flips the checkbox
to `[x]`, and appends a dated entry to `TODO_COMPLETE.md`. This keeps the
backlog and completion log in sync without manual editing.

Usage:
    python scripts/log_todo_completion.py --entry "Add CHANGELOG.md automation::Implemented changelog sync script"
    python scripts/log_todo_completion.py \\
        --entry "Task one::details" \\
        --entry "Task two::details"
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parent.parent
TODO_PATH = REPO_ROOT / "TODO.md"
TODO_COMPLETE_PATH = REPO_ROOT / "TODO_COMPLETE.md"
DATE_FMT = "%Y-%m-%d"
DATE_HEADING_PATTERN = re.compile(r"^## (\d{4}-\d{2}-\d{2})$")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--entry",
        action="append",
        required=True,
        help="Task entry in the format 'Task Title::Details'. "
        "Repeat for multiple tasks.",
    )
    parser.add_argument(
        "--date",
        type=str,
        default=dt.date.today().strftime(DATE_FMT),
        help="Completion date (default: today).",
    )
    parser.add_argument(
        "--todo",
        type=Path,
        default=TODO_PATH,
        help="Path to TODO.md (default: %(default)s)",
    )
    parser.add_argument(
        "--log",
        type=Path,
        default=TODO_COMPLETE_PATH,
        help="Path to TODO_COMPLETE.md (default: %(default)s)",
    )
    return parser.parse_args()


def mark_todo_completed(todo_lines: list[str], task_title: str) -> list[str]:
    """Flip the checkbox for the matching TODO entry."""

    updated = False
    for idx, line in enumerate(todo_lines):
        if "[ ]" in line and task_title in line:
            todo_lines[idx] = line.replace("[ ]", "[x]", 1)
            updated = True
    if not updated:
        raise ValueError(f"Task '{task_title}' not found or already completed in TODO.md")
    return todo_lines


def ensure_date_section(log_lines: list[str], target_date: str) -> list[str]:
    """Ensure TODO_COMPLETE has a section for the given date."""

    for idx, line in enumerate(log_lines):
        match = DATE_HEADING_PATTERN.match(line.strip())
        if match and match.group(1) == target_date:
            return log_lines  # section already exists

    # Insert new section after the first horizontal rule (`---`) or at the end if not present.
    insert_idx = None
    for idx, line in enumerate(log_lines):
        if line.strip() == "---":
            insert_idx = idx + 1
            break
    if insert_idx is None:
        insert_idx = len(log_lines)

    block = ["", f"## {target_date}", ""]
    return log_lines[:insert_idx] + block + log_lines[insert_idx:]


def append_log_entries(log_lines: list[str], entries: Iterable[str], date: str) -> list[str]:
    log_lines = ensure_date_section(log_lines, date)

    lines_with_index = list(enumerate(log_lines))
    section_start = next(
        idx for idx, line in lines_with_index if line.strip() == f"## {date}"
    )

    insertion_point = section_start + 1
    while insertion_point < len(log_lines) and log_lines[insertion_point].strip().startswith("- [x]"):
        insertion_point += 1

    insert_block = [f"- [x] TODO \"{title}\" - {details} - completed {date}" for title, details in entries]
    insert_block.append("")  # trailing blank line for readability

    return log_lines[:insertion_point] + insert_block + log_lines[insertion_point:]


def main() -> int:
    args = parse_args()
    try:
        dt.datetime.strptime(args.date, DATE_FMT)
    except ValueError as exc:
        raise ValueError(f"Invalid date {args.date!r}; expected YYYY-MM-DD") from exc

    parsed_entries = []
    for raw in args.entry:
        if "::" not in raw:
            raise ValueError(f"Invalid entry format {raw!r}; expected 'Task::Details'")
        task, details = raw.split("::", maxsplit=1)
        task = task.strip()
        details = details.strip()
        if not task or not details:
            raise ValueError("Task title and details must be non-empty")
        parsed_entries.append((task, details))

    todo_lines = args.todo.read_text(encoding="utf-8").splitlines()
    for task, _ in parsed_entries:
        todo_lines = mark_todo_completed(todo_lines, task)
    args.todo.write_text("\n".join(todo_lines) + "\n", encoding="utf-8")

    log_lines = args.log.read_text(encoding="utf-8").splitlines()
    log_lines = append_log_entries(log_lines, parsed_entries, args.date)
    args.log.write_text("\n".join(log_lines).rstrip() + "\n", encoding="utf-8")

    print(f"Logged {len(parsed_entries)} task(s) for {args.date}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
