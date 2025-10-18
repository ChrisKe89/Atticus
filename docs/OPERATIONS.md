# OPERATIONS — Atticus

This document provides day‑to‑day runbooks and a quick guide for interpreting evaluation metrics. It complements README.md for setup and SECURITY.md for policy.

---

## Ingest & Index

1. Add or update source files under `content/`.
2. Run ingestion:

    ```bash
    make ingest
    ```

    > This parses, chunks (CED policy with SHA‑256 de‑dupe), embeds, and updates the vector index.

3. Check logs in `logs/app.jsonl` for document counts, chunk totals, and token ranges.
4. When ready for release, commit the updated `indexes/` snapshot and `indexes/manifest.json`.
5. Generate deterministic seed data with `make seed`.

---

## Database Health (pgvector)

1. Ensure Docker Compose Postgres is running (`make db.up`).
2. Validate the schema, pgvector extension, and IVFFlat configuration:

    ```bash
    make db.verify
    ```

3. For ad‑hoc checks, run the SQL script directly with psql.

---

## Evaluate Retrieval

1. Ensure gold Q/A sets exist under `eval/goldset/*.jsonl`.
2. Run evaluation:

```bash
make eval
```

Results are written to `eval/runs/<timestamp>/` and mirrored under `reports/` for CI artifacts.

---

## Quality Gates & CI Parity

Run `make quality` before every pull request. The target chains:

- ruff check / format check
- mypy type checks
- pytest with ≥90% coverage
- Next.js lint, typecheck, and build
- Audit scripts as configured

---

## API & UI Operations

- Start the FastAPI service (JSON APIs only):

```bash
make api
```

- Launch the Next.js workspace:

```bash
make web-dev
```

- To run an end‑to‑end smoke (ingest → eval → API/UI check):

```bash
make e2e
```

---

## Admin Service

The standalone admin workspace handles escalated chat review and lives in the `admin/` directory.

```bash
npm run dev --workspace admin    # http://localhost:3101
```

- Set `ATTICUS_MAIN_BASE_URL` if the primary UI runs behind nginx or a custom domain.
- Docker Compose exposes the same workspace via the `admin` service (`docker compose up admin`).
- Approved answers append to `content/<family>/<model>.csv`; all actions log to `reports/content-actions.log`.

---

## Ingestion & Evaluation Panels

Use the admin console to orchestrate ingestion and evaluation upkeep without leaving the browser.

- **Embed new documents** &rarr; submit partial or full refresh jobs through the ingestion panel. Results surface document/chunk counts plus manifest, index, and snapshot paths.
- **Glossary library** &rarr; audit `indices/dictionary.json` entries before applying synonym updates.
- **Evaluation seeds** &rarr; edit `eval/gold_set.csv` in place; updates drive CI retrieval benchmarks.

---

## Escalation Email

See SECURITY.md for the canonical SES/email policy, credential guidance, and IAM restrictions.

Operational note:

```bash
make smtp-test
```

Uses sandbox/non‑delivery settings in local environments; production must follow SECURITY.md.

---

## Snapshot & Rollback

1. Snapshot `indexes/` during each release.
2. To revert to a previous snapshot:

    ```bash
    python scripts/rollback.py --manifest indexes/manifest.json
    ```

3. After rollback, run a smoke evaluation (`make eval`).

---

## Observability & Debugging

- Logs: `logs/app.jsonl` (info), `logs/errors.jsonl` (errors)
- Rate limiting: see `/admin/metrics`
- Environment diagnostics: `python scripts/debug_env.py`

---

## Evaluation Metrics Interpretation

Core metrics:

- nDCG@K — ranking quality
- Recall@K — coverage
- MRR@K — how early correct hits appear
- Precision@K — relevance of retrieved chunks

Typical CI thresholds: fail on 3–5% nDCG@10 drop, 5% Recall@10 drop, or 5–10% MRR@10 drop vs baseline.

---

## References

- README.md — first‑time setup and Make targets
- SECURITY.md — SES/email and admin token policy (canonical)
- AGENTS.md — architecture and error policy
- TROUBLESHOOTING.md — quick fixes

## Environment Variables

| Variable                  | Dev      | Prod     | Notes |
| ------------------------- | -------- | -------- | ----- |
| ADMIN_API_TOKEN           | required | required |       |
| ADMIN_EMAIL               | required | required |       |
| ADMIN_NAME                | required | required |       |
| ATTICUS_MAIN_BASE_URL     | optional | optional | Admin service upstream base URL |
| ATTICUS_REVIEWER_ID      | optional | optional | Admin service reviewer identifier |
| ATTICUS_REVIEWER_NAME    | optional | optional | Display name for curator logs |
| ATTICUS_REVIEWER_EMAIL   | optional | optional | Reviewer email for audit trails |
| ASK_SERVICE_URL           | required | required |       |
| CHUNK_MIN_TOKENS          | required | required |       |
| CHUNK_OVERLAP_TOKENS      | required | required |       |
| CHUNK_TARGET_TOKENS       | required | required |       |
| CONFIDENCE_THRESHOLD      | required | required |       |
| CONTACT_EMAIL             | required | required |       |
| CONTENT_ROOT              | required | required |       |
| DATABASE_URL              | required | required |       |
| DEFAULT_ORG_ID            | required | required |       |
| DEFAULT_ORG_NAME          | required | required |       |
| DICTIONARY_PATH           | required | required |       |
| EMAIL_FROM                | required | required |       |
| EMAIL_SANDBOX             | required | required |       |
| EMAIL_SERVER_HOST         | required | required |       |
| EMAIL_SERVER_PASSWORD     | required | required |       |
| EMAIL_SERVER_PORT         | required | required |       |
| EMAIL_SERVER_USER         | required | required |       |
| EMBED_MODEL               | required | required |       |
| EMBEDDING_MODEL_VERSION   | required | required |       |
| ENABLE_RERANKER           | required | required |       |
| ERROR_LOG_PATH            | required | required |       |
| EVAL_REGRESSION_THRESHOLD | required | required |       |
| GEN_MODEL                 | required | required |       |
| INDICES_DIR               | required | required |       |
| LOG_FORMAT                | required | required |       |
| LOG_LEVEL                 | required | required |       |
| LOG_PATH                  | required | required |       |
| LOG_TRACE                 | required | required |       |
| LOG_VERBOSE               | required | required |       |
| MAX_CONTEXT_CHUNKS        | required | required |       |
| OPENAI_API_KEY            | required | required |       |
| PGVECTOR_LISTS            | required | required |       |
| PGVECTOR_PROBES           | required | required |       |
| POSTGRES_DB               | required | required |       |
| POSTGRES_PASSWORD         | required | required |       |
| POSTGRES_PORT             | required | required |       |
| POSTGRES_USER             | required | required |       |
| RAG_SERVICE_URL           | required | required |       |
| RATE_LIMIT_REQUESTS       | required | required |       |
| RATE_LIMIT_WINDOW_SECONDS | required | required |       |
| SMTP_ALLOW_LIST           | required | required |       |
| SMTP_DRY_RUN              | required | required |       |
| SMTP_FROM                 | required | required |       |
| SMTP_HOST                 | required | required |       |
| SMTP_PASS                 | required | required |       |
| SMTP_PORT                 | required | required |       |
| SMTP_TO                   | required | required |       |
| SMTP_USER                 | required | required |       |
| TIMEZONE                  | required | required |       |
| TOP_K                     | required | required |       |
