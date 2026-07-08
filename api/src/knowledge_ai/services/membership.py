"""Project membership — add/remove members, roles, and MCP exposure flags."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from knowledge_ai.models.project import Project
from knowledge_ai.models.project_membership import ProjectMembership, ProjectMembershipRole
from knowledge_ai.schemas.permissions import DirectoryPermission
from knowledge_ai.services.casbin_permission import CasbinPermissionService
from knowledge_ai.services.directory import DirectoryService
from knowledge_ai.services.project import ProjectService
from knowledge_ai.services.user import UserService


class MembershipError(Exception):
    """Base error for membership domain operations."""


class MembershipNotFoundError(MembershipError):
    """Raised when a user is not a member of the project."""


class MembershipConflictError(MembershipError):
    """Raised when a membership already exists."""


class MembershipValidationError(MembershipError):
    """Raised when membership input violates domain rules."""


@dataclass(frozen=True)
class AccountProject:
    """Project row enriched with the caller's membership details."""

    project: Project
    membership: ProjectMembership


class MembershipService:
    """Manage project members, roles, and per-user MCP exposure."""

    def __init__(
        self,
        session: AsyncSession,
        perm_service: CasbinPermissionService,
    ) -> None:
        self._session = session
        self._perm_service = perm_service
        self._projects = ProjectService(session)
        self._directories = DirectoryService(session)
        self._users = UserService(session)

    async def get_membership(
        self,
        *,
        user_id: UUID,
        project_id: UUID,
    ) -> ProjectMembership | None:
        """Return membership for ``user_id`` on ``project_id``, if any."""
        result = await self._session.execute(
            select(ProjectMembership).where(
                ProjectMembership.user_id == user_id,
                ProjectMembership.project_id == project_id,
            ),
        )
        return result.scalar_one_or_none()

    async def require_membership(
        self,
        *,
        user_id: UUID,
        project_id: UUID,
    ) -> ProjectMembership:
        """Load membership or raise ``MembershipNotFoundError``."""
        membership = await self.get_membership(user_id=user_id, project_id=project_id)
        if membership is None:
            raise MembershipNotFoundError(
                f"User {user_id} is not a member of project {project_id}",
            )
        return membership

    async def is_owner(self, *, user_id: UUID, project_id: UUID) -> bool:
        """Return True when the user has the owner role on the project."""
        membership = await self.get_membership(user_id=user_id, project_id=project_id)
        return membership is not None and membership.role == ProjectMembershipRole.OWNER

    async def list_members(self, project_id: UUID) -> list[ProjectMembership]:
        """Return all memberships for a project ordered by creation time."""
        await self._projects.require_by_id(project_id)
        result = await self._session.execute(
            select(ProjectMembership)
            .where(ProjectMembership.project_id == project_id)
            .order_by(ProjectMembership.created_at),
        )
        return list(result.scalars().all())

    async def list_projects_for_user(self, user_id: UUID) -> list[AccountProject]:
        """Return projects the user belongs to with membership metadata."""
        result = await self._session.execute(
            select(ProjectMembership)
            .where(ProjectMembership.user_id == user_id)
            .options(selectinload(ProjectMembership.project))
            .order_by(ProjectMembership.created_at),
        )
        memberships = list(result.scalars().all())
        return [
            AccountProject(project=membership.project, membership=membership)
            for membership in memberships
        ]

    async def add_member(
        self,
        *,
        project_id: UUID,
        user_id: UUID,
        role: ProjectMembershipRole = ProjectMembershipRole.MEMBER,
    ) -> ProjectMembership:
        """Add a user to a project and grant MANAGE on the project root directory."""
        await self._projects.require_by_id(project_id)
        user = await self._users.get_by_id(user_id)
        if user is None:
            raise MembershipValidationError(f"User {user_id} not found")

        existing = await self.get_membership(user_id=user_id, project_id=project_id)
        if existing is not None:
            raise MembershipConflictError(
                f"User {user_id} is already a member of project {project_id}",
            )

        membership = ProjectMembership(
            user_id=user_id,
            project_id=project_id,
            role=role,
        )
        self._session.add(membership)
        await self._session.flush()

        root = await self._directories.get_root_for_project(project_id)
        if root is not None:
            await self._perm_service.grant_directory_permission(
                user_id=user_id,
                directory_id=root.id,
                permission=DirectoryPermission.MANAGE,
            )

        return membership

    async def remove_member(self, *, project_id: UUID, user_id: UUID) -> None:
        """Remove a user from a project and revoke MANAGE on the project root."""
        membership = await self.require_membership(user_id=user_id, project_id=project_id)

        root = await self._directories.get_root_for_project(project_id)
        if root is not None:
            await self._perm_service.revoke_directory_permission(
                user_id=user_id,
                directory_id=root.id,
                permission=DirectoryPermission.MANAGE,
            )

        await self._session.delete(membership)
        await self._session.flush()

    async def set_context_exposed(
        self,
        *,
        user_id: UUID,
        project_id: UUID,
        is_context_exposed: bool,
    ) -> ProjectMembership:
        """Toggle whether the user's MCP agents may read this project's tree."""
        membership = await self.require_membership(user_id=user_id, project_id=project_id)
        membership.is_context_exposed = is_context_exposed
        await self._session.flush()
        await self._session.refresh(membership)
        return membership
