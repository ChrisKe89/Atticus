# Collaborative Project Rooms Outline

Inspired by `EXAMPLES_ONLY/projects-overview.mdx`, this outline describes how a
project room experience could work inside Atticus.

## Use cases

- Pre-sales teams collaborate on tender responses with shared context.
- Marketing reviews campaign collateral alongside RAG answers.
- Service teams triage escalations that require coordinated research.

## Feature set

- **Room creation** — create rooms scoped to an opportunity or customer. Attach
  content filters (folders, tags) and assign roles.
- **Shared timeline** — chronological log of chat questions, answers, manual
  notes, and uploaded files.
- **Tasks** — lightweight checklist with assignees and due dates.
- **Insights** — pinned answers/snippets for quick reference.

## Technical approach

- New `project_rooms` table plus `room_members` and `room_events` to store
  activity. Use ULIDs for IDs and include `request_id` references when events are
  generated via the API.
- Extend the chat UI with a room selector; persist selection in local storage.
- Provide REST endpoints under `/api/project-rooms` with the shared error
  schema.

## Next steps

1. Finalise data model in an ADR.
2. Build API endpoints with list/create/update/delete operations.
3. Create React components under `web/src/features/projectRooms/` using TanStack
   Query.

This outline unblocks discovery work and removes the TODO item. Implementation
can proceed when prioritised.
