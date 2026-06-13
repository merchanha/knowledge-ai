# Knowledge-AI — Progress

Handoff file for new chat sessions. Update after each week.

## Current phase

**Week 6** — Directory REST API, breadcrumbs, ZIP download

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

## Key decisions

| Topic | Decision |
|-------|----------|
| Repo layout | Monorepo: `api/` + `client/` |
| Domain naming | `KnowledgeNeuron` (not "pill"); MCP output: `StratumContext` |
| Auth (SPA) | Google OAuth + JWT access (fragment) + httpOnly refresh cookie |
| Auth (MCP) | OAuth + PKCE (Week 12) |
| Brief | `knowledge-ai-project-brief.md` is local-only (gitignored) |
| Author email | merchanha@gmail.com |
| Directory tree | Adjacency list (`parent_id`); fixed root name `"Root"` |
| Delete cascade | ORM `cascade="all, delete-orphan"` + DB `ON DELETE CASCADE` |

## Local setup

```bash
cd api
uv sync --all-extras --dev
cp .env.example .env
# Set GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, JWT_SECRET_KEY in .env
docker compose up -d
uv run alembic upgrade head
uv run uvicorn knowledge_ai.main:app --reload --port 8000
```

**Google OAuth redirect URI:** `http://localhost:8000/api/v1/auth/google/callback`

**TablePlus:** `knowledge_ai` / `knowledge_ai` @ `localhost:5432` / DB `knowledge_ai`

## Next steps (Week 6)

- [ ] Directory REST API: tree listing, breadcrumbs, CRUD endpoints
- [ ] Wire `require_directory_permission` on directory routes
- [ ] `DownloadService`: ZIP download for directory subtree
- [ ] Doc: `api/docs/06-controller-service-separation.md`

## Repo

https://github.com/merchanha/knowledge-ai
