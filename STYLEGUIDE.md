# STYLEGUIDE — Atticus

Consistent style makes the codebase easier to read, review, and maintain.
Follow these standards for all code and documentation.

---

## Python Code

* **Formatting**: Use [Ruff](https://docs.astral.sh/ruff/) with Black‑compatible style.

  ```bash
  make fmt     # auto-format
  make lint    # check style
  ```

* **Typing**: All public functions must be type‑hinted. Run `make type` to validate.
* **Imports**: Organized automatically by Ruff on save.
* **Naming**: Use snake_case for functions and variables, PascalCase for classes.

---

## Markdown

* **Line length**: Wrap at about **100 characters** where practical.
* **Code blocks**: Use fenced blocks with a language tag for syntax highlighting. Example:

  ```python
  def example() -> None:
      print("Hello Atticus")
  ```

* **Tables**: Use GitHub‑flavored markdown tables for clear presentation of structured data.
* **Links**: Use relative paths for internal references, e.g. `[AGENTS.md](AGENTS.md)`.

---

## Commits

* Use **imperative mood** and include a scope.
  Examples:
  * `ui: add contact route`
  * `docs: update README for SES configuration`
* Reference related issues or task IDs when possible.

---

## Documentation

* Keep cross-links between [README.md](README.md), [AGENTS.md](AGENTS.md), and [OPERATIONS.md](OPERATIONS.md) accurate.
* Ensure examples and instructions match the latest code and Makefile targets.
* Update [CHANGELOG.md](CHANGELOG.md) when behaviour changes.

---

## Style Philosophy

* Strive for **clarity and minimalism** — no clever one-liners at the expense of readability.
* Ensure code and docs are understandable by both experienced developers and newcomers.
