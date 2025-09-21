# Atticus Documentation

## Adding New Content
1. Place documents inside the `content/` tree following the taxonomy in `AGENTS.md` §3.1.
2. Name files using `YYYYMMDD_topic_version.ext` for traceability.
3. Run `python scripts/run_ingestion.py` to parse, chunk (~512 tokens with 20% overlap), embed, and update the index.
4. Review the ingestion report in `logs/app.jsonl` and commit the updated index snapshot.
5. Execute the evaluation harness with `pytest evaluation/harness` to confirm retrieval quality before tagging a release.
