# 16 — Testing Async Python

> **Audience:** Junior AI engineers. Week 23 expands pytest coverage and explains *why* we structure tests the way we do — not cargo-cult coverage percentages.

## What We Built

- Expanded service tests: rate limits + JWT blacklist with **fakeredis**, email no-op paths, existing directory / embedding / ContextBuilder suites
- Coverage gate aimed at **`services/` ≥ 70%** in CI (`--cov=knowledge_ai.services --cov-fail-under=70`)
- Shared patterns: async fixtures, transaction rollback, dependency overrides

---

## 1. Async pytest fixtures

With `pytest-asyncio` (`asyncio_mode = auto`), an `async def` test runs on an event loop. An async fixture can yield a live `AsyncSession` or `httpx.AsyncClient`:

```python
@pytest.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    engine = create_async_engine(..., poolclass=NullPool)
    connection = await engine.connect()
    transaction = await connection.begin()
    session = AsyncSession(bind=connection, expire_on_commit=False)
    try:
        yield session
    finally:
        await session.close()
        await transaction.rollback()  # never leave test data behind
        ...
```

**Why `NullPool`?** Async engines + pytest’s event-loop lifecycle fight connection pooling; NullPool avoids “attached to a different loop” errors.

---

## 2. fakeredis

Real Redis in every unit test is slow and flaky (port conflicts, leftover keys). **fakeredis** implements the Redis API in-process:

```python
from fakeredis.aioredis import FakeRedis

client = FakeRedis(decode_responses=True)
jwt_service = JWTService(settings, redis=client)
```

Use it for:

- Rate-limit counters (`INCR` / `EXPIRE`)
- JWT blacklist (`SET` with TTL)
- Query-embedding cache (when testing EmbeddingService in isolation)

Integration tests that need the *real* Docker Redis (MCP auth codes, readiness) still hit localhost — that is intentional.

---

## 3. Unit vs integration — what belongs where

| Layer | Example | Asserts |
|-------|---------|---------|
| **Unit** | `RateLimitService`, `JWTService.revoke_*`, `EmailService` without API key | Pure logic; fake Redis / no I/O |
| **Service integration** | `DirectoryService` + Postgres transaction | SQL, constraints, cascades |
| **HTTP / API** | `AsyncClient` + dependency overrides | Status codes, cookies, auth gates |
| **MCP / stdio** | Process or mounted `/mcp` | Protocol surface |

Rule of thumb: if a failure would mean “business rule wrong,” prefer a fast unit/service test. If it would mean “wiring wrong,” use an API test with overrides.

---

## 4. Coverage goals that teach (not cargo-cult)

**≥ 70% on `services/`** is a *learning gate*:

- Forces tests on auth, directories, embeddings, ContextBuilder — the domain heart.
- Does **not** require 100% of controllers, middleware, or MCP glue (those are thinner and better covered by a few integration tests).
- Does **not** mean “coverage = quality.” A thoughtful assertion on blacklist TTL beats asserting every line of a Jinja template.

When coverage dips, ask: “Which service behavior can silently break production?” Cover that first.

---

## 5. CI matrix for this monorepo

One workflow, two jobs (or a matrix):

| Job | Working dir | Gates |
|-----|-------------|-------|
| `api` | `api/` | `ruff`, `mypy`, `pytest` (+ services cov) |
| `client` | `client/` | `oxlint`, `tsc`, `vitest` |

Services (Postgres, Redis) start via Docker Compose or GitHub service containers for API integration tests.

---

## Code Walkthrough

1. **`tests/test_rate_limit_jwt_blacklist.py`** — fakeredis unit tests for Week 22.
2. **`tests/test_email.py`** — proves missing Resend key never raises.
3. **`tests/conftest.py`** — shared `AsyncClient` for HTTP tests.
4. **Existing** `test_directory.py`, `test_embedding.py`, `test_context_builder.py` — service integration against Postgres.

---

## Further Reading

- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [fakeredis](https://fakeredis.readthedocs.io/)
- [Coverage.py](https://coverage.readthedocs.io/)

## Exercises (Optional)

1. Add a unit test that mocks Voyage httpx and asserts Redis query-cache hit on the second `embed_query`.
2. Measure coverage of `services/` locally: `uv run pytest --cov=knowledge_ai.services --cov-report=term-missing`.
