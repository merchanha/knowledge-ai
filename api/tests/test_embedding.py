"""Integration tests for EmbeddingService vector search."""

from collections.abc import AsyncIterator
from uuid import UUID

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from knowledge_ai.core.config import Settings
from knowledge_ai.services.directory import DirectoryService
from knowledge_ai.services.embedding import EmbeddingService
from knowledge_ai.services.knowledge_neuron import KnowledgeNeuronService
from knowledge_ai.services.project import ProjectService

TEST_SETTINGS = Settings(
    jwt_secret_key="test-secret-key-at-least-32-chars-long",
    google_client_id="test-client-id",
    google_client_secret="test-client-secret",
    voyage_api_key="test-voyage-key",
)


@pytest.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    """Postgres session in a transaction that always rolls back."""
    engine = create_async_engine(TEST_SETTINGS.database_url, poolclass=NullPool)
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


def _unit_vector(index: int, dimensions: int = 1024) -> list[float]:
    vector = [0.0] * dimensions
    vector[index] = 1.0
    return vector


async def _create_neuron_with_embedding(
    session: AsyncSession,
    *,
    title: str,
    vector_index: int,
) -> tuple[UUID, UUID]:
    project = await ProjectService(session).create(name="Search Project", description="desc")
    root = await DirectoryService(session).get_root_for_project(project.id)
    assert root is not None
    docs = await DirectoryService(session).create(
        project_id=project.id,
        parent_id=root.id,
        name="Docs",
    )
    neuron = await KnowledgeNeuronService(session).create(
        directory_id=docs.id,
        title=title,
        content=f"Content for {title}",
    )
    neuron.embedding = _unit_vector(vector_index)
    await session.flush()
    return docs.id, neuron.id


@pytest.mark.asyncio
async def test_search_returns_neurons_by_cosine_similarity(
    db_session: AsyncSession,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    docs_id, neuron_id = await _create_neuron_with_embedding(
        db_session,
        title="Error Handling",
        vector_index=0,
    )
    await _create_neuron_with_embedding(
        db_session,
        title="Deployment",
        vector_index=1,
    )

    service = EmbeddingService(db_session, TEST_SETTINGS)

    async def fake_embed_query(_query: str) -> list[float]:
        return _unit_vector(0)

    monkeypatch.setattr(service, "embed_query", fake_embed_query)

    scoped = await service.search(
        query="how do I catch exceptions",
        directory_ids=[docs_id],
        limit=5,
    )
    assert len(scoped) == 1
    assert scoped[0].neuron.id == neuron_id
    assert scoped[0].similarity == pytest.approx(1.0)

    project = await ProjectService(db_session).create(name="Empty Project", description="desc")
    root = await DirectoryService(db_session).get_root_for_project(project.id)
    assert root is not None
    empty_dir = await DirectoryService(db_session).create(
        project_id=project.id,
        parent_id=root.id,
        name="Empty",
    )

    empty = await service.search(
        query="how do I catch exceptions",
        directory_ids=[empty_dir.id],
        limit=5,
    )
    assert empty == []
