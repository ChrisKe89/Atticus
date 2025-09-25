# API Naming Conventions

These rules keep Atticus endpoints and payloads predictable across services.

## Routes

- Prefix all HTTP routes with `/api/` except the UI root (`/`). Example:
  - `GET /api/health`
  - `POST /api/ask`
- Nested resources follow REST conventions: `/api/projects/{project_id}/documents`.
- Health checks and admin utilities stay under `/api/health` and `/api/admin/*`.

## Schemas

- Request models use `Create<Resource>Request`, `Update<Resource>Request`, or
  `<Resource>Query` (for filter payloads).
- Response models end with `<Resource>Response` or `<Resource>Summary`.
- Error payloads conform to [`api.errors.ErrorResponse`](src/api/errors.py):
  - `error`: snake_case identifier
  - `detail`: human-readable message
  - `status`: HTTP status code
  - `request_id`: correlation ID echoed from the middleware
  - `fields`: optional validation issues

## Client hooks

- React Query keys follow `resourceKeys.list()` / `resourceKeys.detail(id)`.
- Hooks expose `use<Resource>()`, `useCreate<Resource>()`, `useUpdate<Resource>()`.

Keep this document updated whenever a new resource is added or the error schema
changes.
