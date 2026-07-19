"""Tests for ContextBuilder ProjectContext assembly."""

from collections.abc import AsyncIterator

import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from knowledge_ai.core.config import Settings
from knowledge_ai.services.casbin_permission import CasbinPermissionService
from knowledge_ai.services.command import CommandService
from knowledge_ai.services.context_builder import ContextBuilder
from knowledge_ai.services.directory import DirectoryService
from knowledge_ai.services.knowledge_neuron import KnowledgeNeuronService
from knowledge_ai.services.membership import MembershipService
from knowledge_ai.services.project import ProjectService
from knowledge_ai.services.user import UserService

TEST_SETTINGS = Settings(
    jwt_secret_key="test-secret-key-at-least-32-chars-long",
    google_client_id="test-client-id",
    google_client_secret="test-client-secret",
)


@pytest.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
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


@pytest.mark.asyncio
async def test_context_builder_includes_only_exposed_projects(db_session: AsyncSession) -> None:
    user = await UserService(db_session).upsert_from_google(
        google_sub="ctx-user",
        email="ctx@example.com",
        full_name="Context User",
    )
    perm_service = CasbinPermissionService(db_session, TEST_SETTINGS)
    await perm_service.sync_user_role(user)

    membership_service = MembershipService(db_session, perm_service)
    directory_service = DirectoryService(db_session)
    command_service = CommandService(db_session)
    neuron_service = KnowledgeNeuronService(db_session)

    exposed_project = await ProjectService(db_session).create(
        name="Exposed",
        description="visible to MCP",
    )
    hidden_project = await ProjectService(db_session).create(
        name="Hidden",
        description="not exposed",
    )

    await membership_service.add_member(project_id=exposed_project.id, user_id=user.id)
    await membership_service.add_member(project_id=hidden_project.id, user_id=user.id)
    await membership_service.set_context_exposed(
        user_id=user.id,
        project_id=exposed_project.id,
        is_context_exposed=True,
    )
    await membership_service.set_context_exposed(
        user_id=user.id,
        project_id=hidden_project.id,
        is_context_exposed=False,
    )

    exposed_root = await directory_service.get_root_for_project(exposed_project.id)
    assert exposed_root is not None
    docs = await directory_service.create(
        project_id=exposed_project.id,
        parent_id=exposed_root.id,
        name="Docs",
    )
    await neuron_service.create(
        directory_id=docs.id,
        title="Auth patterns",
        content="Use PKCE for public clients.",
    )
    await CommandService(db_session).create(
        directory_id=docs.id,
        title="Run tests",
        content="uv run pytest",
    )

    builder = ContextBuilder(
        db_session,
        membership_service,
        directory_service,
        command_service,
    )
    context = await builder.build_for_user(user)

    assert len(context.projects) == 1
    project_context = context.projects[0]
    assert project_context.project_id == exposed_project.id
    assert project_context.project_name == "Exposed"
    assert project_context.root.name == "Root"

    docs_node = next(child for child in project_context.root.children if child.name == "Docs")
    assert len(docs_node.knowledge_neurons) == 1
    assert docs_node.knowledge_neurons[0].title == "Auth patterns"
    assert len(docs_node.commands) == 1
    assert docs_node.commands[0].title == "Run tests"


@pytest.mark.asyncio
async def test_context_builder_returns_empty_when_nothing_exposed(
    db_session: AsyncSession,
) -> None:
    user = await UserService(db_session).upsert_from_google(
        google_sub="ctx-empty",
        email="empty@example.com",
        full_name=None,
    )
    perm_service = CasbinPermissionService(db_session, TEST_SETTINGS)
    membership_service = MembershipService(db_session, perm_service)
    builder = ContextBuilder(
        db_session,
        membership_service,
        DirectoryService(db_session),
        CommandService(db_session),
    )
    context = await builder.build_for_user(user)
    assert context.projects == []
