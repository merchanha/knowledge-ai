"""HTTP integration tests for directory REST API."""

from __future__ import annotations

import io
import zipfile
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
from knowledge_ai.models.directory import ROOT_DIRECTORY_NAME
from knowledge_ai.models.user import User, UserRole
from knowledge_ai.schemas.permissions import DirectoryPermission
from knowledge_ai.services.casbin_permission import CasbinPermissionService
from knowledge_ai.services.directory import DirectoryService
from knowledge_ai.services.jwt import JWTService
from knowledge_ai.services.project import ProjectService

TEST_SETTINGS = Settings(
    jwt_secret_key="test-secret-key-at-least-32-chars-long",
    google_client_id="test-client-id",
    google_client_secret="test-client-secret",
    cors_origins=["http://localhost:5173/auth/callback"],
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


async def _grant_on_root(
    session: AsyncSession,
    *,
    user_id: UUID,
    root_id: UUID,
    permission: DirectoryPermission,
) -> None:
    await _grant_directory(
        session,
        user_id=user_id,
        directory_id=root_id,
        permission=permission,
    )


async def _create_project_tree(session: AsyncSession) -> tuple[UUID, UUID]:
    project = await ProjectService(session).create(name="API Project", description="desc")
    root = await DirectoryService(session).get_root_for_project(project.id)
    assert root is not None
    return project.id, root.id


@pytest.mark.asyncio
async def test_list_tree_forbidden_without_permission(
    authed_client: tuple[AsyncClient, User, AsyncSession],
) -> None:
    client, _user, session = authed_client
    project_id, _root_id = await _create_project_tree(session)

    response = await client.get(f"/api/v1/projects/{project_id}/directories/tree")
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_directory_crud_flow_over_http(
    authed_client: tuple[AsyncClient, User, AsyncSession],
) -> None:
    client, user, session = authed_client
    project_id, root_id = await _create_project_tree(session)
    await _grant_on_root(
        session,
        user_id=user.id,
        root_id=root_id,
        permission=DirectoryPermission.MANAGE,
    )

    create = await client.post(
        f"/api/v1/directories/{root_id}/children",
        json={"name": "Docs"},
    )
    assert create.status_code == 201
    docs_id = create.json()["id"]
    assert create.json()["name"] == "Docs"
    assert create.json()["parent_id"] == str(root_id)

    await _grant_directory(
        session,
        user_id=user.id,
        directory_id=UUID(docs_id),
        permission=DirectoryPermission.MANAGE,
    )

    rename = await client.patch(
        f"/api/v1/directories/{docs_id}",
        json={"name": "Documentation"},
    )
    assert rename.status_code == 200
    assert rename.json()["name"] == "Documentation"

    api_create = await client.post(
        f"/api/v1/directories/{root_id}/children",
        json={"name": "API"},
    )
    assert api_create.status_code == 201
    api_id = api_create.json()["id"]

    await _grant_directory(
        session,
        user_id=user.id,
        directory_id=UUID(api_id),
        permission=DirectoryPermission.WRITE,
    )

    move = await client.patch(
        f"/api/v1/directories/{api_id}/move",
        json={"new_parent_id": docs_id},
    )
    assert move.status_code == 200
    assert move.json()["parent_id"] == docs_id

    children = await client.get(f"/api/v1/directories/{root_id}/children")
    assert children.status_code == 200
    assert {item["id"] for item in children.json()} == {docs_id}

    await _grant_directory(
        session,
        user_id=user.id,
        directory_id=UUID(api_id),
        permission=DirectoryPermission.READ,
    )

    breadcrumbs = await client.get(f"/api/v1/directories/{api_id}/breadcrumbs")
    assert breadcrumbs.status_code == 200
    assert [item["name"] for item in breadcrumbs.json()] == [
        ROOT_DIRECTORY_NAME,
        "Documentation",
        "API",
    ]

    tree = await client.get(f"/api/v1/projects/{project_id}/directories/tree")
    assert tree.status_code == 200
    assert len(tree.json()) == 3

    delete = await client.delete(f"/api/v1/directories/{docs_id}")
    assert delete.status_code == 204

    tree_after = await client.get(f"/api/v1/projects/{project_id}/directories/tree")
    assert tree_after.status_code == 200
    assert len(tree_after.json()) == 1
    assert tree_after.json()[0]["name"] == ROOT_DIRECTORY_NAME


@pytest.mark.asyncio
async def test_download_subtree_zip(
    authed_client: tuple[AsyncClient, User, AsyncSession],
) -> None:
    client, user, session = authed_client
    project_id, root_id = await _create_project_tree(session)
    directory_service = DirectoryService(session)
    docs = await directory_service.create(
        project_id=project_id,
        parent_id=root_id,
        name="Docs",
    )
    await directory_service.create(
        project_id=project_id,
        parent_id=docs.id,
        name="API",
    )
    await _grant_directory(
        session,
        user_id=user.id,
        directory_id=docs.id,
        permission=DirectoryPermission.READ,
    )

    response = await client.get(f"/api/v1/directories/{docs.id}/download")
    assert response.status_code == 200
    assert response.headers["content-type"] == "application/zip"
    assert "Docs.zip" in response.headers["content-disposition"]

    with zipfile.ZipFile(io.BytesIO(response.content)) as archive:
        names = set(archive.namelist())
    assert "Docs/" in names
    assert "Docs/API/" in names


@pytest.mark.asyncio
async def test_rename_conflict_returns_409(
    authed_client: tuple[AsyncClient, User, AsyncSession],
) -> None:
    client, user, session = authed_client
    project_id, root_id = await _create_project_tree(session)
    directory_service = DirectoryService(session)
    await directory_service.create(project_id=project_id, parent_id=root_id, name="Docs")
    second = await directory_service.create(
        project_id=project_id,
        parent_id=root_id,
        name="API",
    )
    await _grant_directory(
        session,
        user_id=user.id,
        directory_id=second.id,
        permission=DirectoryPermission.WRITE,
    )

    response = await client.patch(
        f"/api/v1/directories/{second.id}",
        json={"name": "Docs"},
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_delete_root_returns_400(
    authed_client: tuple[AsyncClient, User, AsyncSession],
) -> None:
    client, user, session = authed_client
    _project_id, root_id = await _create_project_tree(session)
    await _grant_on_root(
        session,
        user_id=user.id,
        root_id=root_id,
        permission=DirectoryPermission.MANAGE,
    )

    response = await client.delete(f"/api/v1/directories/{root_id}")
    assert response.status_code == 400
    assert "root" in response.json()["detail"].lower()
