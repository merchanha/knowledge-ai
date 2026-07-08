"""Pydantic models for Command domain operations."""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class CommandRead(BaseModel):
    """Command row returned from service/API layers."""

    id: UUID
    directory_id: UUID
    title: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)

    model_config = {"from_attributes": True}


class CommandCreate(BaseModel):
    """Create a Command inside a directory."""

    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class CommandUpdate(BaseModel):
    """Partial update for a Command."""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    content: str | None = Field(default=None, min_length=1)
    metadata: dict[str, Any] | None = None
