"""Integration tests for CommandService."""

from collections.abc import AsyncIterator
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from knowledge_ai.core.config import settings
from knowledge_ai.services.command import (
    CommandNotFoundError,
    CommandService,
    CommandValidationError,
)
from knowledge_ai.services.directory import DirectoryService
from knowledge_ai.services.project import ProjectService


@pytest.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    """Postgres session in a transaction that always rolls back."""
    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    connection = await engine.connect()
    transaction = await connection.begin()
    session = AsyncSession(bind=connection, expire_on_commit=False)

    try:
        yield session
    finally:
        await session.close()
        await transaction.rollback()
        await connection.close()
        await engine.dispose()


async def _create_project_with_directory(
    session: AsyncSession,
) -> tuple[UUID, UUID]:
    project = await ProjectService(session).create(name="Command Project", description="desc")
    root = await DirectoryService(session).get_root_for_project(project.id)
    assert root is not None
    scripts = await DirectoryService(session).create(
        project_id=project.id,
        parent_id=root.id,
        name="Scripts",
    )
    return scripts.id, root.id


@pytest.mark.asyncio
async def test_create_list_update_delete_command(db_session: AsyncSession) -> None:
    scripts_id, _root_id = await _create_project_with_directory(db_session)
    command_service = CommandService(db_session)

    created = await command_service.create(
        directory_id=scripts_id,
        title="Run Tests",
        content="uv run pytest",
        metadata={"tags": ["ci"]},
    )
    assert created.title == "Run Tests"
    assert created.metadata_json == {"tags": ["ci"]}

    listed = await command_service.list_by_directory(scripts_id)
    assert len(listed) == 1
    assert listed[0].id == created.id

    updated = await command_service.update(
        created.id,
        title="Run Full Suite",
        content="uv run pytest --cov",
    )
    assert updated.title == "Run Full Suite"

    await command_service.delete(created.id)
    assert await command_service.get_by_id(created.id) is None


@pytest.mark.asyncio
async def test_create_rejects_empty_title_or_content(db_session: AsyncSession) -> None:
    scripts_id, _root_id = await _create_project_with_directory(db_session)
    command_service = CommandService(db_session)

    with pytest.raises(CommandValidationError, match="Title"):
        await command_service.create(
            directory_id=scripts_id,
            title="   ",
            content="Valid content",
        )

    with pytest.raises(CommandValidationError, match="Content"):
        await command_service.create(
            directory_id=scripts_id,
            title="Valid title",
            content="   ",
        )


@pytest.mark.asyncio
async def test_require_by_id_raises_when_missing(db_session: AsyncSession) -> None:
    with pytest.raises(CommandNotFoundError):
        await CommandService(db_session).require_by_id(uuid4())
