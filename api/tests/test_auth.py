"""Tests for authentication HTTP endpoints."""

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
from knowledge_ai.services.oauth_flow import AuthTokens, OAuthFlowService

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


@pytest.fixture
def test_user() -> User:
    now = datetime.now(UTC)
    return User(
        id=uuid4(),
        email="user@example.com",
        full_name="Test User",
        google_sub="google-sub-123",
        role=UserRole.USER,
        is_active=True,
        created_at=now,
        updated_at=now,
    )


@pytest.fixture
async def authed_client(jwt_service: JWTService, test_user: User) -> AsyncIterator[AsyncClient]:
    token, _ = jwt_service.create_access_token(
        user_id=test_user.id,
        email=test_user.email,
        role=test_user.role.value,
    )

    async def override_get_current_user() -> User:
        return test_user

    _apply_test_settings()

    from knowledge_ai.core.deps import get_current_user

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


async def test_google_login_rejects_disallowed_redirect_uri() -> None:
    _apply_test_settings()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/auth/google/login",
            params={"redirect_uri": "http://evil.example/callback"},
            follow_redirects=False,
        )

    assert response.status_code == 400


async def test_google_login_redirects_to_google() -> None:
    _apply_test_settings()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/auth/google/login",
            params={"redirect_uri": "http://localhost:5173/auth/callback"},
            follow_redirects=False,
        )

    assert response.status_code == 302
    location = response.headers["location"]
    assert "accounts.google.com" in location
    assert "client_id=test-client-id" in location


async def test_refresh_requires_cookie() -> None:
    _apply_test_settings()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/auth/refresh")

    assert response.status_code == 401


async def test_refresh_returns_access_token(
    jwt_service: JWTService,
    test_user: User,
) -> None:
    _apply_test_settings()

    refresh = jwt_service.create_refresh_token(user_id=test_user.id)

    with patch(
        "knowledge_ai.api.v1.auth.UserService.get_by_id",
        new_callable=AsyncMock,
        return_value=test_user,
    ):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/refresh",
                cookies={TEST_SETTINGS.refresh_cookie_name: refresh},
            )

    assert response.status_code == 200
    payload = response.json()
    assert "access_token" in payload
    assert payload["token_type"] == "bearer"


async def test_me_requires_authentication() -> None:
    _apply_test_settings()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/api/v1/auth/me")

    assert response.status_code == 401


async def test_me_returns_user(authed_client: AsyncClient, test_user: User) -> None:
    response = await authed_client.get("/api/v1/auth/me")

    assert response.status_code == 200
    payload = response.json()
    assert payload["email"] == test_user.email
    assert payload["role"] == test_user.role.value


async def test_logout_clears_refresh_cookie() -> None:
    _apply_test_settings()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.post("/api/v1/auth/logout")

    assert response.status_code == 204
    set_cookie = response.headers.get("set-cookie", "")
    assert TEST_SETTINGS.refresh_cookie_name in set_cookie


async def test_callback_redirects_with_token_fragment(
    jwt_service: JWTService,
) -> None:
    _apply_test_settings()

    redirect_uri = "http://localhost:5173/auth/callback"
    state = jwt_service.create_oauth_state(redirect_uri=redirect_uri)
    tokens = AuthTokens(
        access_token="access.jwt.here",
        refresh_token="refresh.jwt.here",
        expires_in=900,
    )

    mock_flow = AsyncMock(spec=OAuthFlowService)
    mock_flow.handle_callback = AsyncMock(return_value=(tokens, redirect_uri))
    mock_flow.default_redirect_uri = redirect_uri

    app.dependency_overrides[get_oauth_flow_service] = lambda: mock_flow

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/auth/google/callback",
            params={"code": "auth-code", "state": state},
            follow_redirects=False,
        )

    assert response.status_code == 302
    assert response.headers["location"] == f"{redirect_uri}#token=access.jwt.here"
    assert TEST_SETTINGS.refresh_cookie_name in response.headers.get("set-cookie", "")


async def test_callback_invalid_state_redirects_with_error(
    jwt_service: JWTService,
) -> None:
    _apply_test_settings()

    mock_flow = OAuthFlowService(
        AsyncMock(),
        jwt_service,
        AsyncMock(),
        allowed_redirect_origins=TEST_SETTINGS.cors_origins,
    )
    app.dependency_overrides[get_oauth_flow_service] = lambda: mock_flow

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/auth/google/callback",
            params={"code": "auth-code", "state": "not-a-valid-state"},
            follow_redirects=False,
        )

    assert response.status_code == 302
    assert "#error=auth_failed" in response.headers["location"]
