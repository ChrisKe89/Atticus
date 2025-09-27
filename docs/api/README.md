# API Documentation

## Generating the OpenAPI Schema

Run either command to emit the latest schema:

```bash
make openapi
```

or

```bash
python scripts/generate_api_docs.py --output docs/api/openapi.json
```

The CLI loads the FastAPI application directly, so the server does not need to be running.

---

## `/ask` Request & Response

```jsonc
POST /ask
{
  "question": "How does Atticus escalate low confidence answers?",
  "filters": {
    "source_type": "runbook"
  }
}
```

- `question` (string, required) - Natural-language query. Alias `query` is also accepted for backwards compatibility.
- `filters` (object, optional) - Restrict retrieval. Supported keys: `source_type`, `path_prefix`.

```jsonc
200 OK
{
  "answer": "Atticus blends retrieval and LLM confidence...",
  "citations": [
    {
      "chunk_id": "chunk-000045",
      "source_path": "content/20240901_escalation_playbook_v1.pdf",
      "page_number": 7,
      "heading": "Escalation Workflow",
      "score": 0.82
    }
  ],
  "confidence": 0.74,
  "should_escalate": false,
  "request_id": "9db0dd1c-..."
}
```

- `answer` - Grounded response including references to the supplied citations.
- `citations` - Ordered list of supporting chunks. Each item matches `retriever.models.Citation`.
- `confidence` - Combined retrieval plus LLM score (0-1).
- `should_escalate` - `true` when `confidence` falls below `CONFIDENCE_THRESHOLD`.
- `request_id` - Trace identifier surfaced in logs.

Errors follow the JSON error schema described in [AGENTS.md](../AGENTS.md#error-handling).

---

## Related References

- [ATTICUS_DETAILED_GUIDE.md](../ATTICUS_DETAILED_GUIDE.md)
- [README.md](../README.md)
- [OPERATIONS.md](../OPERATIONS.md)
