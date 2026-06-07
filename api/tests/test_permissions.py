"""Tests for Casbin RBAC and permission HTTP endpoints."""

from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from knowledge_ai.core.config import Settings, get_settings
from knowledge_ai.core.deps import get_casbin_permission_service, get_current_user
from knowledge_ai.main import app
from knowledge_ai.models.user import User, UserRole
from knowledge_ai.schemas.permissions import DirectoryPermission
from knowledge_ai.services.casbin_permission import CasbinPermissionService
from knowledge_ai.services.jwt import JWTService

TEST_SETTINGS = Settings(
    jwt_secret_key="test-secret-key-at-least-32-chars-long",
    google_client_id="test-client-id",
    google_client_secret="test-client-secret",
    cors_origins=["http://localhost:5173/auth/callback"],
)


def _apply_test_settings() -> None:
    app.dependency_overrides[get_settings] = lambda: TEST_SETTINGS


@pytest.fixture
def jwt_service() -> JWTService:
    return JWTService(TEST_SETTINGS)


def _make_user(*, role: UserRole) -> User:
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
async def user_client(jwt_service: JWTService) -> AsyncIterator[AsyncClient]:
    user = _make_user(role=UserRole.USER)
    token, _ = jwt_service.create_access_token(
        user_id=user.id,
        email=user.email,
        role=user.role.value,
    )

    async def override_get_current_user() -> User:
        return user

    _apply_test_settings()
    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as client:
        yield client


@pytest.fixture
async def admin_client(jwt_service: JWTService) -> AsyncIterator[AsyncClient]:
    admin = _make_user(role=UserRole.ADMIN)
    token, _ = jwt_service.create_access_token(
        user_id=admin.id,
        email=admin.email,
        role=admin.role.value,
    )

    async def override_get_current_user() -> User:
        return admin

    _apply_test_settings()
    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = ASGITransport(app=app)
    async with AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    ) as client:
        yield client


@pytest.fixture(autouse=True)
def _clear_dependency_overrides() -> Iterator[None]:
    yield
    app.dependency_overrides.clear()


async def test_admin_users_forbidden_for_regular_user(user_client: AsyncClient) -> None:
    response = await user_client.get("/api/v1/admin/users")
    assert response.status_code == 403


async def test_admin_users_allowed_for_admin(admin_client: AsyncClient) -> None:
    mock_user_service = AsyncMock()
    mock_user_service.list_all = AsyncMock(return_value=[])

    from knowledge_ai.core.deps import get_user_service

    app.dependency_overrides[get_user_service] = lambda: mock_user_service

    response = await admin_client.get("/api/v1/admin/users")
    assert response.status_code == 200
    assert response.json() == []


async def test_grant_directory_permission_requires_admin(user_client: AsyncClient) -> None:
    directory_id = uuid4()
    target_user_id = uuid4()
    response = await user_client.post(
        f"/api/v1/permissions/directories/{directory_id}",
        json={"user_id": str(target_user_id), "permission": "READ"},
    )
    assert response.status_code == 403


async def test_grant_and_list_directory_permissions(admin_client: AsyncClient) -> None:
    directory_id = uuid4()
    target_user_id = uuid4()

    mock_perm = AsyncMock(spec=CasbinPermissionService)
    mock_perm.grant_directory_permission = AsyncMock(return_value=True)
    mock_perm.list_directory_permissions_for_user = AsyncMock(
        return_value=[(directory_id, DirectoryPermission.READ)],
    )

    app.dependency_overrides[get_casbin_permission_service] = lambda: mock_perm

    grant = await admin_client.post(
        f"/api/v1/permissions/directories/{directory_id}",
        json={"user_id": str(target_user_id), "permission": "READ"},
    )
    assert grant.status_code == 204

    mock_perm.list_directory_permissions_for_user = AsyncMock(
        return_value=[(directory_id, DirectoryPermission.READ)],
    )
    app.dependency_overrides[get_casbin_permission_service] = lambda: mock_perm

    listing = await admin_client.get("/api/v1/permissions/me")
    assert listing.status_code == 200
    payload = listing.json()
    assert len(payload["permissions"]) == 1
    assert payload["permissions"][0]["directory_id"] == str(directory_id)
    assert payload["permissions"][0]["permission"] == "READ"
