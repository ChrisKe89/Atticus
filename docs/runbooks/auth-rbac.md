# Auth & RBAC Runbook

This runbook documents the Auth.js + Prisma deployment that powers Atticus phase 3.

## Overview

- **Provider**: Auth.js (NextAuth) with email magic link.
- **Adapter**: Prisma + Postgres with row-level security (RLS) keyed by `org_id` and role.
- **Roles**: `USER`, `REVIEWER`, `ADMIN`.
  - Users and reviewers can read glossary entries scoped to their org.
  - Admins can invite teammates, promote glossary entries, and manage roles.
- **Session storage**: Database-backed sessions (`Session` table) with Prisma adapter.

## Environment variables

| Variable                                                                                  | Purpose                                                                         |
| ----------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------- |
| `DATABASE_URL`                                                                            | Postgres connection string used by Prisma and Auth.js.                          |
| `AUTH_SECRET`                                                                             | Secret used to sign NextAuth cookies/JWT (matches `lib/auth.ts`).               |
| `DEFAULT_ORG_ID` / `DEFAULT_ORG_NAME`                                                     | Seed organization for default tenancy.                                          |
| `ADMIN_EMAIL` / `ADMIN_NAME`                                                              | Bootstrap admin account created by `npm run db:seed`.                           |
| `EMAIL_FROM`                                                                              | From address for Auth.js email provider.                                        |
| `EMAIL_SERVER_HOST` / `EMAIL_SERVER_PORT` / `EMAIL_SERVER_USER` / `EMAIL_SERVER_PASSWORD` | SMTP server used for magic link delivery (UI mailer also supports `SMTP_*`).    |
| `AUTH_DEBUG_MAILBOX_DIR`                                                                  | Filesystem directory where test magic links are persisted (used by Playwright). Defaults to `./logs/mailbox`. |

Use `python scripts/generate_env.py --force` to regenerate `.env` with sensible defaults. Override secrets in production.

## Provisioning steps

1. **Start Postgres**
   ```bash
   make db.up
   ```
2. **Apply migrations**
   ```bash
   make db.migrate
   ```
3. **Generate Prisma client**
   ```bash
   npm run prisma:generate
   ```
4. **Seed default org + admin**
   ```bash
   make db.seed
   ```
   The seed script creates (or updates) the organization referenced by `DEFAULT_ORG_ID` and promotes `ADMIN_EMAIL` to `ADMIN`.
5. **Run the app**
   ```bash
   npm run dev
   ```
   Visit `http://localhost:3000/signin`, request a magic link for the admin email, and open the link to access `/admin`.

## Testing

- **Unit**: `npm run test:unit` (Vitest) covers RBAC helpers.
- **Playwright**: `npm run test:e2e` validates the magic link flow and admin gating. Ensure the dev server is running and `AUTH_DEBUG_MAILBOX_DIR` (default `./logs/mailbox`) is writable before running.
- **Smoke**: `make web-test` + `make web-e2e` are wired into CI.

## RLS behaviour

- Policies enforce `org_id` scoping for users, sessions, accounts, and glossary entries.
- Admin-only actions (`INSERT`, `UPDATE`, `DELETE` on `GlossaryEntry`) require the connection role to be `ADMIN`. Service-level operations (NextAuth adapter) run under the `SERVICE` context, set via database defaults, to bootstrap new sessions.
- Always wrap Prisma calls that rely on user context with `withRlsContext(session, fn)` to set `app.current_user_*` settings.

## Operations

- **Magic link debugging**: Magic links are written to `<email>.txt` in `AUTH_DEBUG_MAILBOX_DIR` (default `./logs/mailbox`). Clear the file to invalidate previous links.
- **Role changes**: Use Prisma Studio or a SQL client to update `User.role`. RLS allows admins to self-manage via future UI.
- **Glossary management**: Admins manage terms in `/admin`. Reviewers will gain propose-only permissions in later phases.

## Rollback

1. Stop the Next.js app (`Ctrl+C`).
2. Revert migrations by restoring the previous database snapshot or running `psql` to drop the new tables/enums if safe.
3. Reset the workspace by checking out the prior git tag and reinstalling dependencies (`npm install`).
4. Restore `.env` from backups and restart services.

For emergency disablement, set `NEXTAUTH_SECRET` to an empty value and restart; Auth.js rejects new sessions, effectively putting the UI into maintenance mode while RBAC policies remain intact.
