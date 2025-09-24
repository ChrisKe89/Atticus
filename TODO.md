# TODO — Atticus (Authoritative Active List)

This file is the **single source of truth** for active tasks.
Items completed are moved to [ToDo-Complete.md](ToDo-Complete.md).
Tasks marked **[Codex]** are ideal for automation.

---
## Uncategorized

- review all documentation for any changes and updates.
- review all code for any changes and updates.
- action anything that is outstanding in the todo or readme.
- if there is anything you come across that is wrong, fix it.
- implement a way for me to access the local app from a remote PC.
- ensure the front end is working as well as everything else.
- Make sure everything is ticked off the todo list.
- do not stop until it is done.
- improve documentation to ensure that it is as detailed as possible.
- I want the documentation to describe every aspect of this application and how it works. from ingestion to understanding ambigious questions. create a more detailed guide if you need to.
    - i've put an EXAMPLE folder in the repo to show you what i mean.
    - To be very clear, this is an example only. C:\Users\Chris\OneDrive\Projects\Atticus\EXAMPLES_ONLY
    - I want the same thing for my app as in detail on how it works.
    - if there is fucntionality described in the C:\Users\Chris\OneDrive\Projects\Atticus\EXAMPLES_ONLY that could or should be included in my application, list it down as a future todo and i'll review it.

## Product & Audience

- [ ] Update external website and any public README hero copy to emphasise **Sales** as the primary audience and **tender acceleration** as a key benefit.

## Retrieval

- [ ] **[Codex]** Evaluate and optionally enable a re-ranker (e.g., BM25 hybrid tweak or lightweight re-rank). Add an env flag and update [AGENTS.md](AGENTS.md).

## API & UI

- [ ] **[Codex]** Confirm that the UI is integrated under the API at `/`. If split deployment is needed, reintroduce `make ui` documentation and update port mapping.
- [ ] Document `/ask` request/response models in the API docs. Ensure `make openapi` correctly regenerates the schema.

## Error Handling

- [ ] Implement the proposed **JSON error schema** across all routes and add tests to assert shape and required fields (400/401/422/5xx).
\n
## Tooling

- [ ] Adjust `Makefile` to add `-n auto` only if `pytest-xdist` is installed.
- [ ] Add `SMTP_DRY_RUN=1` branch to the mailer and a corresponding test.

## Documentation

- [ ] Replace README hero image placeholder with a production-ready graphic.
- [ ] Verify and maintain cross-links between [README.md](README.md), [AGENTS.md](AGENTS.md), and [OPERATIONS.md](OPERATIONS.md).

---

> Keep this list accurate and up to date. Once a task is finished, move it to [ToDo-Complete.md](ToDo-Complete.md) with the completion date and relevant commit ID.


