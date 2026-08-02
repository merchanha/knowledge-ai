# 07 — Frontend Testing

> **Audience:** Junior engineers learning the Knowledge-AI SPA. Week 23 adds Vitest + React Testing Library for the pieces most likely to regress: auth session, directory tree, KnowledgeNeuron form dialog.

## What We Built

- **Vitest** + **jsdom** + **React Testing Library**
- Tests for:
  - `features/auth/session.ts` — in-memory access token store
  - `DirectoryTree` — expand/select/actions visibility
  - `KnowledgeNeuronFormDialog` — validation + submit payload
- npm scripts: `pnpm test`, `pnpm test:run`
- Documented Sentry source-map upload for production CI builds

---

## 1. What we test (and what we don’t)

| Prefer | Skip (for now) |
|--------|----------------|
| Pure session helpers | Full Google OAuth in a browser |
| Dialog submit contracts | Pixel-perfect Tailwind |
| Tree interaction (expand, links) | Entire AppShell + router smoke |

TanStack Query hooks are easier with MSW later; Week 23 focuses on **components and session**, which fail often during refactors and need no backend.

---

## 2. Vitest vs Jest

Vite projects use **Vitest**: same config spirit as Vite, ESM-native, fast. React Testing Library queries by role/label (`getByRole`, `getByLabelText`) so tests mirror how users and assistive tech see the UI.

---

## 3. Sentry source maps (CI-ready)

Minified production stacks are useless without source maps.

1. Keep `VITE_SENTRY_DSN` for runtime error reporting (already in `src/lib/sentry.ts`).
2. In CI production builds, set `SENTRY_AUTH_TOKEN`, `SENTRY_ORG`, `SENTRY_PROJECT`.
3. `@sentry/vite-plugin` (optional in `vite.config.ts`) uploads maps during `pnpm build` when those env vars exist.
4. Prefer upload-only maps — do not leave `.map` files publicly downloadable on CloudFront if you can avoid it.

Local `pnpm build` without those secrets simply skips upload.

---

## Further Reading

- [Vitest](https://vitest.dev/)
- [Testing Library — React](https://testing-library.com/docs/react-testing-library/intro/)
- [Sentry Vite plugin](https://docs.sentry.io/platforms/javascript/guides/react/sourcemaps/uploading/vite/)

## Exercises (Optional)

1. Add a test that `ProtectedRoute` redirects when `useAccessToken()` is null (wrap with MemoryRouter).
2. Mock `api.post('/auth/logout')` and assert `clearAccessToken` runs in the logout mutation.
