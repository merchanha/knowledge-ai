# Knowledge-AI — Progress

Handoff file for new chat sessions. Update after each week.

## Current phase

**Week 22** — Security hardening + observability (next)

## Completed

### Week 1 — FastAPI foundation

- [x] Monorepo layout: `api/` (backend), `client/` (placeholder)
- [x] FastAPI app, CORS, `GET /api/v1/health`
- [x] Docker Compose: PostgreSQL 17 (pgvector), Redis 7
- [x] Dev tooling: uv, ruff, mypy, pytest, pre-commit
- [x] Doc: `api/docs/01-fastapi-async-foundation.md`

### Week 2 — Database layer

- [x] SQLAlchemy 2.x async engine + `get_db()` dependency
- [x] Models: `User`, `Project`, `ProjectMembership`
- [x] `TimestampMixin`, `str_enum_values` (Postgres enum fix)
- [x] Alembic migrations: `users`, `projects`, `project_memberships`
- [x] Redis async client stub + health check
- [x] `GET /api/v1/health/ready` (DB + Redis)
- [x] Doc: `api/docs/02-sqlalchemy-async-alembic.md`

### Week 3 — SPA authentication

- [x] `OAuthService`, `OAuthFlowService`, `JWTService`, `UserService`
- [x] `GET /api/v1/auth/google/login`
- [x] `GET /api/v1/auth/google/callback` → JWT fragment + httpOnly refresh cookie
- [x] `POST /api/v1/auth/refresh`, `POST /api/v1/auth/logout`
- [x] `get_current_user` dependency; `GET /api/v1/auth/me`
- [x] Doc: `api/docs/03-oauth-jwt-auth.md`
- [x] Deps: `authlib`, `PyJWT`

### Week 4 — Casbin RBAC

- [x] `CasbinPermissionService` + casbin-async-sqlalchemy-adapter
- [x] Roles (`admin`, `user`); directory permissions (`READ`, `WRITE`, `MANAGE`)
- [x] `require_admin`, `require_directory_permission`; admin + permissions endpoints
- [x] Alembic: `casbin_rule` table; startup seed `p, admin, *, *`
- [x] OAuth login syncs Casbin grouping policy from `users.role`
- [x] Doc: `api/docs/04-rbac-with-casbin.md`
- [x] Deps: `casbin`, `casbin-async-sqlalchemy-adapter`

### Week 5 — Directory domain model

- [x] `directories` table (adjacency list: `parent_id`, scoped to `project_id`)
- [x] `Directory` ORM model; one root per project; sibling name uniqueness
- [x] `DirectoryService`: create, rename, move, delete (cascade + cycle rules)
- [x] `ProjectService.create` → auto-create root directory (`"Root"`)
- [x] Alembic: `20260613_0001_add_directories_table`
- [x] Doc: `api/docs/05-hierarchical-data-trees.md`
- [x] Tests: `tests/test_directory.py` (integration against Postgres)

### Week 6 — Directory REST API

- [x] `api/v1/directories.py` — tree, children, breadcrumbs, CRUD, ZIP download
- [x] `require_directory_permission` wired on every route (dual WRITE check on move)
- [x] `DownloadService` — BFS subtree walk → in-memory ZIP
- [x] Permission grant/revoke validates directory exists (`404`)
- [x] Casbin matcher fix: `MANAGE` ⊃ `WRITE` ⊃ `READ` (policy → request direction)
- [x] Doc: `api/docs/06-controller-service-separation.md`
- [x] Tests: `tests/test_directories_api.py` (JWT + Postgres integration)

### Week 7 — KnowledgeNeuron CRUD

- [x] `knowledge_neurons` table: title, content, `directory_id`, `metadata` (JSONB)
- [x] `KnowledgeNeuron` ORM model; `KnowledgeNeuronService` CRUD + list by directory
- [x] `api/v1/knowledge_neurons.py` — thin REST controllers with directory permission checks
- [x] Alembic: `20260620_0001_add_knowledge_neurons_table`
- [x] Doc: `api/docs/07-domain-modeling-patterns.md`
- [x] Tests: `tests/test_knowledge_neuron.py`, `tests/test_knowledge_neurons_api.py`

### Week 8 — Embedding pipeline

- [x] `EmbeddingService` + Voyage AI client (`voyage-code-3`) via httpx
- [x] Celery app + Redis broker; task `embed_knowledge_neuron(neuron_id)`
- [x] Trigger embed on create/update via `KnowledgeNeuronService._enqueue_embed`
- [x] pgvector column `embedding vector(1024)` on `knowledge_neurons`
- [x] Settings: `VOYAGE_API_KEY`, `VOYAGE_MODEL`, `VOYAGE_EMBEDDING_DIMENSIONS`
- [x] Alembic: `20260620_0002_add_knowledge_neuron_embedding`
- [x] Doc: `api/docs/08-embeddings-and-celery.md`
- [x] Deps: `celery`, `pgvector`

### Week 9 — Vector search

- [x] pgvector HNSW index (cosine) — `20260620_0003_add_knowledge_neuron_hnsw_index`
- [x] `GET /api/v1/knowledge-neurons?search_term=...` scoped to readable directories
- [x] `EmbeddingService.search`: embed query → cosine rank → top-k
- [x] Redis query-embedding cache (5-minute TTL)
- [x] `CasbinPermissionService.get_readable_directory_ids`
- [x] Doc: `api/docs/09-vector-search-pgvector.md`
- [x] Tests: `tests/test_embedding.py`

### Week 10 — Command CRUD

- [x] `commands` table: title, content, `directory_id`, `metadata` (JSONB)
- [x] `Command` ORM model; `CommandService` CRUD + list by directory (no embeddings)
- [x] `api/v1/commands.py` — thin REST controllers with directory permission checks
- [x] Alembic: `20260704_0001_add_commands_table`
- [x] Doc: `api/docs/10-reusing-domain-patterns.md`
- [x] Tests: `tests/test_command.py`, `tests/test_commands_api.py`

### Week 11 — Project, Membership, Users, Account

- [x] `ProjectService` — CRUD, archive/unarchive, delete
- [x] `MembershipService` — add/remove members, roles; auto-grant `MANAGE` on project root
- [x] `UserService.update` — admin role/status management; `PATCH /api/v1/admin/users/{id}`
- [x] `GET /api/v1/account`, `PATCH /api/v1/account/projects/{id}` — `is_context_exposed` toggle
- [x] `api/v1/projects.py` — project + membership REST routes
- [x] Alembic: `20260704_0002_add_is_context_exposed_to_memberships`
- [x] Doc: `api/docs/11-multi-tenant-project-scoping.md`
- [x] Tests: `tests/test_project_membership.py`, `tests/test_projects_api.py`

### Week 12 — MCP foundation + agent auth

- [x] `mcp[cli]`; FastMCP mounted at `/mcp` (Streamable HTTP); stdio via `python -m knowledge_ai.mcp.stdio`
- [x] `/.well-known/oauth-authorization-server` + `/.well-known/oauth-protected-resource`
- [x] `PKCEService`; `OAuthFlowService` MCP authorize/callback/token flow
- [x] `MCPAuthMiddleware` — route-scoped Bearer JWT on `/mcp` only
- [x] `GET /api/v1/auth/mcp/authorize`, `callback`, `POST /api/v1/auth/mcp/token`
- [x] Doc: `api/docs/12-mcp-oauth-and-protocol.md`
- [x] Tests: `tests/test_pkce.py`, `tests/test_mcp_auth.py`

### Week 13 — MCP search tools

- [x] Tool `search_knowledge_neurons` — reuses `EmbeddingService.search` + Casbin scoping
- [x] Tool `list_commands` — browse by directory or all readable directories
- [x] `CommandService.list_in_directories`
- [x] Doc: `api/docs/13-mcp-tool-design.md`
- [x] Tests: `tests/test_mcp_tools.py`

### Week 14 — ProjectContext retrieval

- [x] `ContextBuilder` — assembles `ProjectContext` from exposed project directory trees
- [x] Tool `get_project_context` — projects where `is_context_exposed=true`
- [x] `schemas/project_context.py` — `ProjectDirectoryNode`, `ProjectTree`, etc.
- [x] stdio integration test: `tests/test_mcp_stdio.py`
- [x] Doc: `api/docs/14-project-context-for-agents.md`
- [x] Tests: `tests/test_context_builder.py`

### Week 15 — Frontend bootstrap

- [x] `client/` Vite + React 19 + TypeScript + pnpm
- [x] Tailwind CSS v4 + shadcn/ui; AppShell; React Router v7
- [x] Axios → `/api/v1` (Vite proxy); TanStack Query (no Zustand)
- [x] Sentry browser SDK (optional `VITE_SENTRY_DSN`)
- [x] Doc: `client/docs/01-react-spa-architecture.md`

### Week 16 — Auth feature module

- [x] `/login` → Google OAuth via `GET /api/v1/auth/google/login`
- [x] `/auth/callback` — `#token=` → in-memory session (`features/auth/session.ts` + `useSyncExternalStore`)
- [x] Axios interceptors: Bearer + auto-refresh on 401 (`POST /auth/refresh`)
- [x] `ProtectedRoute`; `GET /auth/me` via TanStack Query
- [x] Doc: `client/docs/02-spa-auth-patterns.md`

### Week 17 — Directories feature module

- [x] Directory tree, breadcrumbs, create/rename/move/delete dialogs
- [x] Admin permission grant/revoke UI
- [x] Hooks: `useDirectoryTree`, `useBreadcrumbs`, `useDirectoryMutations`
- [x] Wired to `/api/v1/projects/{id}/directories/*` + Casbin permission routes
- [x] Doc: `client/docs/03-feature-module-structure.md`

### Week 18 — KnowledgeNeuron feature module

- [x] `features/knowledge-neurons/` — api, hooks, list/form/delete dialogs, panel
- [x] Routes: `/knowledge` (+ project/directory scoped); semantic search via `?q=` → `search_term`
- [x] Hooks: `useKnowledgeNeurons`, `useKnowledgeNeuronSearch`, `useKnowledgeNeuronMutations`
- [x] Directory detail pane embeds `KnowledgeNeuronPanel`
- [x] Poll list while any neuron has `has_embedding: false` (chip updates without reload)
- [x] Doc: `client/docs/04-tanstack-query-patterns.md`

### Week 19 — Commands feature module

- [x] `features/commands/` — same CRUD pattern as KnowledgeNeurons, no search/embeddings
- [x] Routes: `/commands` (+ project/directory scoped)
- [x] Directory detail pane embeds `CommandPanel`
- [x] Shared browse shell (project picker cards + folder sidebar) for Knowledge/Commands

### Week 20 — Account + Projects admin

- [x] `/account` — project list + `is_context_exposed` toggle
- [x] `/projects` create (admin); `/projects/:id` — edit, archive/unarchive, delete, members
- [x] Doc: `client/docs/05-admin-ui-patterns.md`

### Week 21 — Users admin + polish

- [x] `/users` — admin role/active management (`AdminRoute`)
- [x] Error boundary, toasts, loading/empty states, `getApiErrorMessage`, responsive nav
- [x] Card UI (ItemCard + kebabs); session-expired login fix (clear dead Bearer)
- [x] API: `search_min_similarity` (default 0.45) on semantic search
- [x] Doc: `client/docs/06-frontend-error-handling.md`

## Key decisions

| Topic | Decision |
|-------|----------|
| Repo layout | Monorepo: `api/` + `client/` |
| Domain naming | `KnowledgeNeuron` (not "pill"); MCP output: `ProjectContext` |
| Auth (SPA) | Google OAuth + JWT access (fragment) + httpOnly refresh cookie |
| Auth (MCP) | OAuth + PKCE via `/.well-known/*` → JWT Bearer on `/mcp` |
| SPA server state | TanStack Query; access token in module store (not Zustand) |
| Brief | `knowledge-ai-project-brief.md` is local-only (gitignored) |
| Author email | merchanha@gmail.com |
| Directory tree | Adjacency list (`parent_id`); fixed root name `"Root"` |
| Delete cascade | ORM `cascade="all, delete-orphan"` + DB `ON DELETE CASCADE` |
| Embedding model | Voyage AI `voyage-code-3` (1024 dimensions) |
| Vector index | pgvector HNSW with `vector_cosine_ops` |
| MCP exposure flag | `project_memberships.is_context_exposed` (per-user, per-project) |
| Command CRUD | Duplicate KnowledgeNeuron pattern; no embeddings or Celery |
| MCP transport | Streamable HTTP at `/mcp`; stdio for local dev (`MCP_STDIO_USER_ID` optional) |
| SPA mutations | Invalidate-on-success (not optimistic by default); poll while embeddings pending |
| Admin UI gates | `AdminRoute` + hide controls; API remains the security boundary |
| Search floor | `search_min_similarity` default 0.45 (drop weak nearest-neighbors) |

## Local setup

```bash
cd api
uv sync --all-extras --dev
cp .env.example .env
# Set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, JWT_SECRET_KEY, VOYAGE_API_KEY in .env
docker compose up -d
uv run alembic upgrade head
uv run uvicorn knowledge_ai.main:app --reload --port 8000
# Terminal 2 — Celery worker for embeddings:
uv run celery -A knowledge_ai.core.celery_app worker --loglevel=info -Q embeddings
# Terminal 3 — stdio MCP (local agent testing):
uv run python -m knowledge_ai.mcp.stdio
# Terminal 4 — React SPA:
cd ../client && pnpm install && pnpm dev
```

**Google OAuth redirect URIs (register both in Google Console):**

- SPA: `http://localhost:8000/api/v1/auth/google/callback`
- MCP: `http://localhost:8000/api/v1/auth/mcp/callback`

**SPA OAuth callback (CORS / redirect_uri):** `http://localhost:5173/auth/callback`

**TablePlus:** `knowledge_ai` / `knowledge_ai` @ `localhost:5432` / DB `knowledge_ai`

## Next steps (Week 22)

- [ ] `RateLimitMiddleware` (Redis) + JWT blacklist on logout
- [ ] Sentry on FastAPI/SQLAlchemy/Celery/httpx; frontend source maps in CI
- [ ] Resend + Jinja2 email templates
- [ ] Doc: `api/docs/15-rate-limiting-token-revocation-sentry.md`

## Repo

https://github.com/merchanha/knowledge-ai
