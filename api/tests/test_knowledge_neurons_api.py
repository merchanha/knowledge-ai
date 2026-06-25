"""HTTP integration tests for KnowledgeNeuron REST API."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from knowledge_ai.core.config import Settings, get_settings
from knowledge_ai.core.database import get_db
from knowledge_ai.core.deps import get_current_user, get_embedding_service
from knowledge_ai.main import app
from knowledge_ai.models.user import User, UserRole
from knowledge_ai.schemas.permissions import DirectoryPermission
from knowledge_ai.services.casbin_permission import CasbinPermissionService
from knowledge_ai.services.directory import DirectoryService
from knowledge_ai.services.embedding import EmbeddingService, SearchResult
from knowledge_ai.services.jwt import JWTService
from knowledge_ai.services.knowledge_neuron import KnowledgeNeuronService
from knowledge_ai.services.project import ProjectService

TEST_SETTINGS = Settings(
    jwt_secret_key="test-secret-key-at-least-32-chars-long",
    google_client_id="test-client-id",
    google_client_secret="test-client-secret",
    cors_origins=["http://localhost:5173/auth/callback"],
    voyage_api_key="test-voyage-key",
)


def _apply_test_settings() -> None:
    app.dependency_overrides[get_settings] = lambda: TEST_SETTINGS


def _make_user(*, role: UserRole = UserRole.USER) -> User:
    now = datetime.now(UTC)
    return User(
        id=uuid4(),
        email=f"{role.value}@example.com",
        full_name="Test User",
        google_sub=f"google-{role.value}",
        role=role,
        is_active=True,
        created_at=now,
        updated_at=now,
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


@pytest.fixture
def jwt_service() -> JWTService:
    return JWTService(TEST_SETTINGS)


@pytest.fixture
async def authed_client(
    db_session: AsyncSession,
    jwt_service: JWTService,
) -> AsyncIterator[tuple[AsyncClient, User, AsyncSession]]:
    user = _make_user(role=UserRole.USER)
    token, _ = jwt_service.create_access_token(
        user_id=user.id,
        email=user.email,
        role=user.role.value,
    )

    async def override_get_db() -> AsyncIterator[AsyncSession]:
        yield db_session

    async def override_get_current_user() -> User:
        return user

    _apply_test_settings()
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as client:
        yield client, user, db_session


@pytest.fixture(autouse=True)
def _clear_dependency_overrides() -> Iterator[None]:
    yield
    app.dependency_overrides.clear()


@pytest.fixture(autouse=True)
def _disable_embed_task() -> Iterator[None]:
    with patch(
        "knowledge_ai.services.knowledge_neuron.embed_knowledge_neuron",
        create=True,
    ) as mock_task:
        mock_task.delay = lambda *_args, **_kwargs: None
        with patch(
            "knowledge_ai.services.knowledge_neuron.KnowledgeNeuronService._enqueue_embed",
            staticmethod(lambda _neuron_id: None),
        ):
            yield


async def _grant_directory(
    session: AsyncSession,
    *,
    user_id: UUID,
    directory_id: UUID,
    permission: DirectoryPermission,
) -> None:
    perm_service = CasbinPermissionService(session, TEST_SETTINGS)
    await perm_service.ensure_base_policies()
    await perm_service.grant_directory_permission(
        user_id=user_id,
        directory_id=directory_id,
        permission=permission,
    )
    await session.flush()


async def _create_project_docs_directory(session: AsyncSession) -> tuple[UUID, UUID]:
    project = await ProjectService(session).create(name="API Project", description="desc")
    root = await DirectoryService(session).get_root_for_project(project.id)
    assert root is not None
    docs = await DirectoryService(session).create(
        project_id=project.id,
        parent_id=root.id,
        name="Docs",
    )
    return project.id, docs.id


@pytest.mark.asyncio
async def test_list_neurons_forbidden_without_permission(
    authed_client: tuple[AsyncClient, User, AsyncSession],
) -> None:
    client, _user, session = authed_client
    _project_id, docs_id = await _create_project_docs_directory(session)

    response = await client.get(f"/api/v1/directories/{docs_id}/knowledge-neurons")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_knowledge_neuron_crud_flow_over_http(
    authed_client: tuple[AsyncClient, User, AsyncSession],
) -> None:
    client, user, session = authed_client
    _project_id, docs_id = await _create_project_docs_directory(session)
    await _grant_directory(
        session,
        user_id=user.id,
        directory_id=docs_id,
        permission=DirectoryPermission.MANAGE,
    )

    create = await client.post(
        f"/api/v1/directories/{docs_id}/knowledge-neurons",
        json={
            "title": "Error Handling",
            "content": "Use try/except for recoverable failures.",
            "metadata": {"tags": ["python"]},
        },
    )
    assert create.status_code == 201
    neuron_id = create.json()["id"]
    assert create.json()["title"] == "Error Handling"
    assert create.json()["metadata"] == {"tags": ["python"]}
    assert create.json()["has_embedding"] is False

    listing = await client.get(f"/api/v1/directories/{docs_id}/knowledge-neurons")
    assert listing.status_code == 200
    assert len(listing.json()) == 1
    assert listing.json()[0]["id"] == neuron_id

    get_one = await client.get(f"/api/v1/knowledge-neurons/{neuron_id}")
    assert get_one.status_code == 200
    assert get_one.json()["content"].startswith("Use try/except")

    update = await client.patch(
        f"/api/v1/knowledge-neurons/{neuron_id}",
        json={"title": "Exception Handling"},
    )
    assert update.status_code == 200
    assert update.json()["title"] == "Exception Handling"

    delete = await client.delete(f"/api/v1/knowledge-neurons/{neuron_id}")
    assert delete.status_code == 204

    listing_after = await client.get(f"/api/v1/directories/{docs_id}/knowledge-neurons")
    assert listing_after.status_code == 200
    assert listing_after.json() == []


@pytest.mark.asyncio
async def test_get_neuron_requires_read_on_parent_directory(
    authed_client: tuple[AsyncClient, User, AsyncSession],
) -> None:
    client, user, session = authed_client
    _project_id, docs_id = await _create_project_docs_directory(session)
    neuron = await KnowledgeNeuronService(session).create(
        directory_id=docs_id,
        title="Hidden",
        content="Secret knowledge",
    )

    response = await client.get(f"/api/v1/knowledge-neurons/{neuron.id}")
    assert response.status_code == 403

    await _grant_directory(
        session,
        user_id=user.id,
        directory_id=docs_id,
        permission=DirectoryPermission.READ,
    )
    response = await client.get(f"/api/v1/knowledge-neurons/{neuron.id}")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_delete_neuron_requires_manage_permission(
    authed_client: tuple[AsyncClient, User, AsyncSession],
) -> None:
    client, user, session = authed_client
    _project_id, docs_id = await _create_project_docs_directory(session)
    neuron = await KnowledgeNeuronService(session).create(
        directory_id=docs_id,
        title="Draft",
        content="Temporary note",
    )
    await _grant_directory(
        session,
        user_id=user.id,
        directory_id=docs_id,
        permission=DirectoryPermission.WRITE,
    )

    response = await client.delete(f"/api/v1/knowledge-neurons/{neuron.id}")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_semantic_search_over_http(
    authed_client: tuple[AsyncClient, User, AsyncSession],
) -> None:
    client, user, session = authed_client
    _project_id, docs_id = await _create_project_docs_directory(session)
    neuron = await KnowledgeNeuronService(session).create(
        directory_id=docs_id,
        title="Error Handling",
        content="Use try/except for recoverable failures.",
    )
    await _grant_directory(
        session,
        user_id=user.id,
        directory_id=docs_id,
        permission=DirectoryPermission.READ,
    )

    mock_service = EmbeddingService(session, TEST_SETTINGS)
    mock_service.search = AsyncMock(  # type: ignore[method-assign]
        return_value=[SearchResult(neuron=neuron, similarity=0.92)],
    )

    async def override_embedding_service() -> EmbeddingService:
        return mock_service

    app.dependency_overrides[get_embedding_service] = override_embedding_service

    response = await client.get(
        "/api/v1/knowledge-neurons",
        params={"search_term": "how do I catch exceptions"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["id"] == str(neuron.id)
    assert payload[0]["similarity"] == pytest.approx(0.92)
