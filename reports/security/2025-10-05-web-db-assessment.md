# Web Stack & Database Security Assessment — 2025-10-05

## Overview
- **Scope:** Next.js web application, Auth.js integration, Prisma layer, and Postgres/pgvector schema.
- **Method:** Static review of repository configuration, Prisma schema/migrations, middleware, and dependency audit (`npm audit`).
- **Summary:** One critical and multiple moderate dependency vulnerabilities were detected in the web stack. Database row-level security (RLS) relies on configuration that can be bypassed if misused, and several operational safeguards (TLS enforcement, secret management) require tightening.

## Web Stack Findings

### Critical dependency vulnerabilities
- `next@14.2.5` is affected by multiple advisories including cache poisoning (GHSA-gp8f-8m3g-qvj9) and image optimisation DoS/injection (GHSA-g77x-44xx-532m, GHSA-xv57-4mr9-wg8v). Upgrading to `next@14.2.33` or later resolves these issues without a major version bump.【F:package.json†L1-L41】【cbc5b4†L43-L110】
- `next-auth@4.24.11` pulls in vulnerable `@auth/core` and `cookie` packages. The current fix path requires upgrading to `next-auth@5.x`; plan a migration to Auth.js v5 APIs before release.【F:package.json†L1-L41】【cbc5b4†L5-L42】【cbc5b4†L110-L160】

### Moderate dependency exposure (dev-time)
- Tooling packages (`vitest`, `vite`, `vite-node`, `esbuild`) carry moderate advisories that require major upgrades to address. These impact development servers and CI; schedule coordinated upgrades to Vitest ≥3.2.4 once breaking-change review is complete.【cbc5b4†L110-L206】

### Configuration hardening
- Auth configuration falls back to generating a random secret when `AUTH_SECRET` is missing, which breaks session validation across replicas. Mandate an explicit secret in all environments and document required rotations.【F:lib/auth.ts†L71-L144】
- The Ask API defaults to `http://localhost:8000` when `RAG_SERVICE_URL` is unset, which can downgrade requests to plaintext if deployed without overriding the variable. Require HTTPS endpoints (enforce via validation) before production launch.【F:app/api/ask/route.ts†L1-L132】
- Docker Compose publishes Postgres on `0.0.0.0:5432` with default credentials (`atticus/atticus`). Block external exposure (bind to localhost or remove port mapping) and enforce strong secrets for non-local deployments.【F:docker-compose.yml†L1-L44】

### Compatibility checks
- Next.js 14 requires Node.js ≥18.17; the project uses Node 20 toolchain, so runtime compatibility is satisfied. Continue running CI on Node 20 to match production constraints.【F:package.json†L1-L41】

## Database Findings

### RLS context safety
- `clearRlsContext` resets the connection role to `'SERVICE'`, the bypass role referenced by RLS policies. Although calls occur within a transaction-local scope, any future reuse of this helper outside transactions could silently disable enforcement. Replace the reset with `reset_config` or explicit empty defaults to avoid widening privileges, and add regression tests for policy coverage.【F:lib/prisma.ts†L1-L31】【F:prisma/migrations/20240702120000_auth_rbac/migration.sql†L1-L173】

### pgvector configuration
- The schema expects the `vector` extension and `vector(3072)` embeddings. Ensure Postgres 16 instances include pgvector ≥0.5.1 and that connection pools set `app.pgvector_lists` to tune IVFFlat probes; missing configuration falls back to 100 lists, which may be excessive for smaller datasets.【F:prisma/migrations/20240708123000_pgvector_schema/migration.sql†L1-L64】

### Secret & organisation defaults
- Seeding relies on `DEFAULT_ORG_ID`/`DEFAULT_ORG_NAME` env vars and promotes any `ADMIN_EMAIL` provided. Document rotation procedures and require secret management that prevents accidental admin creation in shared environments.【F:prisma/seed.ts†L1-L36】

## Recommendations
1. **Patch Next.js immediately** to ≥14.2.33 and schedule Auth.js v5 migration to resolve `next-auth`/`cookie` advisories.
2. **Lock production configs**: require `AUTH_SECRET`, `RAG_SERVICE_URL` (HTTPS), and hardened Postgres credentials via environment policy checks.
3. **Harden Prisma RLS helpers**: adjust `clearRlsContext` to avoid `'SERVICE'` fallback and add automated tests that verify RLS enforcement per role.
4. **Plan dev tooling upgrades**: evaluate Vitest/Vite 3.x migration path and update CI matrices to cover new versions.
5. **Document pgvector prerequisites** in deployment runbooks (extension version, `app.pgvector_lists` tuning) to avoid migration/runtime mismatches.
