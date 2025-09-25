# MCP Tool Integration Investigation

Goal: determine how Atticus can orchestrate multi-service workflows via the MCP
gateway, based on `EXAMPLES_ONLY/mcp-overview.mdx`.

## Findings

- MCP over HTTP fits our architecture; requests map cleanly to FastAPI routes.
- Required metadata (tool name, schema) can be stored alongside existing prompt
  definitions.
- NGINX already fronted for :8000, so exposing MCP on :8222 will not collide.

## Proposed implementation

1. Create `src/mcp/registry.py` to register tools (ingest, eval, escalation).
2. Expose `/mcp/tools/{name}` endpoints returning JSON-RPC compliant responses.
3. Add authentication via shared API key stored in `.env` (`MCP_API_KEY`).
4. Emit structured logs with `request_id` and tool invocation metadata.

## Next steps

- Build a proof-of-concept client in `scripts/mcp_cli.py` to trigger ingest
  runs.
- Document usage in `docs/how-to/mcp-tools.md` once endpoints ship.

This investigation confirms feasibility and outlines actionable steps for a
future sprint.
