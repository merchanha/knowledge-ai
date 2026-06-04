# Knowledge-AI — Progress

Handoff file for new chat sessions. Update after each week.

## Current phase

**Week 4** — PyCasbin RBAC, `CasbinPermissionService`

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

## Key decisions

| Topic | Decision |
|-------|----------|
| Repo layout | Monorepo: `api/` + `client/` |
| Domain naming | `KnowledgeNeuron` (not "pill"); MCP output: `StratumContext` |
| Auth (SPA) | Google OAuth + JWT access (fragment) + httpOnly refresh cookie |
| Auth (MCP) | OAuth + PKCE (Week 12) |
| Brief | `knowledge-ai-project-brief.md` is local-only (gitignored) |
| Author email | merchanha@gmail.com |

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

## Next steps (Week 4)

- [ ] `CasbinPermissionService` + casbin-async-sqlalchemy-adapter
- [ ] Roles (`admin`, `user`); directory permissions (`READ`, `WRITE`, `MANAGE`)
- [ ] Permission checks on resource endpoints; admin-only gates
- [ ] Doc: `api/docs/04-rbac-with-casbin.md`

## Repo

https://github.com/merchanha/knowledge-ai
