"""Async Redis client (used by Celery, cache, and rate limiting in later weeks)."""

from redis.asyncio import Redis

from knowledge_ai.core.config import settings

_redis: Redis | None = None


def get_redis() -> Redis:
    """Return the shared async Redis client, creating it on first use."""
    global _redis
    if _redis is None:
        _redis = Redis.from_url(
            settings.redis_url,
            decode_responses=True,
        )
    return _redis


async def check_redis_connection() -> bool:
    """Return True if Redis responds to PING."""
    try:
        redis = get_redis()
        return bool(await redis.ping())
    except Exception:
        return False


async def close_redis() -> None:
    """Close the Redis connection pool."""
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None
