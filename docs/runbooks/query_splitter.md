# Multi-Model Query Splitter Runbook

## Overview

The query splitter isolates FUJIFILM model families mentioned in a user request and executes a dedicated retrieval + generation pass for each target. The helper lives in [`retriever/query_splitter.py`](../../retriever/query_splitter.py) and is wired into the `/api/ask` flow so that multi-model prompts surface clearly separated answers.

- **Detector**: regex for `C\d{4,5}` style codes plus existing model resolver hints.
- **Execution**: `run_rag_for_each()` duplicates the request payload per model scope and calls `retriever.service.answer_question()` for each specialised prompt.
- **Output**: API returns `answers[]` with per-model responses; aggregated markdown keeps backwards-compatible `answer` + `sources` fields.

## Operations Checklist

1. **Unit Tests** — `pytest tests/test_query_splitter.py` validates code detection, prompt splitting, and orchestration behaviour.
2. **End-to-End** — `make quality` runs linting, typing, pytest, and Next.js checks to ensure the splitter integrates cleanly.
3. **Service Logs** — look for `ask_endpoint_complete` events with multiple answers to confirm fan-out execution.
4. **Eval Runs** — `make eval` recalculates retrieval quality; inspect `eval/runs/latest/` for comparative metrics.

## Troubleshooting

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| Multi-model question returns a single combined answer | Regex or model catalog did not resolve distinct scopes | Inspect `retriever/query_splitter.detect_model_codes()` output and confirm catalog entries for the families |
| Responses reference the wrong model | Filters missing family context | Ensure `ModelScope.family_id` is defined and that ingestion metadata uses matching product families |
| Tests fail with `ValueError: split_question requires at least one scope` | Resolver returned an empty set | Check upstream model resolver and fallback scope wiring in `api/routes/chat.py` |

## Rollback

1. Revert commits touching `retriever/query_splitter.py` and chat route wiring.
2. Remove `tests/test_query_splitter.py`.
3. Update `README.md` and `CHANGELOG.md` to remove multi-model query splitter references.
4. Bump `VERSION` and document the rollback reason in `TODO_COMPLETE.md`.

## Upgrade Notes

- No new environment variables are required.
- Ensure `text-embedding-3-large` remains the embedding model so the 3,072-dimension configuration stays aligned.
- When extending to additional product code formats, update `_MODEL_CODE_PATTERN` and extend unit coverage.
