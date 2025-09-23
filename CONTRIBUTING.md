# CONTRIBUTING.md

- Use Python 3.12.
- Lint/typecheck before committing:
  - Lint/format: `make lint` (check) or `make format` (apply fixes)
  - Type check: `make typecheck`
- Write or update tests for any behavior change.
- Keep docs in sync (README, FRONTEND, OPERATIONS).

## Editor setup (Ruff native server)

- VS Code workspace is configured to use Ruff’s native language server (no `ruff-lsp` needed): see `Atticus.code-workspace:22` and `Atticus.code-workspace:29`.
- Ensure the VS Code extension `charliermarsh.ruff` is installed (recommended via `.vscode/extensions.json`).
- On save, the workspace runs Ruff fixes and import organization automatically.
