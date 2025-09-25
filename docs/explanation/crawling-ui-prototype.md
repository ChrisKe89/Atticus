# Knowledge Base Crawling UI Prototype

This document sketches the UX and architecture for a lightweight crawling UI
similar to `EXAMPLES_ONLY/crawling-configuration.mdx`.

## Objectives

- Allow power users to configure crawl targets (URL, cadence, parsing rules)
  without editing YAML files.
- Run crawls asynchronously and surface status updates in the existing progress
  streaming channel.

## Proposed UX

- New sidebar entry **"Crawling"** exposing a table of configured targets.
- Modal form with fields: URL, schedule (cron), parser preset, authentication
  tokens (stored in secrets manager), tags.
- Status column showing last run, next run, last result (success/failure).

## Backend design

- Add `crawling_targets` table (SQLite/Postgres) with columns matching the form
  fields plus metadata (`created_by`, `updated_at`).
- Background scheduler (APScheduler) picks up due targets and enqueues ingestion
  jobs via existing pipeline.
- Store crawl run history in `logs/crawling.jsonl` and expose via `/api/admin/crawls`.

## Next steps

1. Create Pydantic models and REST endpoints for CRUD operations.
2. Build the UI prototype using TanStack Query for data fetching.
3. Integrate with the ingestion pipeline to accept remote URLs as sources.

This prototype unblocks the TODO item; implementation can follow during the next
sprint.
