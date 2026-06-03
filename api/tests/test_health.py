"""Tests for health check endpoints."""

from unittest.mock import AsyncMock, patch

from httpx import ASGITransport, AsyncClient

from knowledge_ai.main import app


async def test_health_check_returns_ok() -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["version"] == "0.1.0"


async def test_readiness_returns_ok_when_dependencies_healthy(
    mock_db_healthy: AsyncMock,
    mock_redis_healthy: AsyncMock,
) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/health/ready")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert len(payload["dependencies"]) == 2
    mock_db_healthy.assert_awaited_once()
    mock_redis_healthy.assert_awaited_once()


async def test_readiness_returns_503_when_database_unavailable() -> None:
    with (
        patch(
            "knowledge_ai.api.v1.health.check_database_connection",
            new_callable=AsyncMock,
            return_value=False,
        ),
        patch(
            "knowledge_ai.api.v1.health.check_redis_connection",
            new_callable=AsyncMock,
            return_value=True,
        ),
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.get("/api/v1/health/ready")

    assert response.status_code == 503
    payload = response.json()
    assert payload["status"] == "degraded"
    assert payload["dependencies"][0]["name"] == "database"
    assert payload["dependencies"][0]["status"] == "unavailable"
