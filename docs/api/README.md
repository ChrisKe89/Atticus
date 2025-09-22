# API Documentation

Generate the OpenAPI schema for Atticus with:

```bash
python scripts/generate_api_docs.py --output docs/api/openapi.json
```

Pass `--format yaml` to emit a YAML document, or change `--output` to send the
schema elsewhere. The command loads the FastAPI application directly, so the
server does not need to be running.
