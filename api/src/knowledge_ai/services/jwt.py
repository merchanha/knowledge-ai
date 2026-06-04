"""JWT creation and verification for access, refresh, and OAuth state."""

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any
from uuid import UUID

import jwt
from jwt.exceptions import InvalidTokenError

from knowledge_ai.core.config import Settings


class TokenKind(StrEnum):
    """Discriminator stored in JWT ``type`` claim."""

    ACCESS = "access"
    REFRESH = "refresh"
    OAUTH_STATE = "oauth_state"


@dataclass(frozen=True)
class AccessTokenClaims:
    """Verified access token payload."""

    user_id: UUID
    email: str
    role: str


@dataclass(frozen=True)
class OAuthStateClaims:
    """Verified OAuth state payload."""

    redirect_uri: str


class JWTService:
    """Issue and verify HS256 tokens for SPA authentication."""

    def __init__(self, settings: Settings) -> None:
        self._secret = settings.jwt_secret_key
        self._algorithm = settings.jwt_algorithm
        self._access_expire = timedelta(minutes=settings.jwt_access_token_expire_minutes)
        self._refresh_expire = timedelta(days=settings.jwt_refresh_token_expire_days)
        self._state_expire = timedelta(minutes=settings.oauth_state_expire_minutes)

    def create_access_token(self, *, user_id: UUID, email: str, role: str) -> tuple[str, int]:
        """Return encoded access JWT and lifetime in seconds."""
        expires_in = int(self._access_expire.total_seconds())
        payload = {
            "sub": str(user_id),
            "email": email,
            "role": role,
            "type": TokenKind.ACCESS,
            "exp": datetime.now(UTC) + self._access_expire,
            "iat": datetime.now(UTC),
        }
        token = jwt.encode(payload, self._secret, algorithm=self._algorithm)
        return token, expires_in

    def create_refresh_token(self, *, user_id: UUID) -> str:
        """Return encoded refresh JWT for httpOnly cookie storage."""
        payload = {
            "sub": str(user_id),
            "type": TokenKind.REFRESH,
            "exp": datetime.now(UTC) + self._refresh_expire,
            "iat": datetime.now(UTC),
        }
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def create_oauth_state(self, *, redirect_uri: str) -> str:
        """Return signed state binding the Google round-trip to the SPA callback."""
        payload = {
            "redirect_uri": redirect_uri,
            "type": TokenKind.OAUTH_STATE,
            "exp": datetime.now(UTC) + self._state_expire,
            "iat": datetime.now(UTC),
        }
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def verify_access_token(self, token: str) -> AccessTokenClaims:
        """Decode and validate a Bearer access token."""
        payload = self._decode(token, expected_type=TokenKind.ACCESS)
        sub = payload.get("sub")
        email = payload.get("email")
        role = payload.get("role")
        if not isinstance(sub, str) or not isinstance(email, str) or not isinstance(role, str):
            raise InvalidTokenError("Invalid access token claims")
        return AccessTokenClaims(user_id=UUID(sub), email=email, role=role)

    def verify_refresh_token(self, token: str) -> UUID:
        """Decode and validate a refresh token; return user id."""
        payload = self._decode(token, expected_type=TokenKind.REFRESH)
        sub = payload.get("sub")
        if not isinstance(sub, str):
            raise InvalidTokenError("Invalid refresh token claims")
        return UUID(sub)

    def verify_oauth_state(self, token: str) -> OAuthStateClaims:
        """Decode and validate OAuth CSRF state."""
        payload = self._decode(token, expected_type=TokenKind.OAUTH_STATE)
        redirect_uri = payload.get("redirect_uri")
        if not isinstance(redirect_uri, str):
            raise InvalidTokenError("Invalid OAuth state claims")
        return OAuthStateClaims(redirect_uri=redirect_uri)

    def _decode(self, token: str, *, expected_type: TokenKind) -> dict[str, Any]:
        try:
            payload = jwt.decode(
                token,
                self._secret,
                algorithms=[self._algorithm],
            )
        except InvalidTokenError:
            raise
        token_type = payload.get("type")
        if token_type != expected_type:
            raise InvalidTokenError("Unexpected token type")
        return payload
