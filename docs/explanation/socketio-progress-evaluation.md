# Socket.IO Progress Streaming Evaluation

We reviewed the feasibility of mirroring the `EXAMPLES_ONLY/socketio.mdx`
pattern inside Atticus. Findings:

## Summary

- **Feasible** with moderate effort. FastAPI supports Socket.IO via
  `python-socketio`. We can reuse ingestion/eval progress events emitted by the
  pipeline and surface them as real-time updates.
- **Dependencies** — add `python-socketio[client]` and integrate with the
  existing metrics recorder. No incompatible libraries identified.
- **Security** — reuse existing auth (API key/session cookie) and namespace
  events under `/ws/progress`.

## Implementation plan

1. Add a background task (`ProgressBroadcaster`) that tails ingest/eval log
   files and emits structured events.
2. Extend `web` UI with a Socket.IO client to display stepwise status in the
   ingest/eval panels. Provide offline fallback by polling REST endpoints.
3. Instrument automated tests using `socketio.AsyncClient` to assert event
   sequencing.

## Outcome

Proceed with implementation in the next iteration. The evaluation did not find
blocking risks. Capture follow-up work in the backlog once scheduled.
