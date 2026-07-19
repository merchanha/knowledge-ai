"""Command business logic — CRUD scoped to directory folders."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from knowledge_ai.models.command import Command
from knowledge_ai.services.directory import DirectoryService


class CommandError(Exception):
    """Base error for Command domain operations."""


class CommandNotFoundError(CommandError):
    """Raised when a Command id does not exist."""


class CommandValidationError(CommandError):
    """Raised when input violates domain rules."""


class CommandService:
    """CRUD operations for Commands stored in directory folders."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._directories = DirectoryService(session)

    async def get_by_id(self, command_id: UUID) -> Command | None:
        """Load a Command by primary key."""
        return await self._session.get(Command, command_id)

    async def require_by_id(self, command_id: UUID) -> Command:
        """Load a Command or raise ``CommandNotFoundError``."""
        command = await self.get_by_id(command_id)
        if command is None:
            raise CommandNotFoundError(f"Command {command_id} not found")
        return command

    async def list_by_directory(self, directory_id: UUID) -> list[Command]:
        """Return Commands in a directory ordered by title."""
        await self._directories.require_by_id(directory_id)
        result = await self._session.execute(
            select(Command)
            .where(Command.directory_id == directory_id)
            .order_by(Command.title),
        )
        return list(result.scalars().all())

    async def list_in_directories(self, directory_ids: list[UUID] | None) -> list[Command]:
        """Return Commands scoped to readable directories (``None`` = all)."""
        if directory_ids is not None and not directory_ids:
            return []
        query = select(Command).order_by(Command.title)
        if directory_ids is not None:
            query = query.where(Command.directory_id.in_(directory_ids))
        result = await self._session.execute(query)
        return list(result.scalars().all())

    async def list_by_project(self, project_id: UUID) -> list[Command]:
        """Return all Commands in a project's directory tree."""
        directories = await self._directories.list_by_project(project_id)
        directory_ids = [directory.id for directory in directories]
        return await self.list_in_directories(directory_ids)

    async def create(
        self,
        *,
        directory_id: UUID,
        title: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> Command:
        """Create a Command inside ``directory_id``."""
        normalized_title = title.strip()
        normalized_content = content.strip()
        if not normalized_title:
            raise CommandValidationError("Title cannot be empty")
        if not normalized_content:
            raise CommandValidationError("Content cannot be empty")

        await self._directories.require_by_id(directory_id)

        command = Command(
            directory_id=directory_id,
            title=normalized_title,
            content=normalized_content,
            metadata_json=metadata or {},
        )
        self._session.add(command)
        await self._session.flush()
        return command

    async def update(
        self,
        command_id: UUID,
        *,
        title: str | None = None,
        content: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> Command:
        """Update fields on an existing Command."""
        command = await self.require_by_id(command_id)

        if title is not None:
            normalized_title = title.strip()
            if not normalized_title:
                raise CommandValidationError("Title cannot be empty")
            command.title = normalized_title

        if content is not None:
            normalized_content = content.strip()
            if not normalized_content:
                raise CommandValidationError("Content cannot be empty")
            command.content = normalized_content

        if metadata is not None:
            command.metadata_json = metadata

        await self._session.flush()
        return command

    async def delete(self, command_id: UUID) -> None:
        """Delete a Command."""
        command = await self.require_by_id(command_id)
        await self._session.delete(command)
        await self._session.flush()
