"""Pydantic models for project membership operations."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from knowledge_ai.models.project_membership import ProjectMembershipRole


class MembershipRead(BaseModel):
    """Project membership row returned from service/API layers."""

    id: UUID
    user_id: UUID
    project_id: UUID
    role: ProjectMembershipRole
    is_context_exposed: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class MembershipCreate(BaseModel):
    """Add a user to a project."""

    user_id: UUID
    role: ProjectMembershipRole = ProjectMembershipRole.MEMBER
