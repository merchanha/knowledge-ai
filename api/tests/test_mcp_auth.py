"""Tests for MCP OAuth discovery, token exchange, and auth middleware."""

from collections.abc import AsyncIterator, Iterator
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from knowledge_ai.core.config import Settings, get_settings
from knowledge_ai.core.deps import get_oauth_flow_service
from knowledge_ai.main import app
from knowledge_ai.models.user import User, UserRole
from knowledge_ai.services.jwt import JWTService
from knowledge_ai.services.oauth_flow import AuthTokens, McpAuthorizationResult, OAuthFlowService
from knowledge_ai.services.pkce import PKCEService

TEST_SETTINGS = Settings(
    jwt_secret_key="test-secret-key-at-least-32-chars-long",
    google_client_id="test-client-id",
    google_client_secret="test-client-secret",
    cors_origins=["http://localhost:5173/auth/callback", "http://127.0.0.1:8765/callback"],
    mcp_issuer_url="http://test",
    mcp_google_redirect_uri="http://test/api/v1/auth/mcp/callback",
)


def _apply_test_settings() -> None:
    app.dependency_overrides[get_settings] = lambda: TEST_SETTINGS
    import knowledge_ai.middleware.mcp_auth as mcp_auth_middleware

    mcp_auth_middleware.get_settings = lambda: TEST_SETTINGS  # type: ignore[attr-defined, assignment]


def _make_flow(jwt_service: JWTService) -> OAuthFlowService:
    return OAuthFlowService(
        AsyncMock(),
        jwt_service,
        AsyncMock(),
        AsyncMock(),
        AsyncMock(),
        allowed_redirect_origins=TEST_SETTINGS.cors_origins,
        mcp_google_redirect_uri=TEST_SETTINGS.mcp_google_redirect_uri,
        mcp_auth_code_expire_seconds=600,
    )


@pytest.fixture(autouse=True)
def _clear_dependency_overrides() -> Iterator[None]:
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def jwt_service() -> JWTService:
    return JWTService(TEST_SETTINGS)


async def test_oauth_authorization_server_metadata() -> None:
    _apply_test_settings()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/.well-known/oauth-authorization-server")

    assert response.status_code == 200
    payload = response.json()
    assert payload["issuer"] == "http://test"
    assert payload["authorization_endpoint"] == "http://test/api/v1/auth/mcp/authorize"
    assert payload["token_endpoint"] == "http://test/api/v1/auth/mcp/token"
    assert "S256" in payload["code_challenge_methods_supported"]


async def test_oauth_protected_resource_metadata() -> None:
    _apply_test_settings()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/.well-known/oauth-protected-resource")

    assert response.status_code == 200
    payload = response.json()
    assert payload["resource"] == "http://test/mcp"
    assert payload["authorization_servers"] == ["http://test"]


async def test_mcp_authorize_rejects_unknown_response_type(jwt_service: JWTService) -> None:
    _apply_test_settings()
    app.dependency_overrides[get_oauth_flow_service] = lambda: _make_flow(jwt_service)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/auth/mcp/authorize",
            params={
                "response_type": "token",
                "redirect_uri": "http://127.0.0.1:8765/callback",
                "code_challenge": "abc",
            },
        )

    assert response.status_code == 400


async def test_mcp_authorize_redirects_to_google(jwt_service: JWTService) -> None:
    _apply_test_settings()
    flow = _make_flow(jwt_service)
    flow._oauth.create_authorization_url = lambda **kwargs: "https://accounts.google.com/o/oauth2/v2/auth?test=1"  # type: ignore[method-assign]  # noqa: SLF001
    app.dependency_overrides[get_oauth_flow_service] = lambda: flow

    verifier = PKCEService.generate_code_verifier()
    challenge = PKCEService.generate_code_challenge(verifier)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/auth/mcp/authorize",
            params={
                "response_type": "code",
                "redirect_uri": "http://127.0.0.1:8765/callback",
                "code_challenge": challenge,
                "code_challenge_method": "S256",
            },
            follow_redirects=False,
        )

    assert response.status_code == 302
    assert "accounts.google.com" in response.headers["location"]


async def test_mcp_token_exchange_returns_access_token(jwt_service: JWTService) -> None:
    _apply_test_settings()
    now = datetime.now(UTC)
    user = User(
        id=uuid4(),
        email="agent@example.com",
        full_name="Agent User",
        google_sub="google-agent",
        role=UserRole.USER,
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    verifier = PKCEService.generate_code_verifier()

    flow = _make_flow(jwt_service)
    mock_users = AsyncMock()
    mock_users.get_by_id = AsyncMock(return_value=user)
    flow._users = mock_users  # noqa: SLF001
    flow.exchange_mcp_authorization_code = AsyncMock(  # type: ignore[method-assign]
        return_value=AuthTokens(
            access_token="mcp.access.token",
            refresh_token="mcp.refresh.token",
            expires_in=900,
        ),
    )
    app.dependency_overrides[get_oauth_flow_service] = lambda: flow

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/mcp/token",
            data={
                "grant_type": "authorization_code",
                "code": "auth-code",
                "redirect_uri": "http://127.0.0.1:8765/callback",
                "code_verifier": verifier,
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["access_token"] == "mcp.access.token"
    assert payload["token_type"] == "bearer"


async def test_mcp_route_requires_bearer_token() -> None:
    _apply_test_settings()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/mcp", json={"jsonrpc": "2.0", "id": 1, "method": "ping"})

    assert response.status_code == 401


@pytest.fixture
async def mcp_authed_client(jwt_service: JWTService) -> AsyncIterator[AsyncClient]:
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
        full_name="MCP User",
        google_sub="google-mcp",
        role=UserRole.USER,
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    _apply_test_settings()

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
            yield client


async def test_mcp_route_accepts_valid_bearer_token(mcp_authed_client: AsyncClient) -> None:
    response = await mcp_authed_client.post(
        "/mcp",
        json={"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
    )
    assert response.status_code != 401


async def test_mcp_callback_redirects_with_authorization_code(jwt_service: JWTService) -> None:
    _apply_test_settings()
    flow = _make_flow(jwt_service)
    flow.handle_mcp_callback = AsyncMock(  # type: ignore[method-assign]
        return_value=McpAuthorizationResult(
            authorization_code="one-time-code",
            client_redirect_uri="http://127.0.0.1:8765/callback",
            client_state="agent-state",
        ),
    )
    app.dependency_overrides[get_oauth_flow_service] = lambda: flow

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/auth/mcp/callback",
            params={"code": "google-code", "state": "signed-state"},
            follow_redirects=False,
        )

    assert response.status_code == 302
    location = response.headers["location"]
    assert location.startswith("http://127.0.0.1:8765/callback?")
    assert "code=one-time-code" in location
    assert "state=agent-state" in location
