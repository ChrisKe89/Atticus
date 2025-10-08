# CONTRIBUTING — Atticus

Thank you for contributing to Atticus! This guide explains how to set up your environment, maintain code quality, and keep documentation consistent.

---

## Development Environment

- Use **Python 3.12** and **Node.js 20**.
- Install Python dependencies:
  ```bash
  pip install -U pip pip-tools
  pip-compile -U requirements.in
  pip-sync requirements.txt
  ```
- Install Node dependencies:
  ```bash
  npm install
  ```

---

## Code Quality Workflow

Before committing any change, run:

```bash
make quality         # Ruff + mypy + pytest + Next lint/typecheck/build + audits
npm run format:check # Prettier (with tailwind sorting)
pre-commit run --all-files --show-diff-on-failure
```

Guidelines:

- Maintain >=90% test coverage. Add or update tests for every behaviour change.
- Keep documentation in sync, especially [README.md](README.md), [OPERATIONS.md](OPERATIONS.md), [RELEASE.md](RELEASE.md), and [AGENTS.md](AGENTS.md).
- Use `npm run format` and `make format` to auto-fix style issues before re-running the checks above.

---

## Editor Setup (VS Code + Ruff Native Server)

Atticus ships with a VS Code workspace that enables **Ruff’s native language server** for fast linting and formatting.

- Make sure the VS Code extension `charliermarsh.ruff` is installed (recommended via `.vscode/extensions.json`).
- On save, Ruff automatically organizes imports and fixes style issues.

This setup eliminates the need for `ruff-lsp` and ensures consistent formatting across the team.

---

## Commit Guidelines

- Use **imperative mood** in commit messages (e.g. `fix: correct SMTP config parsing`).
- Include a clear **scope** where relevant (e.g. `ui: add contact route`).
- Reference related issue or task IDs when possible.

---

## Documentation and Cross‑Links

- Keep references between [README.md](README.md), [AGENTS.md](AGENTS.md), and [OPERATIONS.md](OPERATIONS.md) accurate.
- Update [CHANGELOG.md](CHANGELOG.md) if your changes affect users.
- Move completed tasks from [TODO.md](TODO.md) to [TODO_COMPLETE.md](TODO_COMPLETE.md) with date and commit reference.

---

## Submitting Pull Requests

1. Create a feature branch.
2. Run all quality checks and update docs.
3. Submit a pull request with a concise summary of the change.
4. Ensure CI passes linting, typing, and evaluation regression gates before merge.

By following this guide, you’ll help keep Atticus secure, maintainable, and easy for everyone to use.
