"""Integration tests for DirectoryService and ProjectService tree hooks."""

from collections.abc import AsyncIterator
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from knowledge_ai.core.config import settings
from knowledge_ai.models.directory import ROOT_DIRECTORY_NAME
from knowledge_ai.services.directory import (
    DirectoryConflictError,
    DirectoryNotFoundError,
    DirectoryService,
    DirectoryValidationError,
)
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


async def _create_project(session: AsyncSession, name: str = "Test Project") -> tuple[UUID, UUID]:
    project = await ProjectService(session).create(name=name, description="desc")
    root = await DirectoryService(session).get_root_for_project(project.id)
    assert root is not None
    return project.id, root.id


@pytest.mark.asyncio
async def test_project_create_auto_creates_root(db_session: AsyncSession) -> None:
    project_id, root_id = await _create_project(db_session)

    root = await DirectoryService(db_session).require_by_id(root_id)
    assert root.project_id == project_id
    assert root.parent_id is None
    assert root.name == ROOT_DIRECTORY_NAME
    assert root.is_root is True


@pytest.mark.asyncio
async def test_create_rename_move_delete_directory_tree(db_session: AsyncSession) -> None:
    _, root_id = await _create_project(db_session)
    directory_service = DirectoryService(db_session)

    docs = await directory_service.create(
        project_id=(await directory_service.require_by_id(root_id)).project_id,
        parent_id=root_id,
        name="Docs",
    )
    api = await directory_service.create(
        project_id=docs.project_id,
        parent_id=root_id,
        name="API",
    )

    renamed = await directory_service.rename(docs.id, name="Documentation")
    assert renamed.name == "Documentation"

    moved = await directory_service.move(api.id, new_parent_id=docs.id)
    assert moved.parent_id == docs.id

    children = await directory_service.list_children(root_id)
    assert {child.id for child in children} == {docs.id}

    breadcrumb = await directory_service.get_breadcrumb_chain(api.id)
    assert [node.name for node in breadcrumb] == [ROOT_DIRECTORY_NAME, "Documentation", "API"]

    await directory_service.delete(docs.id)
    assert await directory_service.get_by_id(api.id) is None


@pytest.mark.asyncio
async def test_create_rejects_duplicate_sibling_name(db_session: AsyncSession) -> None:
    project_id, root_id = await _create_project(db_session)
    directory_service = DirectoryService(db_session)

    await directory_service.create(project_id=project_id, parent_id=root_id, name="Docs")
    with pytest.raises(DirectoryConflictError):
        await directory_service.create(project_id=project_id, parent_id=root_id, name="Docs")


@pytest.mark.asyncio
async def test_move_rejects_cycle_and_root(db_session: AsyncSession) -> None:
    project_id, root_id = await _create_project(db_session)
    directory_service = DirectoryService(db_session)

    parent = await directory_service.create(
        project_id=project_id,
        parent_id=root_id,
        name="Parent",
    )
    child = await directory_service.create(
        project_id=project_id,
        parent_id=parent.id,
        name="Child",
    )

    with pytest.raises(DirectoryValidationError, match="descendant"):
        await directory_service.move(parent.id, new_parent_id=child.id)

    with pytest.raises(DirectoryValidationError, match="root"):
        await directory_service.move(root_id, new_parent_id=parent.id)


@pytest.mark.asyncio
async def test_delete_rejects_root(db_session: AsyncSession) -> None:
    _, root_id = await _create_project(db_session)

    with pytest.raises(DirectoryValidationError, match="root"):
        await DirectoryService(db_session).delete(root_id)


@pytest.mark.asyncio
async def test_require_by_id_raises_when_missing(db_session: AsyncSession) -> None:
    with pytest.raises(DirectoryNotFoundError):
        await DirectoryService(db_session).require_by_id(uuid4())
