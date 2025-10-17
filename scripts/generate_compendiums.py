"""
Generate repository compendiums:

- ALL_CODE.md: concatenates source/config files into one Markdown file, with an Index
  of included paths and a header before each file's contents.
- ALL_DOCS.md: concatenates all Markdown documents with an Index and per-file sections.

Reasonable exclusions are applied to avoid binary/data artifacts and lockfiles.
"""

from __future__ import annotations

import io
import os
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parent.parent


CODE_EXTS = {
    ".py": "python",
    ".ts": "ts",
    ".tsx": "tsx",
    ".js": "javascript",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".json": "json",
    ".sql": "sql",
    ".yml": "yaml",
    ".yaml": "yaml",
    ".toml": "toml",
    ".ini": "ini",
    ".ps1": "powershell",
    ".sh": "bash",
    ".css": "css",
    ".scss": "scss",
    ".html": "html",
    ".env": "bash",
}

ALWAYS_INCLUDE = {"Makefile"}

# Exclude heavy or non-source directories/files
EXCLUDE_DIRS = {
    "content",
    "content_unused",
    "indices",
    "logs",
    "node_modules",
    ".next",
    ".git",
    ".venv",
    ".mypy_cache",
    ".pytest_cache",
    "eval/runs",
    "reports/playwright-artifacts",
}

EXCLUDE_FILES = {
    "pnpm-lock.yaml",
    "package-lock.json",
}


def should_exclude(path: Path) -> bool:
    rel = path.relative_to(REPO_ROOT)
    # Exclude directories in any segment
    for part in rel.parts:
        if part in EXCLUDE_DIRS:
            return True
    # Exclude specific filenames
    if path.name in EXCLUDE_FILES:
        return True
    return False


def iter_code_files() -> Iterable[Path]:
    for p in REPO_ROOT.rglob("*"):
        if p.is_dir():
            continue
        if should_exclude(p):
            continue
        if p.suffix in CODE_EXTS or p.name in ALWAYS_INCLUDE:
            yield p


def iter_doc_files() -> Iterable[Path]:
    for p in REPO_ROOT.rglob("*.md"):
        if p.is_dir():
            continue
        if p.name in {"ALL_DOCS.md", "ALL_CODE.md"}:  # avoid self-inclusion/cycles
            continue
        if should_exclude(p):
            continue
        yield p


def guess_lang(path: Path) -> str:
    if path.name in ALWAYS_INCLUDE:
        return "makefile"
    return CODE_EXTS.get(path.suffix, "")


def read_text(path: Path) -> str:
    # Best-effort UTF-8 with replacement to avoid failures on odd files
    with path.open("r", encoding="utf-8", errors="replace") as f:
        return f.read()


def write_all_code(target: Path) -> None:
    files = sorted({p for p in iter_code_files()}, key=lambda p: p.as_posix().lower())
    buf = io.StringIO()
    buf.write("# All Code\n\n")
    buf.write("## Index\n")
    for p in files:
        rel = p.relative_to(REPO_ROOT).as_posix()
        buf.write(f"- `{rel}`\n")
    buf.write("\n")
    for p in files:
        rel = p.relative_to(REPO_ROOT).as_posix()
        buf.write(f"## {rel}\n\n")
        lang = guess_lang(p)
        fence = f"```{lang}" if lang else "```"
        buf.write(f"{fence}\n")
        content = read_text(p)
        buf.write(content)
        if not content.endswith("\n"):
            buf.write("\n")
        buf.write("```\n\n")
    target.write_text(buf.getvalue(), encoding="utf-8")


def write_all_docs(target: Path) -> None:
    files = sorted({p for p in iter_doc_files()}, key=lambda p: p.as_posix().lower())
    buf = io.StringIO()
    buf.write("# All Documentation\n\n")
    buf.write("## Index\n")
    for p in files:
        rel = p.relative_to(REPO_ROOT).as_posix()
        buf.write(f"- `{rel}`\n")
    buf.write("\n")
    for p in files:
        rel = p.relative_to(REPO_ROOT).as_posix()
        buf.write(f"## {rel}\n\n")
        content = read_text(p)
        buf.write(content)
        if not content.endswith("\n"):
            buf.write("\n")
        buf.write("\n")
    target.write_text(buf.getvalue(), encoding="utf-8")


def main() -> None:
    write_all_code(REPO_ROOT / "ALL_CODE.md")
    write_all_docs(REPO_ROOT / "ALL_DOCS.md")
    print("Wrote ALL_CODE.md and ALL_DOCS.md")


if __name__ == "__main__":
    os.chdir(REPO_ROOT)
    main()
