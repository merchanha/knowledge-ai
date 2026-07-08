"""Pydantic models for the authenticated user's account view."""

from uuid import UUID

from pydantic import BaseModel

from knowledge_ai.models.project_membership import ProjectMembershipRole


class AccountProjectRead(BaseModel):
    """Project visible on the account page with membership metadata."""

    id: UUID
    name: str
    description: str | None
    is_archived: bool
    membership_role: ProjectMembershipRole
    is_context_exposed: bool


class AccountProjectExposureUpdate(BaseModel):
    """Toggle MCP StratumContext exposure for one project."""

    is_context_exposed: bool
