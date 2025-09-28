# Glossary Specification

The glossary module enables reviewers to propose terminology updates and administrators
to approve or reject entries. The workflow is designed to mirror the RBAC policies in the
Next.js admin UI and Prisma models.

## Roles

| Role      | Permissions |
|-----------|-------------|
| `user`    | Read-only access to approved glossary entries. |
| `reviewer`| Submit new terms and propose edits. |
| `admin`   | Approve/reject proposals, manage history, export glossary. |

## Data Model

```prisma
model GlossaryEntry {
  id           String   @id @default(cuid())
  term         String
  definition   String
  synonyms     String[]
  status       String   @default("pending") // pending | approved | rejected
  submittedBy  String
  approvedBy   String?
  createdAt    DateTime @default(now())
  updatedAt    DateTime @updatedAt
}
```

All mutations emit structured audit logs (see `logs/app.jsonl`) including the acting user,
the request/trace ID, and the state transition.

## API Contracts

* `GET /api/glossary` – returns `DictionaryPayload` containing approved entries.
* `POST /api/glossary` – admin-only endpoint accepting `DictionaryPayload`; persists
  changes and records the actor/trace metadata.

## UI Flow

1. Reviewer submits a new term with synonyms and rationale.
2. Admin views pending proposals on `/admin/glossary`, reviews the diff, and approves.
3. Approved entries become available to all users and propagate via the API contract.

## CI Expectations

* `make test.api` exercises glossary endpoints under auth.
* `make quality` enforces type checks on the Prisma client and Next.js components.
* Seed data for glossary lives alongside the CED seed manifest (`make seed`).
