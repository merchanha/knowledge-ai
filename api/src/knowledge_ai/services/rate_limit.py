"""Redis-backed fixed-window rate limiting."""

from __future__ import annotations

import time
from dataclasses import dataclass

from redis.asyncio import Redis

from knowledge_ai.core.config import Settings
from knowledge_ai.core.redis import get_redis

RATE_LIMIT_KEY_PREFIX = "ratelimit:"


@dataclass(frozen=True)
class RateLimitDecision:
    """Outcome of a rate-limit check."""

    allowed: bool
    limit: int
    remaining: int
    retry_after_seconds: int


class RateLimitService:
    """Increment Redis counters in fixed windows and enforce per-bucket limits."""

    def __init__(
        self,
        settings: Settings,
        redis: Redis | None = None,
    ) -> None:
        self._settings = settings
        self._redis = redis

    def _client(self) -> Redis:
        return self._redis if self._redis is not None else get_redis()

    async def check(
        self,
        *,
        bucket: str,
        identity: str,
        limit: int,
    ) -> RateLimitDecision:
        """
        Record one hit for ``identity`` in ``bucket`` and return whether allowed.

        Uses a fixed window of ``rate_limit_window_seconds``. First hit sets TTL.
        """
        window = self._settings.rate_limit_window_seconds
        window_id = int(time.time()) // window
        key = f"{RATE_LIMIT_KEY_PREFIX}{bucket}:{identity}:{window_id}"
        redis = self._client()

        count = int(await redis.incr(key))
        if count == 1:
            await redis.expire(key, window)

        ttl = await redis.ttl(key)
        retry_after = ttl if ttl and ttl > 0 else window
        remaining = max(limit - count, 0)
        return RateLimitDecision(
            allowed=count <= limit,
            limit=limit,
            remaining=remaining,
            retry_after_seconds=retry_after,
        )
