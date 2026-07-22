# 06 — Frontend Error Handling

## What We Built

Week 21 finishes Users admin and SPA polish: root `ErrorBoundary`, toast notifications, shared loading/empty states, FastAPI `detail` extraction for user-facing errors, and responsive header nav. Sentry remains optional via `VITE_SENTRY_DSN`.

## Key Concepts

### Error boundaries (render crashes)

React **error boundaries** catch errors thrown during **render** in the child tree — not async event handlers or Query failures. We use a class `ErrorBoundary` around the app:

1. `getDerivedStateFromError` → show fallback UI
2. `componentDidCatch` → `Sentry.captureException` when DSN is set
3. Offer a recovery path (reload / navigate home)

Query/mutation failures stay in hooks: `isError` + toast/`getApiErrorMessage`.

### Toasts vs inline errors

| Situation | Prefer |
|-----------|--------|
| Page load failed | Inline message / empty state |
| Mutation succeeded or failed | Toast (non-blocking) |
| Entire subtree crashed | Error boundary fallback |

`lib/toast.ts` is a tiny `useSyncExternalStore` store — no Zustand. Enough for success/error feedback without a toast library.

### Loading and empty states

Reuse `LoadingState` and `EmptyState` so every feature does not invent its own “nothing here” copy. Empty states should say **what to do next** (“Ask an admin…”, “Create a project…”).

### Sentry on the client

```ts
// lib/sentry.ts
if (VITE_SENTRY_DSN) {
  Sentry.init({ dsn, environment: MODE, tracesSampleRate: 0.1 })
}
```

Locally, leave `VITE_SENTRY_DSN` empty — init no-ops. In production CI, set the DSN (and later, source maps in Week 22+). Boundaries + unhandled promise rejections are the main signal; do not send every 404 toast to Sentry.

### User-facing API errors

Axios wraps HTTP failures. FastAPI returns `{ "detail": "..." }`. Use `getApiErrorMessage(error)` so users see “Directory WRITE permission required” instead of “Request failed with status code 403”.

## Code Walkthrough

1. `components/ErrorBoundary.tsx` — render crash + Sentry.
2. `lib/toast.ts` + `ToastViewport` — ephemeral feedback.
3. `lib/errors.ts` — Axios/FastAPI detail extraction.
4. `features/admin/pages/UsersPage.tsx` — admin table with role/active mutations.

## Further Reading

- [React Error Boundaries](https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary)
- [Sentry React](https://docs.sentry.io/platforms/javascript/guides/react/)
- Backend observability (Week 22): rate limits + server Sentry

## Exercises (Optional)

1. Add a Query `QueryCache` `onError` that toasts unexpected 5xx once.
2. Wrap each feature page in a nested boundary so one page crash does not blank the shell.
