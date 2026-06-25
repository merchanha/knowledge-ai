"""Integration tests for KnowledgeNeuronService."""

from collections.abc import AsyncIterator
from uuid import UUID, uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from knowledge_ai.core.config import settings
from knowledge_ai.services.directory import DirectoryService
from knowledge_ai.services.knowledge_neuron import (
    KnowledgeNeuronNotFoundError,
    KnowledgeNeuronService,
    KnowledgeNeuronValidationError,
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


async def _create_project_with_directory(
    session: AsyncSession,
) -> tuple[UUID, UUID]:
    project = await ProjectService(session).create(name="Neuron Project", description="desc")
    root = await DirectoryService(session).get_root_for_project(project.id)
    assert root is not None
    docs = await DirectoryService(session).create(
        project_id=project.id,
        parent_id=root.id,
        name="Docs",
    )
    return docs.id, root.id


@pytest.mark.asyncio
async def test_create_list_update_delete_knowledge_neuron(db_session: AsyncSession) -> None:
    docs_id, _root_id = await _create_project_with_directory(db_session)
    neuron_service = KnowledgeNeuronService(db_session)

    created = await neuron_service.create(
        directory_id=docs_id,
        title="Error Handling",
        content="Use try/except for recoverable failures.",
        metadata={"tags": ["python"]},
    )
    assert created.title == "Error Handling"
    assert created.metadata_json == {"tags": ["python"]}

    listed = await neuron_service.list_by_directory(docs_id)
    assert len(listed) == 1
    assert listed[0].id == created.id

    updated = await neuron_service.update(
        created.id,
        title="Exception Handling",
        content="Prefer specific exception types.",
    )
    assert updated.title == "Exception Handling"

    await neuron_service.delete(created.id)
    assert await neuron_service.get_by_id(created.id) is None


@pytest.mark.asyncio
async def test_create_rejects_empty_title_or_content(db_session: AsyncSession) -> None:
    docs_id, _root_id = await _create_project_with_directory(db_session)
    neuron_service = KnowledgeNeuronService(db_session)

    with pytest.raises(KnowledgeNeuronValidationError, match="Title"):
        await neuron_service.create(
            directory_id=docs_id,
            title="   ",
            content="Valid content",
        )

    with pytest.raises(KnowledgeNeuronValidationError, match="Content"):
        await neuron_service.create(
            directory_id=docs_id,
            title="Valid title",
            content="   ",
        )


@pytest.mark.asyncio
async def test_require_by_id_raises_when_missing(db_session: AsyncSession) -> None:
    with pytest.raises(KnowledgeNeuronNotFoundError):
        await KnowledgeNeuronService(db_session).require_by_id(uuid4())
