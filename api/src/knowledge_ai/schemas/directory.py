"""Pydantic models for directory domain operations."""

from uuid import UUID

from pydantic import BaseModel, Field


class DirectoryRead(BaseModel):
    """Directory row returned from service/API layers."""

    id: UUID
    project_id: UUID
    parent_id: UUID | None
    name: str
    is_root: bool = False

    model_config = {"from_attributes": True}


class DirectoryCreate(BaseModel):
    """Create a child directory under an existing parent."""

    name: str = Field(min_length=1, max_length=255)


class DirectoryRename(BaseModel):
    """Rename a directory in place."""

    name: str = Field(min_length=1, max_length=255)


class DirectoryMove(BaseModel):
    """Move a directory to a new parent within the same project."""

    new_parent_id: UUID
