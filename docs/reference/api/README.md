# API Documentation

## Generating the OpenAPI Schema

Run either command to emit the latest schema:

```bash
make openapi
```

or

```bash
python scripts/generate_api_docs.py --output docs/reference/api/openapi.json
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
  "bullets": [
    "Escalates when confidence < 0.70.",
    "Sends SES email with citations and AE ID."
  ],
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

- `answer` - Grounded summary (1–2 sentences) including references to the supplied citations.
- `bullets` - Optional list of up to three highlights for readability.
- `citations` - Ordered list of supporting chunks. Each item matches `retriever.models.Citation`.
- `confidence` - Combined retrieval plus LLM score (0-1).
- `should_escalate` - `true` when `confidence` falls below `CONFIDENCE_THRESHOLD`.
- `request_id` - Trace identifier surfaced in logs.
- `sources` - Convenience list combining path, page, and heading strings for UI display.

```jsonc
206 Partial
{
  "answer": "This may be incomplete. Low confidence answer...",
  "bullets": ["Contact the NTS team for a definitive response."],
  "citations": [],
  "confidence": 0.52,
  "should_escalate": true,
  "request_id": "9db0dd1c-...",
  "sources": ["content/20240901_escalation_playbook_v1.pdf (page 7) — Escalation Workflow"],
  "escalated": true,
  "ae_id": "AE142"
}
```

- `escalated`/`ae_id` - present on 206 responses and map to the logged escalation record and email subject (`Escalation from Atticus: {ae_id} · {request_id}`).
- 206 responses always trigger JSON/CSV log entries and the SES mailer; integrations should treat them as actionable escalations.

```jsonc
200 OK (Clarification)
{
  "answer": "Could you share more context (product, workflow, or scenario) so I can search the right guidance?",
  "bullets": null,
  "citations": [],
  "confidence": 0.0,
  "should_escalate": false,
  "request_id": "b9a7b7a4-...",
  "clarification_needed": true,
  "clarification": "Could you share more context (product, workflow, or scenario) so I can search the right guidance?"
}
```

- `clarification_needed`/`clarification` - returned when the system requires one targeted follow-up before attempting retrieval.

Errors follow the JSON error schema described in [AGENTS.md](../../../AGENTS.md#error-handling).

---

## Related References

- [System Overview](../../explanation/system-overview.md)
- [README.md](../../../README.md)
- [OPERATIONS.md](../../../OPERATIONS.md)
