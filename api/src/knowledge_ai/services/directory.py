"""Directory tree business logic — create, rename, move, delete."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from knowledge_ai.models.directory import ROOT_DIRECTORY_NAME, Directory
from knowledge_ai.models.project import Project


class DirectoryError(Exception):
    """Base error for directory domain operations."""


class DirectoryNotFoundError(DirectoryError):
    """Raised when a directory id does not exist."""


class DirectoryConflictError(DirectoryError):
    """Raised when a sibling name already exists."""


class DirectoryValidationError(DirectoryError):
    """Raised when an operation violates tree rules (root, cycles, scope)."""


class DirectoryService:
    """CRUD and tree operations for project-scoped directory hierarchies."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, directory_id: UUID) -> Directory | None:
        """Load a directory by primary key."""
        return await self._session.get(Directory, directory_id)

    async def require_by_id(self, directory_id: UUID) -> Directory:
        """Load a directory or raise ``DirectoryNotFoundError``."""
        directory = await self.get_by_id(directory_id)
        if directory is None:
            raise DirectoryNotFoundError(f"Directory {directory_id} not found")
        return directory

    async def get_root_for_project(self, project_id: UUID) -> Directory | None:
        """Return the root directory for a project, if one exists."""
        result = await self._session.execute(
            select(Directory).where(
                Directory.project_id == project_id,
                Directory.parent_id.is_(None),
            ),
        )
        return result.scalar_one_or_none()

    async def list_children(self, directory_id: UUID) -> list[Directory]:
        """Return immediate child directories ordered by name."""
        result = await self._session.execute(
            select(Directory)
            .where(Directory.parent_id == directory_id)
            .order_by(Directory.name),
        )
        return list(result.scalars().all())

    async def list_by_project(self, project_id: UUID) -> list[Directory]:
        """Return all directories in a project ordered by name."""
        result = await self._session.execute(
            select(Directory)
            .where(Directory.project_id == project_id)
            .order_by(Directory.name),
        )
        return list(result.scalars().all())

    async def get_breadcrumb_chain(self, directory_id: UUID) -> list[Directory]:
        """Return ancestors from root to the target directory (inclusive)."""
        chain: list[Directory] = []
        current = await self.require_by_id(directory_id)
        while current is not None:
            chain.append(current)
            if current.parent_id is None:
                break
            current = await self.require_by_id(current.parent_id)
        chain.reverse()
        return chain

    async def create_root_for_project(self, project: Project) -> Directory:
        """Create the single root directory for a new project."""
        existing = await self.get_root_for_project(project.id)
        if existing is not None:
            raise DirectoryConflictError(
                f"Project {project.id} already has root directory {existing.id}",
            )

        directory = Directory(
            project_id=project.id,
            parent_id=None,
            name=ROOT_DIRECTORY_NAME,
        )
        self._session.add(directory)
        await self._session.flush()
        return directory

    async def create(
        self,
        *,
        project_id: UUID,
        parent_id: UUID,
        name: str,
    ) -> Directory:
        """Create a child directory under ``parent_id`` in ``project_id``."""
        normalized = name.strip()
        if not normalized:
            raise DirectoryValidationError("Directory name cannot be empty")

        parent = await self.require_by_id(parent_id)
        if parent.project_id != project_id:
            raise DirectoryValidationError("Parent directory belongs to a different project")

        await self._ensure_unique_sibling_name(
            project_id=project_id,
            parent_id=parent_id,
            name=normalized,
        )

        directory = Directory(
            project_id=project_id,
            parent_id=parent_id,
            name=normalized,
        )
        self._session.add(directory)
        await self._session.flush()
        return directory

    async def rename(self, directory_id: UUID, *, name: str) -> Directory:
        """Rename a directory; sibling names must remain unique."""
        normalized = name.strip()
        if not normalized:
            raise DirectoryValidationError("Directory name cannot be empty")

        directory = await self.require_by_id(directory_id)
        if directory.name == normalized:
            return directory

        await self._ensure_unique_sibling_name(
            project_id=directory.project_id,
            parent_id=directory.parent_id,
            name=normalized,
            exclude_id=directory.id,
        )
        directory.name = normalized
        await self._session.flush()
        return directory

    async def move(self, directory_id: UUID, *, new_parent_id: UUID) -> Directory:
        """Move a directory under ``new_parent_id`` within the same project."""
        directory = await self.require_by_id(directory_id)
        if directory.is_root:
            raise DirectoryValidationError("The project root directory cannot be moved")

        if directory_id == new_parent_id:
            raise DirectoryValidationError("A directory cannot be moved under itself")

        new_parent = await self.require_by_id(new_parent_id)
        if new_parent.project_id != directory.project_id:
            raise DirectoryValidationError("Target parent belongs to a different project")

        if directory.parent_id == new_parent_id:
            return directory

        descendants = await self._collect_descendant_ids(directory_id)
        if new_parent_id in descendants:
            raise DirectoryValidationError("Cannot move a directory under its own descendant")

        await self._ensure_unique_sibling_name(
            project_id=directory.project_id,
            parent_id=new_parent_id,
            name=directory.name,
            exclude_id=directory.id,
        )

        directory.parent_id = new_parent_id
        await self._session.flush()
        return directory

    async def delete(self, directory_id: UUID) -> None:
        """Delete a directory and all descendants (DB cascade on parent_id)."""
        directory = await self.require_by_id(directory_id)
        if directory.is_root:
            raise DirectoryValidationError("The project root directory cannot be deleted")
        await self._session.delete(directory)
        await self._session.flush()

    async def _ensure_unique_sibling_name(
        self,
        *,
        project_id: UUID,
        parent_id: UUID | None,
        name: str,
        exclude_id: UUID | None = None,
    ) -> None:
        query = select(Directory.id).where(
            Directory.project_id == project_id,
            Directory.name == name,
        )
        if parent_id is None:
            query = query.where(Directory.parent_id.is_(None))
        else:
            query = query.where(Directory.parent_id == parent_id)
        if exclude_id is not None:
            query = query.where(Directory.id != exclude_id)

        result = await self._session.execute(query)
        if result.scalar_one_or_none() is not None:
            raise DirectoryConflictError(
                f"Directory name '{name}' already exists under this parent",
            )

    async def _collect_descendant_ids(self, directory_id: UUID) -> set[UUID]:
        """Return all descendant directory IDs (breadth-first)."""
        descendants: set[UUID] = set()
        queue: list[UUID] = [directory_id]
        while queue:
            current_id = queue.pop()
            result = await self._session.execute(
                select(Directory.id).where(Directory.parent_id == current_id),
            )
            for child_id in result.scalars().all():
                if child_id not in descendants:
                    descendants.add(child_id)
                    queue.append(child_id)
        return descendants
