"""Synchronise the changelog with the latest TODO completions.

The script reads `TODO_COMPLETE.md`, extracts the most recent completed
tasks, and refreshes the "Merged from TODO_COMPLETE (Unversioned)" section
in `CHANGELOG.md` so release notes stay aligned with the backlog.

Usage:
    python scripts/update_changelog_from_todos.py
    python scripts/update_changelog_from_todos.py --date 2025-11-15
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Iterable, Sequence

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_TODO_COMPLETE = REPO_ROOT / "TODO_COMPLETE.md"
DEFAULT_CHANGELOG = REPO_ROOT / "CHANGELOG.md"
SECTION_HEADING = "### Merged from TODO_COMPLETE (Unversioned)"
DATE_PATTERN = re.compile(r"^## (\d{4}-\d{2}-\d{2})$")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--todo",
        type=Path,
        default=DEFAULT_TODO_COMPLETE,
        help="Path to TODO_COMPLETE.md (default: %(default)s)",
    )
    parser.add_argument(
        "--changelog",
        type=Path,
        default=DEFAULT_CHANGELOG,
        help="Path to CHANGELOG.md (default: %(default)s)",
    )
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="Optional ISO date (YYYY-MM-DD) to pull from TODO_COMPLETE. "
        "Defaults to the most recent dated section.",
    )
    return parser.parse_args()


def extract_sections(lines: Sequence[str]) -> dict[str, list[str]]:
    """Return a mapping of ISO date -> completed TODO lines."""

    sections: dict[str, list[str]] = {}
    current_date: str | None = None

    for raw_line in lines:
        line = raw_line.rstrip()
        date_match = DATE_PATTERN.match(line)
        if date_match:
            current_date = date_match.group(1)
            sections.setdefault(current_date, [])
            continue
        if current_date and line.startswith("- [x]"):
            sections[current_date].append(line.strip())

    return sections


def sanitize_entry(line: str, fallback_date: str) -> str:
    """Convert a TODO_COMPLETE bullet to a concise changelog entry."""

    if not line.startswith("- [x]"):
        raise ValueError(f"Unexpected line format: {line}")

    content = line[len("- [x] ") :].strip()
    date = fallback_date
    if " - completed " in content:
        content_part, remainder = content.split(" - completed ", maxsplit=1)
        content = content_part.strip()
        date_token = remainder.strip().split()[0]
        if re.fullmatch(r"\d{4}-\d{2}-\d{2}", date_token):
            date = date_token
    return f"- {date}: {content}"


def build_changelog_block(lines: Sequence[str], target_date: str | None) -> list[str]:
    sections = extract_sections(lines)
    if not sections:
        raise RuntimeError("No dated sections found in TODO_COMPLETE.md")

    if target_date:
        if target_date not in sections:
            raise ValueError(f"No completed entries for {target_date!r}")
        selected_date = target_date
    else:
        selected_date = sorted(sections.keys(), reverse=True)[0]

    entries = sections[selected_date]
    if not entries:
        raise ValueError(f"No completed TODO entries recorded for {selected_date}")

    return [sanitize_entry(line, selected_date) for line in entries]


def replace_changelog_section(changelog_lines: list[str], new_block: Iterable[str]) -> list[str]:
    try:
        heading_index = changelog_lines.index(SECTION_HEADING)
    except ValueError as exc:
        raise RuntimeError(
            f"Unable to locate section heading {SECTION_HEADING!r} in CHANGELOG.md"
        ) from exc

    # Determine where the section ends (next heading at the same or higher level).
    end_index = len(changelog_lines)
    for idx in range(heading_index + 1, len(changelog_lines)):
        line = changelog_lines[idx]
        if line.startswith("### ") or line.startswith("## ["):
            end_index = idx
            break

    block_lines = ["", *list(new_block), ""]  # ensure spacing
    return changelog_lines[: heading_index + 1] + block_lines + changelog_lines[end_index:]


def main() -> int:
    args = parse_arguments()

    todo_lines = args.todo.read_text(encoding="utf-8").splitlines()
    block = build_changelog_block(todo_lines, args.date)

    changelog_lines = args.changelog.read_text(encoding="utf-8").splitlines()
    rewritten = replace_changelog_section(changelog_lines, block)
    args.changelog.write_text("\n".join(rewritten) + "\n", encoding="utf-8")

    print(f"Updated changelog with {len(block)} entries from TODO_COMPLETE ({block[0][:25]}...)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
