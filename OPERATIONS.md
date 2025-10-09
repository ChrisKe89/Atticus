# OPERATIONS — Atticus

This document provides **day‑to‑day runbooks** and a detailed guide for interpreting evaluation metrics.
It complements [README.md](README.md) for setup and [AGENTS.md](AGENTS.md) for architecture.

---

## Ingest & Index

1. Add or update source files under `content/` using `YYYYMMDD_topic_version.ext` naming.
2. Run ingestion:

   ```bash
   make ingest
   ```

   This parses, chunks (CED policy with SHA-256 dedupe), embeds, and updates the vector index.

3. Check logs in `logs/app.jsonl` for document counts, chunk totals, and token ranges.
4. When ready for release, commit the updated `indices/` snapshot and `indices/manifest.json`.
5. Generate a deterministic seed manifest (for CI smoke tests) via `make seed` and archive `seeds/seed_manifest.json` as needed.

---

## Database Health (pgvector)

Run these checks after applying Prisma migrations or when diagnosing ingestion anomalies.

1. Ensure Docker Compose Postgres is running (`make db.up`).
2. Validate the schema, pgvector extension, and IVFFlat index configuration:

   ```bash
   make db.verify
   ```

   ```powershell
   make db.verify
   ```

   The target wraps `psql "$DATABASE_URL" -v expected_pgvector_dimension=${PGVECTOR_DIMENSION:-3072} -v expected_pgvector_lists=${PGVECTOR_LISTS:-100} -f scripts/verify_pgvector.sql`.
   Override the defaults by exporting `PGVECTOR_DIMENSION` / `PGVECTOR_LISTS` before invoking the command.

3. For ad-hoc checks, run the SQL script directly:

   ```bash
   psql "$DATABASE_URL" -v expected_pgvector_dimension=${PGVECTOR_DIMENSION:-3072} -v expected_pgvector_lists=${PGVECTOR_LISTS:-100} -f scripts/verify_pgvector.sql
   ```

   ```powershell
   if (-not $env:PGVECTOR_DIMENSION) { $env:PGVECTOR_DIMENSION = 3072 }
   if (-not $env:PGVECTOR_LISTS) { $env:PGVECTOR_LISTS = 100 }
   psql "$env:DATABASE_URL" -v expected_pgvector_dimension=$env:PGVECTOR_DIMENSION -v expected_pgvector_lists=$env:PGVECTOR_LISTS -f scripts/verify_pgvector.sql
   ```

   The script fails fast if the extension is missing, the embedding dimension drifts, or the IVFFlat index loses its cosine lists configuration.

   > Requires the `psql` client (`postgresql-client` on Debian/Ubuntu).

---

## Glossary Baseline & Rollback

Use these steps to keep glossary fixtures deterministic across environments.

1. Seed the database:

   ```bash
   make db.seed
   ```

   ```powershell
   make db.seed
   ```

   The target provisions service users (`glossary.author@seed.atticus`, `glossary.approver@seed.atticus`) and three glossary entries spanning `APPROVED`, `PENDING`, and `REJECTED` states.

2. Verify the baseline rows (requires Postgres access):

   ```bash
   pytest tests/test_seed_manifest.py::test_glossary_seed_entries_round_trip
   ```

   ```powershell
   pytest tests/test_seed_manifest.py::test_glossary_seed_entries_round_trip
   ```

3. To reset production data after exploratory edits:

   - Snapshot current entries: `psql "$DATABASE_URL" -c 'COPY "GlossaryEntry" TO STDOUT WITH CSV HEADER' > glossary_backup.csv`.
   - Re-import when ready: `psql "$DATABASE_URL" -c "\copy \"GlossaryEntry\" FROM 'glossary_backup.csv' WITH CSV HEADER"`.
   - Rerun `make db.seed` to restore deterministic reviewer accounts.

Document deviations (e.g., temporary reviewer overrides) in the incident or release notes and update `docs/glossary-spec.md` if the workflow changes.

---

## Evaluate Retrieval

1. Ensure gold Q/A sets exist under `eval/goldset/*.jsonl`.
2. Run evaluation:

   ```bash
   make eval
   ```

   Results are written to `eval/runs/<timestamp>/metrics.json` and mirrored under `reports/` for CI artifacts.

3. Compare against baseline metrics. CI will fail if regression exceeds `EVAL_REGRESSION_THRESHOLD`.

Use the [Evaluation Metrics Interpretation](#evaluation-metrics-interpretation) section below to understand the metrics.

---

## Quality Gates & CI parity

Run `make quality` before every pull request. The target chains:

- `ruff check` / `ruff format --check`
- `mypy` across `atticus`, `api`, `ingest`, `retriever`, `eval`
- `pytest` with coverage ≥90%
- `npm run test:unit` (Vitest RBAC/unit coverage) and `npm run test:e2e` (Playwright admin/RBAC flows)
- `npm run lint`, `npm run typecheck`, `npm run build`
- Audit scripts: `npm run audit:ts`, `npm run audit:icons` (lucide import hygiene), `npm run audit:routes`, `npm run audit:py`

CI mirrors this via the `frontend-quality`, `lint-test`, and `pgvector-check` workflows. Audit reports are uploaded as artifacts under `reports/ci/` for inspection.

Formatting helpers:

```bash
npm run format      # Prettier (with tailwind sorting)
make format         # Ruff auto-fix
```

```powershell
npm run format
make format
```

---

## API & UI Operations

- Start the FastAPI service (JSON APIs only):

  ```bash
  make api
  ```

  Available at `http://localhost:8000`; FastAPI docs remain disabled in production and staging.

- Launch the Next.js workspace separately for the UI:

  ```bash
  make web-dev
  ```

  The UI expects the API to be reachable at `RAG_SERVICE_URL` (defaults to `http://localhost:8000`).
- To run a full smoke test (ingest → eval → API/UI check):

  ```bash
  make e2e
  ```

---

## Escalation Email (SES)

- Requires valid SES **SMTP credentials** (not IAM keys).
- Ensure the `CONTACT_EMAIL` and all `SMTP_*` environment variables are correctly set in `.env`.
- Maintain `SMTP_ALLOW_LIST` so only vetted recipients/senders receive escalations; mismatches raise actionable errors.
- The SES identity for `SMTP_FROM` must be verified; sandbox mode also requires verified recipients.
- For security, lock down SES with an IAM policy restricting `ses:FromAddress` to approved senders and region (see [SECURITY.md](SECURITY.md)).
- Escalation emails append structured trace payloads (user/chat/message IDs, top documents) and include the `trace_id` for log correlation.

---

## Snapshot & Rollback

1. Snapshot the `indices/` directory during each release.
2. To revert to a previous snapshot:

   ```bash
   python scripts/rollback.py --manifest indices/manifest.json
   ```

3. After rollback, run a smoke evaluation:

   ```bash
   make eval
   ```

   and test a few known gold queries with `/ask`.

---

## Observability & Debugging

- **Logs**
  - Info: `logs/app.jsonl`
  - Errors: `logs/errors.jsonl`
- **Sessions view**
  - `GET /admin/sessions?format=html|json`
- **Metrics dashboard**
  - `GET /admin/metrics` exposes query/escalation counters, latency histograms, and rate-limit stats.
- **Rate limiting**
  - Defaults to `RATE_LIMIT_REQUESTS=5` per `RATE_LIMIT_WINDOW_SECONDS=60`; violations emit hashed identifiers in `logs/app.jsonl`.
- **Verbose tracing**
  - Set `LOG_VERBOSE=1` and `LOG_TRACE=1` in `.env` and restart the service.
- **Environment diagnostics**
  - `python scripts/debug_env.py` shows the source and fingerprint of every secret.

---

## Dependency risk exceptions

`npm audit` (2025-09-28) flags one critical and seven moderate/low vulnerabilities tied to the current Next.js (14.2.5), @auth/core, esbuild, vite, and vitest toolchain. Upstream patches are pending; monitor Next.js security advisories (GHSA-f82v-jwr5-mffw, GHSA-gp8f-8m3g-qvj9) and plan an upgrade when 14.2.7+ ships with fixes. Track the audit output locally via:

```bash
npm audit --json > reports/ci/npm-audit-latest.json
```

Document mitigation status in security reviews and ensure `frontend-quality` continues to surface `reports/ci/*.json` artifacts for traceability.

---

## Evaluation Metrics Interpretation

When you run `make eval`, metrics appear in `eval/runs/<timestamp>/metrics.json`.
They measure how well retrieval surfaces the right evidence for answer generation.

### Core Metrics

| Metric          | What it Measures                                                 | Ideal Range        | Notes                                   |
| --------------- | ---------------------------------------------------------------- | ------------------ | --------------------------------------- |
| **nDCG@K**      | Quality of ranking — are the best chunks at the top?             | 0.85–1.0 excellent | Higher is better; discounts lower ranks |
| **Recall@K**    | Percentage of questions with at least one correct chunk in top-K | >=0.9 excellent    | Indicates coverage                      |
| **MRR@K**       | How early the first correct chunk appears                        | >=0.7 excellent    | Rewards early hits                      |
| **Precision@K** | Fraction of retrieved chunks that are relevant                   | Context dependent  | Useful when keeping context small       |

### Secondary Metrics

- **HitRate@K**: simpler recall variant — was _any_ relevant item retrieved?
- **MAP** (Mean Average Precision): averages precision across ranks.
- **Coverage**: fraction of gold questions for which any relevant doc exists in the corpus.
- **Latency**: median and 95th percentile retrieval time.

### Typical Thresholds for CI

Fail the evaluation if:

- `nDCG@10` drops more than **3–5%** compared to baseline.
- `Recall@10` drops more than **5%**.
- `MRR@10` drops more than **5–10%**.

These can be tuned for production needs (e.g., stricter for tenders).

### Diagnosing Drops

- **Recall drops, nDCG stable** → content drift or chunk sizes need adjustment.
- **nDCG drops, Recall stable** → ranking issue; consider enabling a reranker.
- **Both drop** → ingestion or index regression.
- **Precision drops, Recall stable** → too many loosely relevant chunks; adjust `MAX_CONTEXT_CHUNKS` or hybrid thresholds.

Example metrics block:

```json
{
  "metrics": {
    "ndcg@10": 0.86,
    "recall@10": 0.92,
    "mrr@10": 0.74,
    "precision@5": 0.62,
    "latency_ms_p50": 62,
    "latency_ms_p95": 110
  },
  "dataset": "eval/goldset/sales_faq.jsonl",
  "index_fingerprint": "3d7c1b...f12",
  "model": {
    "embed": "text-embedding-3-large@2025-01-15",
    "gen": "gpt-4.1"
  }
}
```

Interpretation: strong ranking and recall, with fast median latency.

---

## References

- [README.md](README.md) — first-time setup and Make targets
- [AGENTS.md](AGENTS.md) — architecture and error policy
- [SECURITY.md](SECURITY.md) — secrets and IAM policy
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) — quick fixes
