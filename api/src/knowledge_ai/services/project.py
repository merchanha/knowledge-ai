"""Project persistence and lifecycle hooks."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from knowledge_ai.models.project import Project
from knowledge_ai.services.directory import DirectoryService


class ProjectService:
    """Project CRUD; full admin API ships in Week 11."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, project_id: UUID) -> Project | None:
        """Load a project by primary key."""
        return await self._session.get(Project, project_id)

    async def create(
        self,
        *,
        name: str,
        description: str | None = None,
    ) -> Project:
        """Create a project and its root directory tree node."""
        project = Project(name=name, description=description)
        self._session.add(project)
        await self._session.flush()

        await DirectoryService(self._session).create_root_for_project(project)
        return project

    async def list_all(self) -> list[Project]:
        """Return all projects ordered by name."""
        result = await self._session.execute(select(Project).order_by(Project.name))
        return list(result.scalars().all())
