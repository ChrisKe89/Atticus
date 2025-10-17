# OPERATIONS — Atticus

This document provides day‑to‑day runbooks and a quick guide for interpreting evaluation metrics. It complements README.md for setup and SECURITY.md for policy.

---

## Ingest & Index

1. Add or update source files under `content/`.
2. Run ingestion:

```bash
make ingest
```

This parses, chunks (CED policy with SHA‑256 de‑dupe), embeds, and updates the vector index.

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

