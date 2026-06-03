"""Health check response schemas."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Response payload for the liveness health check endpoint."""

    status: str
    version: str


class DependencyStatus(BaseModel):
    """Status of a single infrastructure dependency."""

    name: str
    status: str


class ReadinessResponse(BaseModel):
    """Response payload for the readiness check (DB + Redis)."""

    status: str
    dependencies: list[DependencyStatus]
