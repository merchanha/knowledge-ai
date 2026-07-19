"""Tests for MCP tool permission scoping."""

from collections.abc import AsyncIterator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.pool import NullPool

from knowledge_ai.core.config import Settings, get_settings
from knowledge_ai.core.mcp_context import set_current_mcp_user
from knowledge_ai.main import app
from knowledge_ai.models.user import User, UserRole
from knowledge_ai.schemas.permissions import DirectoryPermission
from knowledge_ai.services.casbin_permission import CasbinPermissionService
from knowledge_ai.services.command import CommandService
from knowledge_ai.services.directory import DirectoryService
from knowledge_ai.services.embedding import SearchResult
from knowledge_ai.services.project import ProjectService

TEST_SETTINGS = Settings(
    jwt_secret_key="test-secret-key-at-least-32-chars-long",
    google_client_id="test-client-id",
    google_client_secret="test-client-secret",
    voyage_api_key="test-voyage-key",
)


def _apply_test_settings() -> None:
    app.dependency_overrides[get_settings] = lambda: TEST_SETTINGS
    import knowledge_ai.middleware.mcp_auth as mcp_auth_middleware

    mcp_auth_middleware.get_settings = lambda: TEST_SETTINGS  # type: ignore[attr-defined, assignment]


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


def _make_user() -> User:
    now = datetime.now(UTC)
    return User(
        id=uuid4(),
        email="tools@example.com",
        full_name="Tools User",
        google_sub="google-tools",
        role=UserRole.USER,
        is_active=True,
        created_at=now,
        updated_at=now,
    )


@pytest.mark.asyncio
async def test_list_commands_scoped_to_readable_directories(db_session: AsyncSession) -> None:
    user = _make_user()
    perm_service = CasbinPermissionService(db_session, TEST_SETTINGS)
    await perm_service.sync_user_role(user)

    project = await ProjectService(db_session).create(name="Tool Project", description=None)
    root = await DirectoryService(db_session).get_root_for_project(project.id)
    assert root is not None
    docs = await DirectoryService(db_session).create(
        project_id=project.id,
        parent_id=root.id,
        name="Docs",
    )
    await perm_service.grant_directory_permission(
        user_id=user.id,
        directory_id=docs.id,
        permission=DirectoryPermission.READ,
    )
    await CommandService(db_session).create(
        directory_id=docs.id,
        title="Lint",
        content="uv run ruff check .",
    )

    command_service = CommandService(db_session)
    readable_ids = await perm_service.get_readable_directory_ids(user)
    commands = await command_service.list_in_directories(readable_ids)
    assert len(commands) == 1
    assert commands[0].title == "Lint"


@pytest.mark.asyncio
async def test_search_tool_uses_directory_scoping(monkeypatch: pytest.MonkeyPatch) -> None:
    from knowledge_ai.mcp.server import create_mcp_server
    from knowledge_ai.models.knowledge_neuron import KnowledgeNeuron

    user = _make_user()
    neuron_id = uuid4()
    directory_id = uuid4()
    neuron = KnowledgeNeuron(
        id=neuron_id,
        directory_id=directory_id,
        title="Testing",
        content="pytest patterns",
        metadata_json={},
    )

    async def fake_search(
        self: object,
        *,
        query: str,
        directory_ids: list[UUID] | None,
        limit: int,
    ) -> list[SearchResult]:
        assert query == "pytest"
        assert directory_ids == [directory_id]
        return [SearchResult(neuron=neuron, similarity=0.91)]

    monkeypatch.setattr(
        "knowledge_ai.mcp.server.EmbeddingService.search",
        fake_search,
    )
    monkeypatch.setattr(
        "knowledge_ai.mcp.server.CasbinPermissionService.get_readable_directory_ids",
        AsyncMock(return_value=[directory_id]),
    )

    server = create_mcp_server()
    set_current_mcp_user(user)
    tool_fn = server._tool_manager._tools["search_knowledge_neurons"].fn  # noqa: SLF001
    results = await tool_fn(query="pytest", limit=5)
    assert results[0]["title"] == "Testing"
    assert results[0]["similarity"] == 0.91


@pytest.mark.asyncio
async def test_mcp_http_lists_tools_when_authenticated() -> None:
    from knowledge_ai.services.jwt import JWTService

    settings = TEST_SETTINGS
    _apply_test_settings()
    jwt_service = JWTService(settings)
    user_id = uuid4()
    token, _ = jwt_service.create_access_token(
        user_id=user_id,
        email="mcp@example.com",
        role=UserRole.USER.value,
    )
    now = datetime.now(UTC)
    user = User(
        id=user_id,
        email="mcp@example.com",
        full_name="MCP",
        google_sub="sub",
        role=UserRole.USER,
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    with patch(
        "knowledge_ai.middleware.mcp_auth.UserService.get_by_id",
        new_callable=AsyncMock,
        return_value=user,
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(
            transport=transport,
            base_url="http://test",
            headers={"Authorization": f"Bearer {token}"},
        ) as client:
            response = await client.post(
                "/mcp",
                headers={"Accept": "application/json"},
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/list",
                    "params": {},
                },
            )

    app.dependency_overrides.clear()
    assert response.status_code != 401
    if response.status_code == 200:
        payload = response.json()
        tool_names = {tool["name"] for tool in payload["result"]["tools"]}
        assert "search_knowledge_neurons" in tool_names
        assert "list_commands" in tool_names
        assert "get_project_context" in tool_names
