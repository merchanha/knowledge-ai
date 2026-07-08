"""Integration tests for ProjectService and MembershipService."""

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from uuid import uuid4

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from knowledge_ai.core.config import Settings
from knowledge_ai.models.project_membership import ProjectMembershipRole
from knowledge_ai.models.user import User, UserRole
from knowledge_ai.schemas.permissions import DirectoryPermission
from knowledge_ai.services.casbin_permission import CasbinPermissionService
from knowledge_ai.services.directory import DirectoryService
from knowledge_ai.services.membership import (
    MembershipConflictError,
    MembershipNotFoundError,
    MembershipService,
)
from knowledge_ai.services.project import (
    ProjectNotFoundError,
    ProjectService,
    ProjectValidationError,
)

TEST_SETTINGS = Settings(
    jwt_secret_key="test-secret-key-at-least-32-chars-long",
    google_client_id="test-client-id",
    google_client_secret="test-client-secret",
    cors_origins=["http://localhost:5173/auth/callback"],
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


@pytest.mark.asyncio
async def test_project_crud_and_archive(db_session: AsyncSession) -> None:
    project_service = ProjectService(db_session)

    created = await project_service.create(name="Alpha", description="First project")
    assert created.name == "Alpha"

    root = await DirectoryService(db_session).get_root_for_project(created.id)
    assert root is not None
    assert root.name == "Root"

    updated = await project_service.update(created.id, name="Alpha Renamed")
    assert updated.name == "Alpha Renamed"

    archived = await project_service.archive(created.id)
    assert archived.is_archived is True

    restored = await project_service.unarchive(created.id)
    assert restored.is_archived is False

    await project_service.delete(created.id)
    assert await project_service.get_by_id(created.id) is None


@pytest.mark.asyncio
async def test_project_create_rejects_empty_name(db_session: AsyncSession) -> None:
    with pytest.raises(ProjectValidationError, match="name"):
        await ProjectService(db_session).create(name="   ")


@pytest.mark.asyncio
async def test_require_by_id_raises_when_missing(db_session: AsyncSession) -> None:
    with pytest.raises(ProjectNotFoundError):
        await ProjectService(db_session).require_by_id(uuid4())


@pytest.mark.asyncio
async def test_add_member_grants_manage_on_root(db_session: AsyncSession) -> None:
    project = await ProjectService(db_session).create(name="Member Project", description=None)
    user = await _persist_user(db_session, _make_user())

    perm_service = CasbinPermissionService(db_session, TEST_SETTINGS)
    await perm_service.ensure_base_policies()
    membership_service = MembershipService(db_session, perm_service)

    membership = await membership_service.add_member(
        project_id=project.id,
        user_id=user.id,
        role=ProjectMembershipRole.OWNER,
    )
    assert membership.role == ProjectMembershipRole.OWNER

    root = await DirectoryService(db_session).get_root_for_project(project.id)
    assert root is not None
    allowed = await perm_service.check_directory_permission(
        user,
        root.id,
        DirectoryPermission.MANAGE,
    )
    assert allowed is True


@pytest.mark.asyncio
async def test_remove_member_revokes_manage_on_root(db_session: AsyncSession) -> None:
    project = await ProjectService(db_session).create(name="Remove Member", description=None)
    user = await _persist_user(db_session, _make_user())

    perm_service = CasbinPermissionService(db_session, TEST_SETTINGS)
    await perm_service.ensure_base_policies()
    membership_service = MembershipService(db_session, perm_service)

    await membership_service.add_member(
        project_id=project.id,
        user_id=user.id,
        role=ProjectMembershipRole.MEMBER,
    )
    await membership_service.remove_member(project_id=project.id, user_id=user.id)

    root = await DirectoryService(db_session).get_root_for_project(project.id)
    assert root is not None
    allowed = await perm_service.check_directory_permission(
        user,
        root.id,
        DirectoryPermission.MANAGE,
    )
    assert allowed is False

    with pytest.raises(MembershipNotFoundError):
        await membership_service.require_membership(user_id=user.id, project_id=project.id)


@pytest.mark.asyncio
async def test_add_member_rejects_duplicate(db_session: AsyncSession) -> None:
    project = await ProjectService(db_session).create(name="Dup Member", description=None)
    user = await _persist_user(db_session, _make_user())

    perm_service = CasbinPermissionService(db_session, TEST_SETTINGS)
    await perm_service.ensure_base_policies()
    membership_service = MembershipService(db_session, perm_service)

    await membership_service.add_member(project_id=project.id, user_id=user.id)
    with pytest.raises(MembershipConflictError):
        await membership_service.add_member(project_id=project.id, user_id=user.id)


@pytest.mark.asyncio
async def test_set_context_exposed_on_membership(db_session: AsyncSession) -> None:
    project = await ProjectService(db_session).create(name="Exposure", description=None)
    user = await _persist_user(db_session, _make_user())

    perm_service = CasbinPermissionService(db_session, TEST_SETTINGS)
    await perm_service.ensure_base_policies()
    membership_service = MembershipService(db_session, perm_service)

    await membership_service.add_member(project_id=project.id, user_id=user.id)
    updated = await membership_service.set_context_exposed(
        user_id=user.id,
        project_id=project.id,
        is_context_exposed=True,
    )
    assert updated.is_context_exposed is True

    account_projects = await membership_service.list_projects_for_user(user.id)
    assert len(account_projects) == 1
    assert account_projects[0].project.id == project.id
    assert account_projects[0].membership.is_context_exposed is True
