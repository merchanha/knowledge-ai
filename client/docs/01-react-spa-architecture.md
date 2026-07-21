# 01 — React SPA Architecture

## What We Built

Week 15 bootstraps the `client/` Vite + React 19 + TypeScript SPA: Tailwind CSS v4, shadcn/ui, React Router v7 shell, Axios client pointed at `/api/v1`, TanStack Query, and an optional Sentry DSN. The monorepo layout remains `api/` + `client/`; Vite proxies `/api` to `http://localhost:8000` so browser calls stay same-origin in local dev while CORS still allows `http://localhost:5173` for production-like cookie flows.

## Key Concepts

### SPA (Single-Page Application)

The browser loads one HTML shell; React Router swaps views without full page reloads. The FastAPI backend stays the source of truth — the SPA is a thin client over REST.

### Vite

Vite is the dev server and bundler. In development it serves ES modules with Hot Module Replacement (instant updates). In production it emits optimized static assets. Port **5173** matches the backend `CORS_ORIGINS` default.

### Feature modules

Code is grouped by domain (`features/auth`, `features/directories`, `features/projects`) instead of by technical layer alone. Each feature owns its API helpers, hooks, and UI. Shared primitives live in `components/ui` and `lib/`.

### Server state vs client state

| Kind | Examples | Tool |
|------|----------|------|
| **Server state** | `/auth/me`, project list, directory tree | **TanStack Query** — cache, refetch, mutations, invalidation |
| **Client credentials** | JWT access token after `#token=` | Tiny module + `useSyncExternalStore` (`features/auth/session.ts`) |
| **Local UI state** | which dialog is open, tree expand/collapse | React `useState` in the component |

**TanStack Query is enough** when the data comes from the API and can be identified by a query key. You invalidate keys after mutations instead of hand-syncing arrays.

**Zustand (or another global store) is justified** when many distant components need the same *non-server* client state and React context would re-render too broadly — for example a complex multi-panel editor selection model. We did **not** add Zustand: the access token is a single module with subscribers, and Query covers API data.

### Thin pages, fat hooks

Pages (`*Page.tsx`) compose layout and wire hooks. Fetching, mutations, and cache orchestration live in hooks (`useDirectoryTree`, `useAuth`). That keeps routes readable and makes hooks reusable from other views later.

## Code Walkthrough

1. `src/main.tsx` — QueryClientProvider + BrowserRouter + Sentry init.
2. `src/lib/api.ts` — Axios instance (`withCredentials` for refresh cookie).
3. `src/App.tsx` — route table: public login/callback, protected app shell.
4. `vite.config.ts` — `@` alias, Tailwind plugin, `/api` proxy.

## Further Reading

- [Vite Guide](https://vite.dev/guide/)
- [TanStack Query docs](https://tanstack.com/query/latest/docs/framework/react/overview)
- [React Router](https://reactrouter.com/)

## Exercises (Optional)

1. Add a React Query Devtools panel in development only.
2. Introduce a `features/health` hook that polls `GET /api/v1/health` and shows API status in the header.
