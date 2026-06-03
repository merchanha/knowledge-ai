"""Shared pytest fixtures."""

from collections.abc import AsyncIterator, Iterator
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from knowledge_ai.main import app


@pytest.fixture
async def client() -> AsyncIterator[AsyncClient]:
    """HTTP client for API integration tests."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as http_client:
        yield http_client


@pytest.fixture
def mock_db_healthy() -> Iterator[AsyncMock]:
    """Patch database health check to return healthy."""
    with patch(
        "knowledge_ai.api.v1.health.check_database_connection",
        new_callable=AsyncMock,
        return_value=True,
    ) as mock:
        yield mock


@pytest.fixture
def mock_redis_healthy() -> Iterator[AsyncMock]:
    """Patch Redis health check to return healthy."""
    with patch(
        "knowledge_ai.api.v1.health.check_redis_connection",
        new_callable=AsyncMock,
        return_value=True,
    ) as mock:
        yield mock
