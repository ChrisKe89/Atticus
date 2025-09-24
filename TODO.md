# TODO — Atticus (Authoritative Active List)

This file is the **single source of truth** for active tasks.
Items completed are moved to [ToDo-Complete.md](ToDo-Complete.md).
Tasks marked **[Codex]** are ideal for automation.

---

## Product & Audience

- [ ] Update external website and any public README hero copy to emphasise **Sales** as the primary audience and **tender acceleration** as a key benefit.

## Retrieval

- [ ] **[Codex]** Evaluate and optionally enable a re-ranker (e.g., BM25 hybrid tweak or lightweight re-rank). Add an env flag and update [AGENTS.md](AGENTS.md).

## API & UI

- [ ] **[Codex]** Confirm that the UI is integrated under the API at `/`. If split deployment is needed, reintroduce `make ui` documentation and update port mapping.
- [ ] Document `/ask` request/response models in the API docs. Ensure `make openapi` correctly regenerates the schema.

## Error Handling

- [ ] Implement the proposed **JSON error schema** across all routes and add tests to assert shape and required fields (400/401/422/5xx).

## Security

- [ ] Add SES IAM policy snippet to [SECURITY.md](SECURITY.md) that restricts `ses:FromAddress` and region; cross-link from [README.md](README.md).

## Tooling

- [ ] Adjust `Makefile` to add `-n auto` only if `pytest-xdist` is installed.
- [ ] Add `SMTP_DRY_RUN=1` branch to the mailer and a corresponding test.

## Documentation

- [ ] Replace README hero image placeholder with a production-ready graphic.
- [ ] Verify and maintain cross-links between [README.md](README.md), [AGENTS.md](AGENTS.md), and [OPERATIONS.md](OPERATIONS.md).

---

> Keep this list accurate and up to date. Once a task is finished, move it to [ToDo-Complete.md](ToDo-Complete.md) with the completion date and relevant commit ID.
