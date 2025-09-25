# Tutorial — Getting Started with Atticus

This hands-on guide walks through the minimum steps to ingest new collateral,
evaluate retrieval quality, and serve the Atticus API.

## 1. Generate configuration

```bash
make env
```

This command writes `.env` using the defaults captured in
[`AGENTS.md`](../../AGENTS.md). Populate SMTP and OpenAI keys before
continuing.

## 2. Install dependencies

```bash
pip install -U pip pip-tools
pip-sync requirements.txt
```

> ℹ️  `requirements.txt` is kept up to date via `pip-compile` and is safe to
> install directly for both development and CI.

## 3. Add content

Drop new or updated files into `content/`, following the
`YYYYMMDD_topic_version.ext` naming convention from the agent playbook.

## 4. Ingest

```bash
make ingest
```

The pipeline parses, chunks, embeds, and refreshes `indices/manifest.json`. The
summary is logged to `logs/app.jsonl`.

## 5. Evaluate retrieval

```bash
make eval
```

Metrics land in `eval/runs/<timestamp>/metrics.json`. Compare against
`eval/baseline.json`; CI fails if regression >3%.

## 6. Serve the API & UI

```bash
make api
```

The FastAPI app and chat UI are available at `http://localhost:8000`. Every
response includes a `request_id` for traceability.

## 7. Quality gate before release

```bash
make quality
```

This target orchestrates the format → lint → type → test → coverage flow to
mirror CI. When it passes, commit updated indices, metrics, and content.
