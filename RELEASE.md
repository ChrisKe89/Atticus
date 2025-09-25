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
     make fmt
     make lint
     make type
     make test
     make eval
     make e2e
     ```

   * CI requires >=90% coverage and enforces evaluation regression thresholds.
4. **Cut the Release**
   * Use Commitizen automation (runs version bump + changelog + git push with tags):

     ```bash
     make release
     ```

   * The pushed tag triggers the `Release` GitHub Action which publishes the GitHub Release.

---

## Post‑Release

* Monitor `logs/app.jsonl` and `logs/errors.jsonl` for early issues.
* Announce the release internally and update any dependent services or documentation.

---

## References

* [CHANGELOG.md](CHANGELOG.md) — full version history.
* [OPERATIONS.md](OPERATIONS.md) — runbooks and evaluation metrics.
* [SECURITY.md](SECURITY.md) — secrets management and IAM policy examples.
