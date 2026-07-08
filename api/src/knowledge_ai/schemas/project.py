"""Pydantic models for Project domain operations."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class ProjectRead(BaseModel):
    """Project row returned from service/API layers."""

    id: UUID
    name: str
    description: str | None
    is_archived: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProjectCreate(BaseModel):
    """Create a new project (admin)."""

    name: str = Field(min_length=1, max_length=255)
    description: str | None = None


class ProjectUpdate(BaseModel):
    """Partial update for a project."""

    name: str | None = Field(default=None, min_length=1, max_length=255)
    description: str | None = None
