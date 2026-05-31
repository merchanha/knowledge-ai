"""Health check controller."""

from fastapi import APIRouter

from knowledge_ai.core.config import settings
from knowledge_ai.schemas.health import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Return application health status."""
    return HealthResponse(status="ok", version=settings.app_version)
