# 15 — Rate Limiting, Token Revocation, Sentry & Email

> **Audience:** Junior AI engineers. Week 22 hardens the API for production: Redis rate limits, JWT blacklist on logout, optional Sentry observability, and non-blocking transactional email via Resend.

## What We Built

- **`RateLimitService`** + **`RateLimitMiddleware`** — Redis fixed-window counters on sensitive routes (search, auth refresh/login)
- **JWT access-token blacklist** — `jti` claim + Redis key on logout; checked in `get_current_user` and `MCPAuthMiddleware`
- **Sentry SDK** (optional `SENTRY_DSN`) — FastAPI, SQLAlchemy, Celery, httpx integrations
- **`EmailService`** — Resend + Jinja2 templates (`welcome`, `permission_granted`); skips gracefully when `RESEND_API_KEY` is missing
- Frontend: Sentry source-map upload story documented for CI (`VITE_SENTRY_DSN` already optional)

---

## 1. Redis rate-limit windows

A **fixed window** counter answers: “How many requests has this client made in the current minute?”

```text
key:   ratelimit:{bucket}:{identity}:{window_id}
value: integer count
TTL:   ~60 seconds (window length)
```

On each request:

1. Compute `window_id = floor(now / 60)` so every client shares the same wall-clock minute.
2. `INCR` the key; on first hit, `EXPIRE` so Redis cleans up.
3. If count > limit → **429 Too Many Requests** with a clear JSON body.

**Why Redis?** Counters must be shared across uvicorn workers (and later multiple hosts). In-memory dicts only protect a single process.

**Why not limit everything?** Aggressive global limits punish normal SPA browsing (tree loads, list polls). We throttle **expensive or abuse-prone** paths:

| Route pattern | Why |
|---------------|-----|
| `GET .../knowledge-neurons?search_term=` | Voyage embed + vector search cost |
| `POST /api/v1/auth/refresh` | Credential stuffing / token farming |
| `GET /api/v1/auth/google/login` | OAuth start spam |

Identity: authenticated user id from Bearer when present, otherwise client IP. Middleware stays transport-level; business auth stays in `Depends`.

---

## 2. Why blacklist access tokens on logout?

SPA auth has two credentials:

| Credential | Where stored | Lifetime |
|------------|--------------|----------|
| Access JWT | SPA memory (Bearer) | ~15 minutes |
| Refresh JWT | httpOnly cookie | ~7 days |

Clearing the refresh cookie alone is **necessary but not sufficient**. Until the access JWT expires, anyone who copied the Bearer token can still call `/api/v1` and `/mcp`.

**Blacklist approach:**

1. Each access token gets a unique `jti` (JWT ID).
2. On logout, store `jwt:blacklist:{jti}` in Redis with TTL = remaining token lifetime.
3. On every verify (`get_current_user`, MCP middleware), reject if `jti` is blacklisted.

We do **not** need a permanent revoke list — once the JWT’s `exp` passes, the key can expire. Refresh is already invalidated by deleting the cookie (and we do not re-issue refresh on logout).

**Middleware vs Depends (reminder):**

- **Rate limits** → middleware (applies before route matching, path/IP based).
- **JWT validity + blacklist** → `Depends(get_current_user)` for REST; `MCPAuthMiddleware` only for `/mcp`.
- Never put SPA REST auth in a global middleware — it would break public OAuth callbacks and health checks.

---

## 3. Sentry sampling

`traces_sample_rate` (e.g. `0.1`) means “send ~10% of transactions for performance.” Errors still report at full rate when the SDK captures an exception.

Why sample?

- Full tracing is noisy and expensive at scale.
- Learning goal: see errors + a representative slice of latency, not 100% of every health check.

DSN empty → `init_sentry()` is a no-op so local dev stays quiet. Same pattern as the SPA’s `VITE_SENTRY_DSN`.

**Frontend source maps (CI-ready):** Production minified stacks are useless without source maps. In CI, after `pnpm build`, upload maps with `@sentry/vite-plugin` when `SENTRY_AUTH_TOKEN`, `SENTRY_ORG`, and `SENTRY_PROJECT` are set. Keep maps out of the public CDN when possible (upload-only). See `client/docs` / Week 23 CI notes.

---

## 4. Transactional email patterns

Transactional email = “something happened to *this* user” (welcome, permission granted), not marketing blasts.

Patterns we follow:

1. **Optional provider** — missing `RESEND_API_KEY` logs and returns; OAuth/permission APIs still succeed.
2. **Never block the core mutation** — wrap send in try/except; failures are observability, not user-facing 500s.
3. **Jinja2 templates** — HTML lives in `templates/email/`; Python only passes context (`name`, `directory_name`, …).
4. **Fire after success** — welcome only when upsert *created* a user; permission email only after Casbin grant succeeds.

---

## Code Walkthrough

1. **`services/rate_limit.py`** + **`middleware/rate_limit.py`** — counter logic vs HTTP 429 responses.
2. **`services/jwt.py`** — `jti` on issue; `revoke_access_token` / `is_access_token_revoked`.
3. **`api/v1/auth.py`** — logout clears cookie **and** blacklists Bearer when present.
4. **`core/sentry.py`** — optional SDK init with FastAPI / SQLAlchemy / Celery / httpx.
5. **`services/email.py`** + **`templates/email/*.html`** — Resend send helpers.

Middleware order in `main.py` (outer → inner): **CORS → RateLimit → MCPAuth → routes**.

---

## Further Reading

- [Redis INCR rate limiting patterns](https://redis.io/docs/latest/develop/clients/patterns/rate-limiting/)
- [JWT `jti` claim (RFC 7519)](https://datatracker.ietf.org/doc/html/rfc7519#section-4.1.7)
- [Sentry Python sampling](https://docs.sentry.io/platforms/python/configuration/sampling/)
- [Resend Python SDK](https://resend.com/docs/send-with-python)

## Exercises (Optional)

1. Switch the rate limiter from fixed windows to a sliding window (`ZSET` of timestamps) and compare Redis memory use.
2. Add a `Retry-After` header on 429 responses derived from the window TTL.
