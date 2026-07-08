"""Project persistence and lifecycle hooks."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from knowledge_ai.models.project import Project
from knowledge_ai.services.directory import DirectoryService


class ProjectError(Exception):
    """Base error for project domain operations."""


class ProjectNotFoundError(ProjectError):
    """Raised when a project id does not exist."""


class ProjectValidationError(ProjectError):
    """Raised when input violates domain rules."""


class ProjectService:
    """Project CRUD, archive lifecycle, and root-directory hook on create."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, project_id: UUID) -> Project | None:
        """Load a project by primary key."""
        return await self._session.get(Project, project_id)

    async def require_by_id(self, project_id: UUID) -> Project:
        """Load a project or raise ``ProjectNotFoundError``."""
        project = await self.get_by_id(project_id)
        if project is None:
            raise ProjectNotFoundError(f"Project {project_id} not found")
        return project

    async def create(
        self,
        *,
        name: str,
        description: str | None = None,
    ) -> Project:
        """Create a project and its root directory tree node."""
        normalized_name = name.strip()
        if not normalized_name:
            raise ProjectValidationError("Project name cannot be empty")

        project = Project(name=normalized_name, description=description)
        self._session.add(project)
        await self._session.flush()

        await DirectoryService(self._session).create_root_for_project(project)
        return project

    async def list_all(self) -> list[Project]:
        """Return all projects ordered by name."""
        result = await self._session.execute(select(Project).order_by(Project.name))
        return list(result.scalars().all())

    async def update(
        self,
        project_id: UUID,
        *,
        name: str | None = None,
        description: str | None = None,
    ) -> Project:
        """Update mutable fields on a project."""
        project = await self.require_by_id(project_id)

        if name is not None:
            normalized_name = name.strip()
            if not normalized_name:
                raise ProjectValidationError("Project name cannot be empty")
            project.name = normalized_name

        if description is not None:
            project.description = description

        await self._session.flush()
        return project

    async def archive(self, project_id: UUID) -> Project:
        """Mark a project as archived."""
        project = await self.require_by_id(project_id)
        project.is_archived = True
        await self._session.flush()
        return project

    async def unarchive(self, project_id: UUID) -> Project:
        """Clear the archived flag on a project."""
        project = await self.require_by_id(project_id)
        project.is_archived = False
        await self._session.flush()
        return project

    async def delete(self, project_id: UUID) -> None:
        """Delete a project and cascade to directories, neurons, and commands."""
        project = await self.require_by_id(project_id)
        await self._session.delete(project)
        await self._session.flush()
