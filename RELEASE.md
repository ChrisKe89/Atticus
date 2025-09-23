# Release Process

- Version with Semantic Versioning (MAJOR.MINOR.PATCH).
- Update `CHANGELOG.md` for each release with date and highlights.
- Tag `vX.Y.Z` to trigger the `Release` GitHub Action.
- CI gates: lint, type-check, tests, and evaluation regression check using `EVAL_REGRESSION_THRESHOLD`.
