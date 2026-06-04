"""Tests for JWTService."""

from datetime import UTC, datetime, timedelta
from uuid import uuid4

import jwt
import pytest
from jwt.exceptions import InvalidTokenError

from knowledge_ai.core.config import Settings
from knowledge_ai.services.jwt import JWTService, TokenKind


@pytest.fixture
def jwt_settings() -> Settings:
    return Settings(
        jwt_secret_key="test-secret-key-at-least-32-chars-long",
        jwt_access_token_expire_minutes=15,
        jwt_refresh_token_expire_days=7,
        oauth_state_expire_minutes=10,
    )


@pytest.fixture
def jwt_service(jwt_settings: Settings) -> JWTService:
    return JWTService(jwt_settings)


def test_create_and_verify_access_token(jwt_service: JWTService) -> None:
    user_id = uuid4()
    token, expires_in = jwt_service.create_access_token(
        user_id=user_id,
        email="user@example.com",
        role="user",
    )

    assert expires_in == 15 * 60
    claims = jwt_service.verify_access_token(token)
    assert claims.user_id == user_id
    assert claims.email == "user@example.com"
    assert claims.role == "user"


def test_create_and_verify_refresh_token(jwt_service: JWTService) -> None:
    user_id = uuid4()
    token = jwt_service.create_refresh_token(user_id=user_id)

    assert jwt_service.verify_refresh_token(token) == user_id


def test_create_and_verify_oauth_state(jwt_service: JWTService) -> None:
    token = jwt_service.create_oauth_state(
        redirect_uri="http://localhost:5173/auth/callback",
    )
    claims = jwt_service.verify_oauth_state(token)
    assert claims.redirect_uri == "http://localhost:5173/auth/callback"


def test_rejects_wrong_token_type(jwt_service: JWTService, jwt_settings: Settings) -> None:
    payload = {
        "sub": str(uuid4()),
        "type": TokenKind.REFRESH,
        "exp": datetime.now(UTC) + timedelta(hours=1),
        "iat": datetime.now(UTC),
    }
    token = jwt.encode(payload, jwt_settings.jwt_secret_key, algorithm="HS256")

    with pytest.raises(InvalidTokenError):
        jwt_service.verify_access_token(token)
