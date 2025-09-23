# Operations

- Ingestion: `python scripts/ingest_cli.py` (or `make ingest`).
- Index manifest/snapshots live under `indices/` and `indices/snapshots/`.
- Rollback: `python scripts/rollback.py` with a chosen snapshot.
- Evaluation: `python scripts/eval_run.py --json --output-dir eval/runs/<name>`.
- Escalation email requires `.env` SMTP_* and CONTACT_EMAIL configured.

See `TROUBLESHOOTING.md` for Windows and parsing pitfalls.
