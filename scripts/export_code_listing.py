"""Generate a Markdown file containing repository source snippets.

This script walks the target directory (the current working directory by
default) and collects files with whitelisted extensions. Each file is
rendered inside a fenced code block, with the relative path printed as the
section heading.

It skips the following content:
- Directories named "indexes" or "indices" (case-insensitive)
- Any directory or file whose name contains the substring "cache" (case-insensitive)
- Files larger than the configured size limit (default: 2 MiB)

Usage
-----
python scripts/export_code_listing.py --output code_listing.md
python scripts/export_code_listing.py --root ./app --output app_sources.md
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Iterable

ALLOWED_EXTENSIONS = {
    ".py": "python",
    ".tsx": "tsx",
    ".ts": "ts",
    ".json": "json",
    ".css": "css",
}

DEFAULT_MAX_SIZE = 2 * 1024 * 1024  # 2 MiB


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export repository sources to Markdown.")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="Directory to scan for source files (defaults to current working directory).",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("code_listing.md"),
        help="Path to the Markdown file that will be generated.",
    )
    parser.add_argument(
        "--max-bytes",
        type=int,
        default=DEFAULT_MAX_SIZE,
        help="Maximum file size (in bytes) to include. Defaults to 2 MiB.",
    )
    return parser.parse_args()


def should_skip_directory(name: str) -> bool:
    lowered = name.lower()
    if lowered in {"indexes", "indices"}:
        return True
    return "cache" in lowered


def should_skip_file(path: Path, max_bytes: int, root: Path) -> bool:
    if path == root:
        return True

    lowered_name = path.name.lower()
    if "cache" in lowered_name:
        return True

    for part in path.relative_to(root).parts:
        if "cache" in part.lower():
            return True

    extension = path.suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        return True

    try:
        size = path.stat().st_size
    except OSError:
        return True

    if size > max_bytes:
        return True

    return False


def iter_source_files(root: Path, max_bytes: int) -> Iterable[Path]:
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [name for name in dirnames if not should_skip_directory(name)]

        for filename in filenames:
            file_path = Path(dirpath) / filename
            if should_skip_file(file_path, max_bytes=max_bytes, root=root):
                continue
            yield file_path


def read_file_content(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def build_markdown(root: Path, files: Iterable[Path]) -> str:
    lines: list[str] = []
    for file_path in sorted(files):
        relative_path = file_path.relative_to(root)
        language = ALLOWED_EXTENSIONS[file_path.suffix.lower()]
        lines.append(f"## {relative_path}")
        lines.append("")
        lines.append(f"```{language}")
        lines.append(read_file_content(file_path))
        lines.append("```")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    args = parse_args()
    root = args.root.resolve()

    if not root.exists() or not root.is_dir():
        raise SystemExit(f"Root directory does not exist or is not a directory: {root}")

    output_path = args.output
    if not output_path.is_absolute():
        output_path = root / output_path

    files = list(iter_source_files(root=root, max_bytes=args.max_bytes))
    markdown = build_markdown(root=root, files=files)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")

    print(f"Wrote {len(files)} files to {output_path}")


if __name__ == "__main__":
    main()
