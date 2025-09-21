# Requirements

## ced-362-source
- **What is needed:** The CED PDF `content/model/AC7070/Apeos_C7070-C6570-C5570-C4570-C3570-C3070-C2570-CSO-FN-CED-362.pdf`.
- **Why:** The `scripts/chunk_ced.py` workflow depends on this source file to generate the chunk JSONL, tables JSONL, and document index outputs specified in TODO §CED.
- **Acceptance:** After the PDF is supplied, running `python scripts/chunk_ced.py --input ... --output data/index/ced-362.chunks.jsonl --tables data/index/ced-362.tables.jsonl --doc-index data/index/ced-362.doc_index.json` should complete successfully and produce the three artifacts.

## future-state-roadmap
- **What is needed:** Product and infrastructure approvals (designs, credentials, and target environments) to implement Azure AD/SSO, pgvector/Postgres, and Prometheus/Grafana integrations.
- **Why:** These items are intentionally deferred future-state features and require architectural decisions plus service access that are not available in the current scope.
- **Acceptance:** Supply the approved architecture/credential bundle so the integrations can be implemented and validated end-to-end in CI.
