# Knowledge-AI Client

React SPA for browsing projects and directories (Weeks 15–17). KnowledgeNeuron / Command UIs land in Weeks 18+.

## Stack

- Vite 8 + React 19 + TypeScript
- Tailwind CSS v4 + shadcn/ui
- React Router v7
- Axios → `/api/v1` (proxied to `http://localhost:8000`)
- TanStack Query for server state
- In-memory auth session (no Zustand — see `docs/01`)
- Sentry browser SDK (optional stub DSN)

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
