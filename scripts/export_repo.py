#!/usr/bin/env python3
"""
Export all relevant, human-readable files into ONE markdown file for code review,
plus a MANIFEST with sizes and skip reasons.

Includes (by extension / name):
  .py .ts .tsx .js .jsx .json .yaml .yml .toml .ini .cfg .config .md .mdx .sql .graphql .gql .sh .ps1
  Dockerfile .env.example .envrc .editorconfig .prettierrc .eslintrc .eslintignore .gitignore .gitattributes

Skips (dir substrings, case-insensitive, at any depth):
  node_modules .git __pycache__ .venv .mypy_cache .pytest_cache .ruff_cache .next .turbo .cache dist build
  coverage .parcel-cache indexes indices vector cache

Also skips obvious binary/asset extensions and any file containing NUL bytes.
Hard-excludes the absolute path: C:\Dev\Atticus\indices (and below).

Outputs:
  - ALL_FILES.md  (sections with ``` fences, language autodetected)
  - MANIFEST.txt  (every file with size + included/skipped reason + totals)

Usage (from repo root):
  python scripts/export_repo.py --root . --output ALL_FILES.md --manifest MANIFEST.txt --max-file-mb 5
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Iterable, Iterator, Sequence

# ---------- Config ----------
BLOAT_DIR_KEYWORDS = tuple(
    k.casefold()
    for k in (
        "node_modules",
        ".git",
        "__pycache__",
        ".venv",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".next",
        ".turbo",
        ".cache",
        "dist",
        "build",
        "coverage",
        ".parcel-cache",
        "indexes",
        "indices",
        "vector",
        "cache",
    )
)
# Absolute hard-excludes (and all their subpaths)
HARD_EXCLUDE_DIRS = {Path(r"C:\Dev\Atticus\indices")}

# Human-readable include set (lowercased suffixes or exact basenames)
INCLUDE_EXTENSIONS = {
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".ini",
    ".cfg",
    ".config",
    ".md",
    ".mdx",
    ".sql",
    ".graphql",
    ".gql",
    ".sh",
    ".ps1",
}
INCLUDE_BASENAMES = {
    "dockerfile",
    ".env",
    ".env.example",
    ".envrc",
    ".editorconfig",
    ".prettierrc",
    ".eslintrc",
    ".eslintignore",
    ".gitignore",
    ".gitattributes",
}

# Obvious binary-ish or huge assets to skip by extension
BINARY_LIKE_EXTS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".bmp",
    ".tiff",
    ".ico",
    ".svg",
    ".woff",
    ".woff2",
    ".ttf",
    ".otf",
    ".eot",
    ".mp4",
    ".mp3",
    ".wav",
    ".flac",
    ".mkv",
    ".mov",
    ".zip",
    ".tar",
    ".gz",
    ".bz2",
    ".xz",
    ".7z",
    ".rar",
    ".pdf",
    ".doc",
    ".docx",
    ".ppt",
    ".pptx",
    ".xls",
    ".xlsx",
    ".wasm",
    ".bin",
    ".dll",
    ".exe",
    ".so",
    ".dylib",
    ".obj",
    ".class",
    ".psd",
    ".ai",
    ".sketch",
    ".fig",
}

LANGUAGE_BY_EXTENSION = {
    ".py": "python",
    ".ts": "typescript",
    ".tsx": "tsx",
    ".js": "javascript",
    ".jsx": "jsx",
    ".sh": "bash",
    ".ps1": "powershell",
    ".rb": "ruby",
    ".php": "php",
    ".go": "go",
    ".rs": "rust",
    ".java": "java",
    ".kt": "kotlin",
    ".swift": "swift",
    ".cs": "csharp",
    ".c": "c",
    ".h": "c",
    ".cpp": "cpp",
    ".hpp": "cpp",
    ".mjs": "javascript",
    ".cjs": "javascript",
    ".json": "json",
    ".yaml": "yaml",
    ".yml": "yaml",
    ".toml": "toml",
    ".ini": "ini",
    ".cfg": "ini",
    ".sql": "sql",
    ".md": "md",
    ".mdx": "mdx",
    ".gql": "graphql",
    ".graphql": "graphql",
}
# ---------- End Config ----------


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=Path.cwd(), help="Root to scan (repo root).")
    p.add_argument(
        "--output", type=Path, default=Path("ALL_FILES.md"), help="Output markdown file."
    )
    p.add_argument(
        "--manifest", type=Path, default=Path("MANIFEST.txt"), help="Manifest text file."
    )
    p.add_argument(
        "--include-hidden", action="store_true", help="Include hidden files/dirs (dotfiles)."
    )
    p.add_argument(
        "--max-file-mb", type=float, default=5.0, help="Max single file size to include (MB)."
    )
    return p.parse_args(argv)


def _resolve_set(paths: set[Path]) -> set[Path]:
    out = set()
    for p in paths:
        try:
            out.add(p.resolve())
        except OSError:
            out.add(p)
    return out


def _is_under_any(path: Path, roots: set[Path]) -> bool:
    try:
        resolved = path.resolve()
    except OSError:
        return False
    for r in roots:
        try:
            rr = r.resolve()
        except OSError:
            continue
        if resolved == rr or resolved.is_relative_to(rr):
            return True
    return False


def should_skip_dir_parts(parts: Iterable[str], include_hidden: bool) -> bool:
    for part in parts:
        if not include_hidden and part.startswith("."):
            return True
        lowered = part.casefold()
        if any(k in lowered for k in BLOAT_DIR_KEYWORDS):
            return True
    return False


def is_binary_quick(path: Path) -> bool:
    # quick sniff: NUL byte → likely binary
    try:
        with path.open("rb") as f:
            chunk = f.read(4096)
        return b"\x00" in chunk
    except OSError:
        return True  # unreadable → treat as binary to be safe


def is_included_file(path: Path) -> bool:
    name = path.name
    if name.casefold() in (n.casefold() for n in INCLUDE_BASENAMES):
        return True
    ext = path.suffix.lower()
    return ext in INCLUDE_EXTENSIONS


def iter_candidates(root: Path, include_hidden: bool) -> Iterator[Path]:
    hard_ex = _resolve_set(HARD_EXCLUDE_DIRS)
    for current_dir, dirnames, filenames in os.walk(root):
        dir_path = Path(current_dir)

        # hard excludes short-circuit
        if _is_under_any(dir_path, hard_ex):
            dirnames[:] = []
            continue

        rel_parts = dir_path.relative_to(root).parts if dir_path != root else ()

        # skip this dir?
        if should_skip_dir_parts(rel_parts, include_hidden):
            dirnames[:] = []
            continue

        # prune children
        pruned = []
        for d in dirnames:
            cand = dir_path / d
            if _is_under_any(cand, hard_ex):
                continue
            if should_skip_dir_parts(rel_parts + (d,), include_hidden):
                continue
            pruned.append(d)
        dirnames[:] = pruned

        for fn in filenames:
            fp = dir_path / fn
            # hidden path check
            if not include_hidden and any(p.startswith(".") for p in fp.relative_to(root).parts):
                continue
            yield fp


def detect_language(path: Path) -> str:
    # special basenames
    if path.name.lower() == "dockerfile":
        return "dockerfile"
    return LANGUAGE_BY_EXTENSION.get(path.suffix.lower(), "")


def format_bytes(n: int) -> str:
    return f"{n:,} bytes"


def mb(n: int) -> float:
    return n / (1024 * 1024)


def build_exports(
    root: Path, files: Iterable[Path], output_md: Path, manifest_txt: Path, max_file_mb: float
) -> None:
    max_bytes = int(max_file_mb * 1024 * 1024)
    lines_md: list[str] = ["# Consolidated Repository Files", ""]
    lines_manifest: list[str] = ["# Export Manifest", f"Root: {root}", ""]

    included_count = 0
    skipped_count = 0
    total_bytes_included = 0
    total_bytes_seen = 0

    for fp in sorted(files):
        rel = fp.relative_to(root)
        ext = fp.suffix.lower()
        name_lower = fp.name.lower()

        # extension-based quick skips (binary-ish)
        if ext in BINARY_LIKE_EXTS:
            try:
                sz = fp.stat().st_size
                total_bytes_seen += sz
            except OSError:
                pass
            lines_manifest.append(f"[SKIP: binary-ext] {rel.as_posix()}")
            skipped_count += 1
            continue

        # include filter
        if not is_included_file(fp) and name_lower not in (n.casefold() for n in INCLUDE_BASENAMES):
            # not in whitelist → skip (keeps output lean)
            try:
                sz = fp.stat().st_size
                total_bytes_seen += sz
            except OSError:
                pass
            lines_manifest.append(f"[SKIP: not-in-include-list] {rel.as_posix()}")
            skipped_count += 1
            continue

        # size checks
        try:
            size = fp.stat().st_size
        except OSError as exc:
            lines_manifest.append(f"[SKIP: unreadable: {exc}] {rel.as_posix()}")
            skipped_count += 1
            continue

        total_bytes_seen += size

        if size > max_bytes:
            lines_manifest.append(
                f"[SKIP: too-large ({mb(size):.2f} MB > {max_file_mb:.2f} MB)] {rel.as_posix()} ({format_bytes(size)})"
            )
            skipped_count += 1
            continue

        # binary sniff
        if is_binary_quick(fp):
            lines_manifest.append(f"[SKIP: binary-sniff] {rel.as_posix()} ({format_bytes(size)})")
            skipped_count += 1
            continue

        # read & append to MD
        try:
            text = fp.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            lines_manifest.append(
                f"[SKIP: read-error: {exc}] {rel.as_posix()} ({format_bytes(size)})"
            )
            skipped_count += 1
            continue

        lang = detect_language(fp)
        lines_md.append(f"## `{rel.as_posix()}`")
        lines_md.append("")
        code_fence = f"```{lang}".rstrip()
        lines_md.append(code_fence)
        lines_md.append(text)
        lines_md.append("```")
        lines_md.append("")

        lines_manifest.append(
            f"[INCLUDED] {rel.as_posix()} ({format_bytes(size)} / {mb(size):.2f} MB)"
        )
        included_count += 1
        total_bytes_included += size

    # manifest footer
    lines_manifest.append("")
    lines_manifest.append(f"Files included: {included_count}")
    lines_manifest.append(f"Files skipped : {skipped_count}")
    lines_manifest.append(
        f"Total seen    : {format_bytes(total_bytes_seen)} ({mb(total_bytes_seen):.2f} MB)"
    )
    lines_manifest.append(
        f"Included size : {format_bytes(total_bytes_included)} ({mb(total_bytes_included):.2f} MB)"
    )
    lines_manifest.append(f"Per-file cap  : {max_file_mb:.2f} MB")

    output_md.write_text("\n".join(lines_md).rstrip() + "\n", encoding="utf-8")
    manifest_txt.write_text("\n".join(lines_manifest).rstrip() + "\n", encoding="utf-8")


def main(argv: Sequence[str] | None = None) -> None:
    args = parse_args(argv)
    root = args.root.resolve()
    if not root.exists():
        raise SystemExit(f"Root path does not exist: {root}")

    # Resolve hard excludes
    hard_ex = _resolve_set(HARD_EXCLUDE_DIRS)

    # Walk and filter
    candidates = []
    for fp in iter_candidates(root, args.include_hidden):
        # hard exclude check on parent chain
        if _is_under_any(fp.parent, hard_ex):
            continue
        # bloat dir check on full path parts (defense-in-depth)
        if any(k in part.casefold() for part in fp.parts for k in BLOAT_DIR_KEYWORDS):
            continue
        candidates.append(fp)

    # Compute output paths (relative → under root)
    out_md = (args.output if args.output.is_absolute() else root / args.output).resolve()
    out_manifest = (
        args.manifest if args.manifest.is_absolute() else root / args.manifest
    ).resolve()

    build_exports(root, candidates, out_md, out_manifest, args.max_file_mb)
    print(f"Wrote {out_md} and {out_manifest} (from {len(candidates)} candidate files).")


if __name__ == "__main__":
    main()
