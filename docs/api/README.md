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
  "models": ["C7070"],
  "filters": {
    "source_type": "runbook"
  }
}
```

- `question` (string, required) - Natural-language query. Alias `query` is also accepted for backwards compatibility.
- `filters` (object, optional) - Restrict retrieval. Supported keys: `source_type`, `path_prefix`.
- `models` (array, optional) - Explicit model or family identifiers returned from a clarification prompt. When omitted Atticus infers models from the question text.

```jsonc
200 OK
{
  "answer": "Atticus blends retrieval and LLM confidence...",
  "answers": [
    {
      "model": "Apeos C7070",
      "family": "C7070",
      "family_label": "Apeos C7070 range",
      "answer": "Atticus blends retrieval and LLM confidence...",
      "confidence": 0.74,
      "should_escalate": false,
      "sources": [
        {
          "chunkId": "chunk-000045",
          "path": "content/20240901_escalation_playbook_v1.pdf",
          "page": 7,
          "heading": "Escalation Workflow",
          "score": 0.82
        }
      ]
    }
  ],
  "confidence": 0.74,
  "should_escalate": false,
  "request_id": "9db0dd1c-...",
  "sources": [
    {
      "chunkId": "chunk-000045",
      "path": "content/20240901_escalation_playbook_v1.pdf",
      "page": 7,
      "heading": "Escalation Workflow",
      "score": 0.82
    }
  ]
}
```

- `answer` - Aggregate response (string). For multi-model queries each entry in `answers` contains the scoped answer.
- `answers` - List of per-model responses surfaced when multiple models or families are requested.
- `sources` - Aggregated supporting citations for the response (per-entry sources live under each `answers[i].sources`).
- `confidence` - Combined retrieval plus LLM score (0-1).
- `should_escalate` - `true` when `confidence` falls below `CONFIDENCE_THRESHOLD`.
- `request_id` - Trace identifier surfaced in logs.

When Atticus cannot confidently infer a model, the endpoint returns a clarification payload instead of an answer:

```jsonc
200 OK
{
  "request_id": "bcf8854e-...",
  "clarification": {
    "message": "Which model are you referring to? If you like, I can provide a list of product families that I can assist with.",
    "options": [
      { "id": "C7070", "label": "Apeos C7070 range" },
      { "id": "C8180", "label": "Apeos C8180 series" }
    ]
  }
}
```

Errors follow the Error JSON schema described in [AGENTS.md](../../AGENTS.md).

---

## Related References

- [ATTICUS_DETAILED_GUIDE.md](../ATTICUS_DETAILED_GUIDE.md)
- [README.md](../README.md)
- [OPERATIONS.md](../OPERATIONS.md)
