# Atticus Documentation

## Adding New Content
1. Place documents inside the `content/` tree following the taxonomy in `AGENTS.md` §3.1.
2. Name files using `YYYYMMDD_topic_version.ext` for traceability.
3. Run `python scripts/ingest.py` (or `make ingest`) to parse, chunk (defaults controlled by `config.yaml` / `.env`), embed, and update the index.
4. Review the ingestion report in `logs/app.jsonl` and commit the updated index snapshot plus `indices/manifest.json`.
5. Execute the evaluation harness with `python scripts/eval_run.py --json --output-dir eval/runs/manual` to confirm retrieval quality before tagging a release.
6. Regenerate API documentation with `python scripts/generate_api_docs.py` so the OpenAPI schema in `docs/api/openapi.json` stays in sync with the deployed code.
