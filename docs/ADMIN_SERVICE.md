# Admin Service Overview

The Atticus admin service is a lightweight Next.js application that separates escalation review tooling from the primary chat workspace. It consumes the same upstream APIs as the main UI, writes curator feedback into `content/` CSV archives, and exposes a focused experience for reviewers.

## Key characteristics

- **Framework:** Next.js 14.x (app router, TypeScript)
- **Port:** `3101` (`npm run dev --workspace admin`)
- **Data sources:** Atticus main workspace APIs (`/api/admin/uncertain/**`)
- **Outputs:** Appends approved answers to `content/<family>/<model>.csv` in Excel-friendly format

## Local development

```bash
# Install dependencies (root workspace)
npm install

# Start the admin UI (port 3101)
npm run dev --workspace admin
```

The Docker Compose stack now includes an `admin` service that runs the same command:

```bash
docker compose up admin
```

By default the service forwards requests to `http://localhost:3000`. Override `ATTICUS_MAIN_BASE_URL` if the primary Next.js app runs elsewhere (e.g. when served behind nginx).

## Workflow outline

1. **Embed new documents** — invoke POST `/api/ingest` with optional path filters or a full-refresh toggle. Responses include document counts, chunk totals, and manifest/index paths for downstream auditing.
2. **Review escalated chats** — retrieve the queue via `GET /api/admin/uncertain` (includes `pending_review`, `draft`, and `rejected` states), inspect the transcript, edit the curated answer, and approve/reject as needed. Approved records append to `content/<model_family>/<model>.csv` with the schema `timestamp,question,answer,model,reviewer`.
3. **Glossary library** — call `GET /api/admin/dictionary` to confirm synonyms, aliases, units, and canonical product families before updating `indices/dictionary.json`; the chat service consumes this metadata to render inline glossary highlights.
4. **Evaluation seeds** — manage `eval/gold_set.csv` via `GET/POST /api/admin/eval-seeds`. The admin UI writes directly to the CSV with canonical headers (`question,relevant_documents,expected_answer,notes`).

## Headers & identity

Authentication is handled upstream. The admin service forwards curated requests with the following headers so the main workspace can attribute actions:

| Header                   | Purpose                                      |
| ------------------------ | -------------------------------------------- |
| `x-atticus-user-id`      | Reviewer identifier (defaults to `admin-service`) |
| `x-atticus-user-name`    | Display name (defaults to `Admin Service`)   |
| `x-atticus-user-email`   | Contact email for audit trails               |
| `x-atticus-role`         | Fixed to `ADMIN`                             |
| `x-atticus-org-id`       | Defaults to `org-atticus`                    |

Configure the reviewer identity with environment variables:

```bash
export ATTICUS_REVIEWER_ID="reviewer-123"
export ATTICUS_REVIEWER_NAME="Priya Sharma"
export ATTICUS_REVIEWER_EMAIL="psharma@example.com"
```

## Error handling

- API or CSV write issues are logged to `reports/phase2-errors.txt`.
- Failures to contact the main workspace surface inline to the reviewer UI so reviewers can retry without losing their drafts.

## Next steps

- Integrate real-time status updates when multiple reviewers are active.
- Extend ingestion panel with run history, including metrics snapshots under `reports/`.
