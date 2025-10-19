# Glossary Baseline

This document captures the canonical glossary that powers inline dictionary
lookups for the Atticus chat experience. It is the working contract for the
dictionary agent, the FastAPI `/admin/dictionary` bridge, and downstream
services that surface glossary hits.

## Data Sources

- Primary store: `indices/dictionary.json` (JSON list of glossary entries).
- Seed pipeline: `make db.seed` loads deterministic rows for smoke suites.
- Runtime configuration: `DICTIONARY_PATH` environment variable (defaults to
  `indices/dictionary.json`) as defined in `core.config.AppSettings`.

If the JSON file does not exist locally, run `make db.seed` or copy the file
from the latest production snapshot before running glossary tooling.

## Entry Schema

Each dictionary entry is a JSON object with the following fields:

| Field | Type | Required | Purpose |
| --- | --- | --- | --- |
| `term` | string | yes | Canonical glossary heading shown in the UI. |
| `definition` | string | yes | Markdown-friendly description returned to users. |
| `synonyms` | array[string] | no | Alternate terminology submitted by reviewers. |
| `aliases` | array[string] | no | Additional strings that should trigger a hit. |
| `units` | array[string] | no | Units of measure that clarify the definition. |
| `productFamilies` | array[string] | no | Canonical FUJIFILM product families. |
| `normalizedAliases` | array[string] | no | Precomputed lowercase tokens (optional; auto-generated if omitted). |
| `normalizedFamilies` | array[string] | no | Precomputed uppercase family labels (optional; auto-generated if omitted). |

All list fields accept either an array or a comma-separated string. The loader
normalises values during ingestion so the dictionary agent can work with
consistent tokens (`atticus/glossary.py`).

## Workflow

1. The dictionary agent exports the current JSON into a working branch.
2. Reviewers stage edits using `pnpm --filter atticus-admin-service dev` or
   by editing `indices/dictionary.json` directly.
3. Run `pytest tests/test_glossary_hits.py` to ensure token normalisation
   still behaves as expected.
4. Commit the changes and document them in `CHANGELOG.md` (see automation
   below).

All mutations should be traceable via `TODO_COMPLETE.md` and the changelog.
The admin FastAPI surface (`/admin/dictionary`) mirrors these entries for
legacy tooling until the Prisma-backed workflow is fully deployed.

## Sample Entry

```json
{
  "term": "Managed Print Services",
  "definition": "Co-managed print optimisation programme delivered by FUJIFILM.",
  "synonyms": ["MPS"],
  "aliases": ["print optimisation"],
  "units": ["devices"],
  "productFamilies": ["Apeos series"],
  "normalizedAliases": ["managedprintservices", "mps", "printoptimisation"],
  "normalizedFamilies": ["APEOS SERIES"]
}
```

## Validation Checklist

- `make quality` - runs unit tests, API suites, and Next.js checks that depend
  on glossary metadata.
- `pytest tests/test_admin_route.py` - exercises the admin dictionary endpoints.
- `pytest tests/test_glossary_hits.py` - verifies hit detection across answers,
  aliases, and product family tokens.
- Manual smoke: ask the chat surface for glossary-covered terms and confirm
  inline highlights render with definitions and citations.

## Automation Hooks

- Use `python scripts/log_todo_completion.py` to log glossary-related TODO
  completions with the current date.
- Run `python scripts/update_changelog_from_todos.py` (or `make changelog.sync`)
  after logging completions to rebuild the `CHANGELOG.md` backlog section.

These scripts keep documentation and automation aligned with backlog hygiene
requirements.
