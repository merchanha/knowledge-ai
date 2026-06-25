"""Pydantic models for KnowledgeNeuron domain operations."""

from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field


class KnowledgeNeuronRead(BaseModel):
    """KnowledgeNeuron row returned from service/API layers."""

    id: UUID
    directory_id: UUID
    title: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    has_embedding: bool = False

    model_config = {"from_attributes": True}


class KnowledgeNeuronCreate(BaseModel):
    """Create a KnowledgeNeuron inside a directory."""

    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    metadata: dict[str, Any] = Field(default_factory=dict)


class KnowledgeNeuronUpdate(BaseModel):
    """Partial update for a KnowledgeNeuron."""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    content: str | None = Field(default=None, min_length=1)
    metadata: dict[str, Any] | None = None


class KnowledgeNeuronSearchResult(BaseModel):
    """KnowledgeNeuron matched by semantic search with similarity score."""

    id: UUID
    directory_id: UUID
    title: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)
    similarity: float

    model_config = {"from_attributes": True}
