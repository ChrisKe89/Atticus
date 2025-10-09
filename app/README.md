# Wynstan — GC MFD Root-Cause Chat

Baseline Next.js (App Router) workspace for the Wynstan diagnostics experience. Stage 0 establishes tooling so that Stage 1 can layer the UI frame, panes, and skeleton loaders described in `TODO.md`.

## Prerequisites

All development happens with Node.js 20+ and pnpm.

```powershell
node -v   # expect v20.x
pnpm -v   # expect v10+
git --version
```

If any tool is missing, install them before proceeding (see `TODO.md` for Windows-specific commands).

## Getting started

```powershell
pnpm install
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) to confirm the baseline Tailwind styles render. The landing screen includes a badge and status row that should reflect the Tailwind color tokens configured in `src/app/globals.css`.

## Project scripts

| Command       | Purpose                                |
| ------------- | -------------------------------------- |
| `pnpm dev`    | Start Next.js dev server (Turbopack).  |
| `pnpm build`  | Production build.                      |
| `pnpm start`  | Run the compiled build.                |
| `pnpm lint`   | Lint with the Next.js ESLint config.   |

## Tooling stack

- **Next.js 15** (App Router, TypeScript, Turbopack).
- **Tailwind CSS 3.4** configured via `tailwind.config.ts` with shadcn-compatible tokens.
- **shadcn/ui** configuration via `components.json` (manual bootstrap pending CLI registry access).
- **React Query 5** for client data fetching and caching.
- **Zod** for runtime validation.
- **Lucide icons** for consistent iconography.

Utility helpers such as `cn` live in `src/lib/utils.ts`.

## Next steps

Stage 1 tasks will create the shared layout (header/nav), route placeholders, and skeleton states. Track progress and acceptance criteria in `TODO.md`.
