"""HTTP integration tests for Project, Membership, Account, and Admin user APIs."""

from __future__ import annotations

from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from knowledge_ai.core.config import Settings, get_settings
from knowledge_ai.core.database import get_db
from knowledge_ai.core.deps import get_current_user
from knowledge_ai.main import app
from knowledge_ai.models.project_membership import ProjectMembershipRole
from knowledge_ai.models.user import User, UserRole
from knowledge_ai.services.jwt import JWTService
from knowledge_ai.services.membership import MembershipService
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
        email=f"{role.value}-{uuid4()}@example.com",
        full_name="Test User",
        google_sub=f"google-{uuid4()}",
        role=role,
        is_active=True,
        created_at=now,
        updated_at=now,
    )


async def _persist_user(session: AsyncSession, user: User) -> User:
    session.add(user)
    await session.flush()
    return user


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


def _auth_client(
    *,
    user: User,
    session: AsyncSession,
    jwt_service: JWTService,
) -> AsyncClient:
    token, _ = jwt_service.create_access_token(
        user_id=user.id,
        email=user.email,
        role=user.role.value,
    )

    async def override_get_db() -> AsyncIterator[AsyncSession]:
        yield session

    async def override_get_current_user() -> User:
        return user

    _apply_test_settings()
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user

    transport = ASGITransport(app=app)
    return AsyncClient(
        transport=transport,
        base_url="http://test",
        headers={"Authorization": f"Bearer {token}"},
    )


@pytest.fixture(autouse=True)
def _clear_dependency_overrides() -> Iterator[None]:
    yield
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_admin_creates_project_and_adds_member(
    db_session: AsyncSession,
    jwt_service: JWTService,
) -> None:
    admin = await _persist_user(db_session, _make_user(role=UserRole.ADMIN))
    member = await _persist_user(db_session, _make_user(role=UserRole.USER))

    async with _auth_client(user=admin, session=db_session, jwt_service=jwt_service) as client:
        create = await client.post(
            "/api/v1/projects",
            json={"name": "Team Alpha", "description": "Main workspace"},
        )
        assert create.status_code == 201
        project_id = create.json()["id"]

        add_member = await client.post(
            f"/api/v1/projects/{project_id}/members",
            json={"user_id": str(member.id), "role": "owner"},
        )
        assert add_member.status_code == 201
        assert add_member.json()["role"] == "owner"

        members = await client.get(f"/api/v1/projects/{project_id}/members")
        assert members.status_code == 200
        assert len(members.json()) == 1


@pytest.mark.asyncio
async def test_member_lists_only_their_projects(
    db_session: AsyncSession,
    jwt_service: JWTService,
) -> None:
    admin = await _persist_user(db_session, _make_user(role=UserRole.ADMIN))
    member = await _persist_user(db_session, _make_user(role=UserRole.USER))

    project_service = ProjectService(db_session)
    project_a = await project_service.create(name="Project A", description=None)
    project_b = await project_service.create(name="Project B", description=None)

    from knowledge_ai.services.casbin_permission import CasbinPermissionService

    perm_service = CasbinPermissionService(db_session, TEST_SETTINGS)
    await perm_service.ensure_base_policies()
    membership_service = MembershipService(db_session, perm_service)
    await membership_service.add_member(project_id=project_a.id, user_id=member.id)

    async with _auth_client(user=member, session=db_session, jwt_service=jwt_service) as client:
        response = await client.get("/api/v1/projects")
        assert response.status_code == 200
        project_ids = {row["id"] for row in response.json()}
        assert str(project_a.id) in project_ids
        assert str(project_b.id) not in project_ids

    async with _auth_client(user=admin, session=db_session, jwt_service=jwt_service) as client:
        response = await client.get("/api/v1/projects")
        assert response.status_code == 200
        assert len(response.json()) >= 2


@pytest.mark.asyncio
async def test_non_member_cannot_get_project(
    db_session: AsyncSession,
    jwt_service: JWTService,
) -> None:
    user = await _persist_user(db_session, _make_user(role=UserRole.USER))
    project = await ProjectService(db_session).create(name="Private", description=None)

    async with _auth_client(user=user, session=db_session, jwt_service=jwt_service) as client:
        response = await client.get(f"/api/v1/projects/{project.id}")
        assert response.status_code == 403


@pytest.mark.asyncio
async def test_account_lists_projects_and_toggles_exposure(
    db_session: AsyncSession,
    jwt_service: JWTService,
) -> None:
    user = await _persist_user(db_session, _make_user(role=UserRole.USER))
    project = await ProjectService(db_session).create(name="MCP Project", description=None)

    from knowledge_ai.services.casbin_permission import CasbinPermissionService

    perm_service = CasbinPermissionService(db_session, TEST_SETTINGS)
    await perm_service.ensure_base_policies()
    membership_service = MembershipService(db_session, perm_service)
    await membership_service.add_member(
        project_id=project.id,
        user_id=user.id,
        role=ProjectMembershipRole.MEMBER,
    )

    async with _auth_client(user=user, session=db_session, jwt_service=jwt_service) as client:
        account = await client.get("/api/v1/account")
        assert account.status_code == 200
        assert len(account.json()) == 1
        assert account.json()[0]["is_context_exposed"] is False

        toggle = await client.patch(
            f"/api/v1/account/projects/{project.id}",
            json={"is_context_exposed": True},
        )
        assert toggle.status_code == 200
        assert toggle.json()["is_context_exposed"] is True

        account_after = await client.get("/api/v1/account")
        assert account_after.json()[0]["is_context_exposed"] is True


@pytest.mark.asyncio
async def test_admin_updates_user_role(
    db_session: AsyncSession,
    jwt_service: JWTService,
) -> None:
    admin = await _persist_user(db_session, _make_user(role=UserRole.ADMIN))
    target = await _persist_user(db_session, _make_user(role=UserRole.USER))

    async with _auth_client(user=admin, session=db_session, jwt_service=jwt_service) as client:
        response = await client.patch(
            f"/api/v1/admin/users/{target.id}",
            json={"role": "admin"},
        )
        assert response.status_code == 200
        assert response.json()["role"] == "admin"


@pytest.mark.asyncio
async def test_regular_user_cannot_create_project(
    db_session: AsyncSession,
    jwt_service: JWTService,
) -> None:
    user = await _persist_user(db_session, _make_user(role=UserRole.USER))

    async with _auth_client(user=user, session=db_session, jwt_service=jwt_service) as client:
        response = await client.post("/api/v1/projects", json={"name": "Nope"})
        assert response.status_code == 403
