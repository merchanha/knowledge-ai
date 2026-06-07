"""Pydantic models for directory permission endpoints."""

import uuid
from enum import StrEnum

from pydantic import BaseModel, Field


class DirectoryPermission(StrEnum):
    """Fine-grained access on a directory resource."""

    READ = "READ"
    WRITE = "WRITE"
    MANAGE = "MANAGE"


class GrantDirectoryPermissionRequest(BaseModel):
    """Admin grant of directory access to a user."""

    user_id: uuid.UUID
    permission: DirectoryPermission


class RevokeDirectoryPermissionRequest(BaseModel):
    """Admin revocation of directory access from a user."""

    user_id: uuid.UUID
    permission: DirectoryPermission


class DirectoryPermissionEntry(BaseModel):
    """One Casbin policy row exposed to the API."""

    directory_id: uuid.UUID
    permission: DirectoryPermission


class UserDirectoryPermissionsResponse(BaseModel):
    """Directory permissions for the authenticated user."""

    permissions: list[DirectoryPermissionEntry] = Field(default_factory=list)
