"""Health check controllers."""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from knowledge_ai.core.config import settings
from knowledge_ai.core.database import check_database_connection
from knowledge_ai.core.redis import check_redis_connection
from knowledge_ai.schemas.health import (
    DependencyStatus,
    HealthResponse,
    ReadinessResponse,
)

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Liveness probe — confirms the API process is running."""
    return HealthResponse(status="ok", version=settings.app_version)


@router.get("/health/ready", response_model=ReadinessResponse)
async def readiness_check() -> JSONResponse | ReadinessResponse:
    """Readiness probe — confirms database and Redis are reachable."""
    db_ok = await check_database_connection()
    redis_ok = await check_redis_connection()

    dependencies = [
        DependencyStatus(name="database", status="ok" if db_ok else "unavailable"),
        DependencyStatus(name="redis", status="ok" if redis_ok else "unavailable"),
    ]
    all_ok = db_ok and redis_ok
    body = ReadinessResponse(
        status="ok" if all_ok else "degraded",
        dependencies=dependencies,
    )

    if not all_ok:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content=body.model_dump(),
        )
    return body
