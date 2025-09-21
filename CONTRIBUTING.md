# Contributing to Atticus

Thank you for your interest in improving Atticus. This guide explains how to set up your environment, run checks, propose changes, and open pull requests.

## Prerequisites

- Python 3.12
- Git
- Optional (parsers):
  - Tesseract OCR (for OCR of scanned PDFs/images)
  - Java (for Tabula fallback table extraction)

## Quick Start (Local)

1) Clone and enter the repo
- `git clone <your-fork-or-repo-url>`
- `cd Atticus`

2) Create and activate a virtual environment
- Windows PowerShell: `py -3.12 -m venv .venv; .\.venv\Scripts\Activate.ps1`
- macOS/Linux: `python3.12 -m venv .venv; source .venv/bin/activate`

3) Install dependencies
- `pip install -r requirements.txt`

4) Build the local index (ingestion)
- `python scripts/ingest.py`

5) Run the API (choose one)
- `uvicorn api.main:app --host 0.0.0.0 --port 8000`
- Or Docker: `docker compose up --build`

6) Run tests and quality checks
- `pytest -q`
- `ruff check .`
- `mypy`
- Coverage target: `pytest --cov --cov-report=term-missing` (≥90% unless exempted)

## Pull Request Rules

- Branch name: `feature/<topic>`, `fix/<topic>`, or `chore/<topic>`
- Title format: `[atticus] Short description`
- Must include:
  - Passing CI checks (lint, type, test, build)
  - Updated tests and documentation
  - Updated CHANGELOG entry (Unreleased)
- Use Conventional Commits in your messages when possible.

## Coding Standards

- Follow `.editorconfig` for formatting, and `ruff` for lint rules.
- Type hints required; `mypy --strict` passes.
- Keep changes minimal and focused; avoid unrelated refactors.

## Docs Policy

- Update README and CHANGELOG in the same PR as code changes when behavior or usage changes.
- Security-impacting changes should also update SECURITY.md if relevant.

## To-Do Workflow

- Active tasks live in `TODO.md`.
- When completing an item, mark it done and move it (with date + commit) to `ToDo-Complete.md`.

## Reporting Issues

- Provide steps to reproduce, logs (if safe), and environment details (OS, Python version).

