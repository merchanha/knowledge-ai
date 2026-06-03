# Knowledge-AI — Progress

Handoff file for new chat sessions. Update after each week.

## Current phase

**Week 3** — Google OAuth, JWT, refresh cookie, `UserService`

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

## Key decisions

| Topic | Decision |
|-------|----------|
| Repo layout | Monorepo: `api/` + `client/` |
| Domain naming | `KnowledgeNeuron` (not "pill"); MCP output: `StratumContext` |
| Auth (planned) | SPA: Google OAuth + JWT; MCP: OAuth + PKCE (Week 12) |
| Brief | `knowledge-ai-project-brief.md` is local-only (gitignored) |
| Author email | merchanha@gmail.com |

## Local setup

```bash
cd api
uv sync --all-extras --dev
cp .env.example .env
docker compose up -d
uv run alembic upgrade head
uv run uvicorn knowledge_ai.main:app --reload --port 8000
```

**TablePlus:** `knowledge_ai` / `knowledge_ai` @ `localhost:5432` / DB `knowledge_ai`

## Next steps (Week 3)

- [ ] `OAuthService`, `JWTService`, `UserService`
- [ ] `GET /api/v1/auth/google/login`
- [ ] OAuth callback → JWT + httpOnly refresh cookie
- [ ] `POST /api/v1/auth/refresh`, `POST /api/v1/auth/logout`
- [ ] `get_current_user` dependency
- [ ] Doc: `api/docs/03-oauth-jwt-auth.md`

## Repo

https://github.com/merchanha/knowledge-ai
