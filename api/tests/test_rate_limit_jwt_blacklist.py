"""Unit tests for RateLimitService and JWT blacklist using fakeredis."""

from __future__ import annotations

from collections.abc import AsyncIterator
from uuid import uuid4

import pytest
from fakeredis.aioredis import FakeRedis
from jwt.exceptions import InvalidTokenError

from knowledge_ai.core.config import Settings
from knowledge_ai.services.jwt import JWTService
from knowledge_ai.services.rate_limit import RateLimitService


@pytest.fixture
async def fake_redis() -> AsyncIterator[FakeRedis]:
    client = FakeRedis(decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()


@pytest.fixture
def settings() -> Settings:
    return Settings(
        jwt_secret_key="test-secret-key-at-least-32-chars-long",
        jwt_access_token_expire_minutes=15,
        rate_limit_window_seconds=60,
        rate_limit_search_per_window=3,
        rate_limit_auth_per_window=2,
    )


@pytest.mark.asyncio
async def test_rate_limit_allows_under_limit(
    settings: Settings,
    fake_redis: FakeRedis,
) -> None:
    service = RateLimitService(settings, redis=fake_redis)
    first = await service.check(bucket="search", identity="user:1", limit=3)
    second = await service.check(bucket="search", identity="user:1", limit=3)

    assert first.allowed is True
    assert first.remaining == 2
    assert second.allowed is True
    assert second.remaining == 1


@pytest.mark.asyncio
async def test_rate_limit_blocks_over_limit(
    settings: Settings,
    fake_redis: FakeRedis,
) -> None:
    service = RateLimitService(settings, redis=fake_redis)
    for _ in range(3):
        decision = await service.check(bucket="auth", identity="ip:127.0.0.1", limit=3)
        assert decision.allowed is True

    blocked = await service.check(bucket="auth", identity="ip:127.0.0.1", limit=3)
    assert blocked.allowed is False
    assert blocked.remaining == 0
    assert blocked.retry_after_seconds > 0


@pytest.mark.asyncio
async def test_rate_limit_buckets_are_independent(
    settings: Settings,
    fake_redis: FakeRedis,
) -> None:
    service = RateLimitService(settings, redis=fake_redis)
    await service.check(bucket="search", identity="user:1", limit=1)
    blocked = await service.check(bucket="search", identity="user:1", limit=1)
    other = await service.check(bucket="auth", identity="user:1", limit=1)

    assert blocked.allowed is False
    assert other.allowed is True


@pytest.mark.asyncio
async def test_jwt_blacklist_rejects_revoked_token(
    settings: Settings,
    fake_redis: FakeRedis,
) -> None:
    jwt_service = JWTService(settings, redis=fake_redis)
    user_id = uuid4()
    token, _ = jwt_service.create_access_token(
        user_id=user_id,
        email="user@example.com",
        role="user",
    )
    claims = jwt_service.verify_access_token(token)
    assert await jwt_service.is_access_token_revoked(claims.jti) is False

    assert await jwt_service.revoke_access_token(token) is True
    assert await jwt_service.is_access_token_revoked(claims.jti) is True


@pytest.mark.asyncio
async def test_access_token_requires_jti(settings: Settings) -> None:
    jwt_service = JWTService(settings)
    token, _ = jwt_service.create_access_token(
        user_id=uuid4(),
        email="user@example.com",
        role="user",
    )
    claims = jwt_service.verify_access_token(token)
    assert claims.jti


@pytest.mark.asyncio
async def test_revoke_invalid_token_is_noop(
    settings: Settings,
    fake_redis: FakeRedis,
) -> None:
    jwt_service = JWTService(settings, redis=fake_redis)
    assert await jwt_service.revoke_access_token("not-a-jwt") is False


@pytest.mark.asyncio
async def test_verify_rejects_wrong_type_after_jti_change(
    settings: Settings,
    fake_redis: FakeRedis,
) -> None:
    jwt_service = JWTService(settings, redis=fake_redis)
    refresh = jwt_service.create_refresh_token(user_id=uuid4())
    with pytest.raises(InvalidTokenError):
        jwt_service.verify_access_token(refresh)
