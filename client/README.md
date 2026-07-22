# Knowledge-AI Client

React SPA for Knowledge-AI: auth, directories, KnowledgeNeurons, Commands, account/MCP exposure, and admin (projects + users).

## Stack

- Vite 8 + React 19 + TypeScript
- Tailwind CSS v4 + shadcn/ui
- React Router v7
- Axios → `/api/v1` (proxied to `http://localhost:8000`)
- TanStack Query for server state (no Zustand by default)
- In-memory auth session — see `docs/02`
- Sentry browser SDK (optional `VITE_SENTRY_DSN`)

## Setup

```bash
cd client
pnpm install
cp .env.example .env   # optional overrides
pnpm dev               # http://localhost:5173
```

API must be running on port 8000 (`api/` + Docker Compose). Google OAuth redirect URI stays:

`http://localhost:8000/api/v1/auth/google/callback`

SPA callback (CORS + `redirect_uri`):

`http://localhost:5173/auth/callback`

## Routes

| Path | Purpose |
|------|---------|
| `/projects` | Project list (+ admin create) |
| `/projects/:id` | Admin project detail / members |
| `/projects/:id/directories/:directoryId?` | Directory tree + neuron/command panels |
| `/knowledge` | KnowledgeNeuron browse + semantic search |
| `/commands` | Command browse (no search) |
| `/account` | MCP `is_context_exposed` toggles |
| `/users` | Admin user role/status |

## Scripts

| Command        | Purpose              |
|----------------|----------------------|
| `pnpm dev`     | Vite dev server      |
| `pnpm build`   | Typecheck + production build |
| `pnpm preview` | Preview production build |
| `pnpm lint`    | oxlint                |

## Docs

- `docs/01-react-spa-architecture.md`
- `docs/02-spa-auth-patterns.md`
- `docs/03-feature-module-structure.md`
- `docs/04-tanstack-query-patterns.md`
- `docs/05-admin-ui-patterns.md`
- `docs/06-frontend-error-handling.md`
