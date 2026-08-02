"""Path-scoped Redis rate limiting for sensitive API routes."""

from __future__ import annotations

import logging
from typing import Any

import jwt
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from knowledge_ai.core.config import get_settings
from knowledge_ai.services.rate_limit import RateLimitService

logger = logging.getLogger(__name__)


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client is not None:
        return request.client.host
    return "unknown"


def _identity_from_request(request: Request) -> str:
    """Prefer JWT ``sub`` when Bearer is present; fall back to client IP."""
    authorization = request.headers.get("Authorization")
    if authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ").strip()
        try:
            # Unverified decode — only used for rate-limit bucketing, not auth.
            payload: dict[str, Any] = jwt.decode(
                token,
                options={"verify_signature": False, "verify_exp": False},
            )
            sub = payload.get("sub")
            if isinstance(sub, str) and sub:
                return f"user:{sub}"
        except Exception:
            logger.debug("Could not decode Bearer for rate-limit identity", exc_info=True)
    return f"ip:{_client_ip(request)}"


def _match_bucket(request: Request) -> tuple[str, int] | None:
    """Return (bucket_name, limit) when this path should be rate-limited."""
    settings = get_settings()
    path = request.url.path
    method = request.method.upper()

    if (
        method == "GET"
        and path.rstrip("/").endswith("/knowledge-neurons")
        and request.query_params.get("search_term")
    ):
        return "search", settings.rate_limit_search_per_window

    if method == "POST" and path == "/api/v1/auth/refresh":
        return "auth_refresh", settings.rate_limit_auth_per_window

    if method == "GET" and path == "/api/v1/auth/google/login":
        return "auth_login", settings.rate_limit_auth_per_window

    return None


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Enforce Redis rate limits on selected sensitive routes."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        settings = get_settings()
        if not settings.rate_limit_enabled:
            return await call_next(request)

        matched = _match_bucket(request)
        if matched is None:
            return await call_next(request)

        bucket, limit = matched
        identity = _identity_from_request(request)
        service = RateLimitService(settings)

        try:
            decision = await service.check(
                bucket=bucket,
                identity=identity,
                limit=limit,
            )
        except Exception:
            # Fail open — rate limits must not take down the API if Redis blips.
            logger.exception("Rate limit check failed; allowing request")
            return await call_next(request)

        if not decision.allowed:
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Rate limit exceeded",
                    "bucket": bucket,
                    "limit": decision.limit,
                    "retry_after_seconds": decision.retry_after_seconds,
                },
                headers={
                    "Retry-After": str(decision.retry_after_seconds),
                    "X-RateLimit-Limit": str(decision.limit),
                    "X-RateLimit-Remaining": "0",
                },
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(decision.limit)
        response.headers["X-RateLimit-Remaining"] = str(decision.remaining)
        return response
