# RELEASE — Atticus

This document describes the official release process for Atticus.
Follow these steps to ensure every release is versioned, tested, and documented correctly.

---

## Versioning

Atticus uses **Semantic Versioning**: `MAJOR.MINOR.PATCH`.

* **MAJOR** — Incompatible API changes or breaking architecture changes.
* **MINOR** — Backwards-compatible feature additions or improvements.
* **PATCH** — Backwards-compatible bug fixes or documentation updates.

---

## Release Checklist

1. **Update CHANGELOG**
   * Edit [CHANGELOG.md](CHANGELOG.md) with the new version number, date, and highlights.
2. **Verify Environment**
   * Confirm `.env` is complete and correct using:

     ```bash
     python scripts/debug_env.py
     ```

3. **Run Full Test Suite**
   * Ensure the following pass:

     ```bash
     make lint
     make typecheck
     make test
     make eval
     make e2e
     ```

   * CI requires >=90% coverage and enforces evaluation regression thresholds.
4. **Tag the Release**
   * Tag using semantic versioning, e.g. `v1.3.0`:

     ```bash
     git tag v1.3.0
     git push origin v1.3.0
     ```

   * Pushing the tag triggers the `Release` GitHub Action.

---

## Post‑Release

* Monitor `logs/app.jsonl` and `logs/errors.jsonl` for early issues.
* Announce the release internally and update any dependent services or documentation.

---

## References

* [CHANGELOG.md](CHANGELOG.md) — full version history.
* [OPERATIONS.md](OPERATIONS.md) — runbooks and evaluation metrics.
* [SECURITY.md](SECURITY.md) — secrets management and IAM policy examples.
