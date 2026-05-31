"""Health check response schema."""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """Response payload for the health check endpoint."""

    status: str
    version: str
