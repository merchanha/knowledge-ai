"""HTTP integration tests for Command REST API."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from knowledge_ai.core.config import Settings, get_settings
from knowledge_ai.core.database import get_db
from knowledge_ai.core.deps import get_current_user
from knowledge_ai.main import app
from knowledge_ai.models.user import User, UserRole
from knowledge_ai.schemas.permissions import DirectoryPermission
from knowledge_ai.services.casbin_permission import CasbinPermissionService
from knowledge_ai.services.command import CommandService
from knowledge_ai.services.directory import DirectoryService
from knowledge_ai.services.jwt import JWTService
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


async def _create_project_scripts_directory(session: AsyncSession) -> tuple[UUID, UUID]:
    project = await ProjectService(session).create(name="API Project", description="desc")
    root = await DirectoryService(session).get_root_for_project(project.id)
    assert root is not None
    scripts = await DirectoryService(session).create(
        project_id=project.id,
        parent_id=root.id,
        name="Scripts",
    )
    return project.id, scripts.id


@pytest.mark.asyncio
async def test_list_commands_forbidden_without_permission(
    authed_client: tuple[AsyncClient, User, AsyncSession],
) -> None:
    client, _user, session = authed_client
    _project_id, scripts_id = await _create_project_scripts_directory(session)

    response = await client.get(f"/api/v1/directories/{scripts_id}/commands")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_command_crud_flow_over_http(
    authed_client: tuple[AsyncClient, User, AsyncSession],
) -> None:
    client, user, session = authed_client
    _project_id, scripts_id = await _create_project_scripts_directory(session)
    await _grant_directory(
        session,
        user_id=user.id,
        directory_id=scripts_id,
        permission=DirectoryPermission.MANAGE,
    )

    create = await client.post(
        f"/api/v1/directories/{scripts_id}/commands",
        json={
            "title": "Run Tests",
            "content": "uv run pytest",
            "metadata": {"tags": ["ci"]},
        },
    )
    assert create.status_code == 201
    command_id = create.json()["id"]
    assert create.json()["title"] == "Run Tests"
    assert create.json()["metadata"] == {"tags": ["ci"]}

    listing = await client.get(f"/api/v1/directories/{scripts_id}/commands")
    assert listing.status_code == 200
    assert len(listing.json()) == 1
    assert listing.json()[0]["id"] == command_id

    get_one = await client.get(f"/api/v1/commands/{command_id}")
    assert get_one.status_code == 200
    assert get_one.json()["content"] == "uv run pytest"

    update = await client.patch(
        f"/api/v1/commands/{command_id}",
        json={"title": "Run Full Suite"},
    )
    assert update.status_code == 200
    assert update.json()["title"] == "Run Full Suite"

    delete = await client.delete(f"/api/v1/commands/{command_id}")
    assert delete.status_code == 204

    listing_after = await client.get(f"/api/v1/directories/{scripts_id}/commands")
    assert listing_after.status_code == 200
    assert listing_after.json() == []


@pytest.mark.asyncio
async def test_get_command_requires_read_on_parent_directory(
    authed_client: tuple[AsyncClient, User, AsyncSession],
) -> None:
    client, user, session = authed_client
    _project_id, scripts_id = await _create_project_scripts_directory(session)
    command = await CommandService(session).create(
        directory_id=scripts_id,
        title="Hidden",
        content="Secret command",
    )

    response = await client.get(f"/api/v1/commands/{command.id}")
    assert response.status_code == 403

    await _grant_directory(
        session,
        user_id=user.id,
        directory_id=scripts_id,
        permission=DirectoryPermission.READ,
    )
    response = await client.get(f"/api/v1/commands/{command.id}")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_delete_command_requires_manage_permission(
    authed_client: tuple[AsyncClient, User, AsyncSession],
) -> None:
    client, user, session = authed_client
    _project_id, scripts_id = await _create_project_scripts_directory(session)
    command = await CommandService(session).create(
        directory_id=scripts_id,
        title="Draft",
        content="Temporary snippet",
    )
    await _grant_directory(
        session,
        user_id=user.id,
        directory_id=scripts_id,
        permission=DirectoryPermission.WRITE,
    )

    response = await client.delete(f"/api/v1/commands/{command.id}")
    assert response.status_code == 403
