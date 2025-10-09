# RELEASE — Atticus

This document describes the official release process for Atticus.
Follow these steps to ensure every release is versioned, tested, and documented correctly.

---

## Versioning

Atticus uses **Semantic Versioning**: `MAJOR.MINOR.PATCH`.

- **MAJOR** — Incompatible API changes or breaking architecture changes.
- **MINOR** — Backwards-compatible feature additions or improvements.
- **PATCH** — Backwards-compatible bug fixes or documentation updates.

---

## Release Checklist

1. **Update CHANGELOG**
   - Edit [CHANGELOG.md](CHANGELOG.md) with the new version number, date, and highlights.
2. **Verify Environment**
   - Confirm `.env` is complete and correct using:

     ```bash
     python scripts/debug_env.py
     ```

3. **Run Full Quality Gates**
   - Ensure the following commands pass locally:

     ```bash
     make quality         # Ruff + mypy + pytest + Next lint/typecheck/build + audits
     npm run format:check # Prettier enforcement
     pre-commit run --all-files --show-diff-on-failure
     make eval            # Retrieval regression suite
     make e2e             # Optional but recommended before tagging
     ```

   - CI requires ≥90% coverage and enforces evaluation regression thresholds.

4. **Sync Versioning**
   - Update [`VERSION`](VERSION), `package.json`, and [CHANGELOG.md](CHANGELOG.md) with the new semantic version (e.g. `0.7.0`).
   - Confirm the values match by running `node -p "require('./package.json').version"` and comparing with `cat VERSION`.
   - Commit the changes with a descriptive message (e.g. `release(0.7.0): developer experience + docs sync`).
5. **Tag the Release**
   - Tag using semantic versioning, e.g. `v0.7.0`:

     ```bash
     git tag v0.7.0
     git push origin v0.7.0
     ```

   - Pushing the tag triggers the `release.yml` GitHub Action.

---

## Post‑Release

- Monitor `logs/app.jsonl` and `logs/errors.jsonl` for early issues.
- Announce the release internally and update any dependent services or documentation.
- Archive `reports/ci/*.json` and evaluation dashboards for audit trails.

---

## Upgrade / Rollback Playbook

### Upgrade

1. Pull the tagged release (`git fetch --tags && git checkout vX.Y.Z`).
2. Run database migrations and seed updates:

   ```bash
   make db.migrate
   make db.seed
   ```

3. Rebuild the Next.js app and restart services:

   ```bash
   npm install --production
   npm run build
   docker compose up -d --build
   ```

  > **Note:** Release 0.7.11 adds Prisma `Chat`/`Ticket` tables plus the tabbed admin console and RBAC APIs. Run `make db.migrate && make db.seed` before `npm run build` so low-confidence chat data and escalations materialise in the UI.
  > **Note:** Release 0.8.0 enforces the `app.pgvector_lists` GUC, introduces the `RagEvent` audit ledger, and adds glossary upsert/follow-up workflows. Run `make db.migrate`, `make db.verify`, and `npm run db:seed` before `npm run build`, and wire `make version-check` into CI to detect version drift early.

4. Verify health:

   ```bash
   make smoke
   make eval
   ```

5. Review audit artifacts (`reports/ci/`, `eval/runs/`) to confirm no regressions.

### Rollback

1. Checkout the previous tag and redeploy (`git checkout vX.Y.(Z-1)` followed by the upgrade steps above).
2. Restore index snapshots using `python scripts/rollback.py --manifest indices/manifest.json` if ingestion changes shipped.
3. Re-run `make eval` and `make quality` to ensure the rolled-back version is healthy.
4. Update status pages/runbooks with the rollback rationale and next steps.

---

## References

- [CHANGELOG.md](CHANGELOG.md) — full version history.
- [OPERATIONS.md](OPERATIONS.md) — runbooks and evaluation metrics.
- [SECURITY.md](SECURITY.md) — secrets management and IAM policy examples.
