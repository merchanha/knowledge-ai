# 01 — FastAPI Async Foundation

## What We Built

Week 1 establishes the backend skeleton inside `api/`:

- FastAPI application with controller–service separation layout
- `GET /api/v1/health` health check endpoint
- CORS middleware configured for the future React SPA (`http://localhost:5173`)
- Docker Compose with PostgreSQL 17 (pgvector) and Redis 7
- Dev tooling: uv, ruff, mypy (strict), pytest, pre-commit

## Key Concepts

### ASGI and FastAPI

FastAPI runs on **ASGI** (Asynchronous Server Gateway Interface), the async successor to WSGI. Uvicorn is the ASGI server that runs our app. Handlers defined with `async def` can await I/O (database, HTTP calls) without blocking other requests.

### Application Factory Pattern

`create_app()` in `main.py` builds the FastAPI instance. This pattern makes testing easy — tests import `app` directly without starting a server.

### Controller–Service Separation

| Layer | Location | Responsibility |
|-------|----------|----------------|
| Controllers | `api/v1/*.py` | Parse HTTP requests, return responses |
| Services | `services/*.py` | Business logic (added from Week 2 onward) |
| Schemas | `schemas/*.py` | Pydantic validation models |
| Models | `models/*.py` | SQLAlchemy ORM (Week 2) |

Week 1 keeps the health controller thin — it returns config values directly. As complexity grows, logic moves into services.

### Middleware vs Depends

- **Middleware** (`middleware/cors.py`) wraps every request — used for cross-cutting concerns like CORS.
- **Depends** (introduced Week 3) injects per-route dependencies like authentication.

Rule: use middleware for transport-level concerns; use `Depends` for business auth and database sessions.

### Dependency Injection with Pydantic Settings

`core/config.py` uses `pydantic-settings` to load configuration from environment variables and `.env`. The `@lru_cache` on `get_settings()` ensures settings are read once.

## Code Walkthrough

1. **`main.py`** — Creates the app, registers CORS, mounts the v1 router at `/api/v1`.
2. **`api/v1/health.py`** — Thin controller: returns `{ status, version }`.
3. **`middleware/cors.py`** — Allows the SPA origin with credentials (needed for httpOnly refresh cookies in Week 3).

## Project Layout

```
api/
├── src/knowledge_ai/
│   ├── main.py
│   ├── api/v1/          # Controllers
│   ├── services/        # Business logic
│   ├── models/          # ORM models
│   ├── schemas/         # Pydantic DTOs
│   ├── core/            # Config, deps
│   └── middleware/      # CORS, rate limit (later)
├── tests/
├── docs/
└── docker-compose.yml
```

## Further Reading

- [FastAPI documentation](https://fastapi.tiangolo.com/)
- [Pydantic Settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [uv package manager](https://docs.astral.sh/uv/)

## Exercises (Optional)

1. Add a `GET /api/v1/health/ready` endpoint that will later check database connectivity.
2. Extend `Settings` with a `log_level` field and configure Uvicorn log level from it.
