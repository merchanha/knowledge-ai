"""JWT creation and verification for access, refresh, and OAuth state."""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any
from uuid import UUID, uuid4

import jwt
from jwt.exceptions import InvalidTokenError
from redis.asyncio import Redis

from knowledge_ai.core.config import Settings
from knowledge_ai.core.redis import get_redis

logger = logging.getLogger(__name__)

JWT_BLACKLIST_PREFIX = "jwt:blacklist:"


class TokenKind(StrEnum):
    """Discriminator stored in JWT ``type`` claim."""

    ACCESS = "access"
    REFRESH = "refresh"
    OAUTH_STATE = "oauth_state"
    MCP_OAUTH_STATE = "mcp_oauth_state"


@dataclass(frozen=True)
class AccessTokenClaims:
    """Verified access token payload."""

    user_id: UUID
    email: str
    role: str
    jti: str


@dataclass(frozen=True)
class OAuthStateClaims:
    """Verified OAuth state payload."""

    redirect_uri: str


@dataclass(frozen=True)
class McpOAuthStateClaims:
    """Verified MCP agent OAuth state binding PKCE to the client redirect."""

    client_redirect_uri: str
    code_challenge: str
    code_challenge_method: str
    client_state: str | None


class JWTService:
    """Issue and verify HS256 tokens for SPA authentication."""

    def __init__(self, settings: Settings, redis: Redis | None = None) -> None:
        self._secret = settings.jwt_secret_key
        self._algorithm = settings.jwt_algorithm
        self._access_expire = timedelta(minutes=settings.jwt_access_token_expire_minutes)
        self._refresh_expire = timedelta(days=settings.jwt_refresh_token_expire_days)
        self._state_expire = timedelta(minutes=settings.oauth_state_expire_minutes)
        self._redis = redis

    def _client(self) -> Redis:
        return self._redis if self._redis is not None else get_redis()

    def create_access_token(self, *, user_id: UUID, email: str, role: str) -> tuple[str, int]:
        """Return encoded access JWT and lifetime in seconds."""
        expires_in = int(self._access_expire.total_seconds())
        payload = {
            "sub": str(user_id),
            "email": email,
            "role": role,
            "type": TokenKind.ACCESS,
            "jti": str(uuid4()),
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
        """Decode and validate a Bearer access token (sync; blacklist checked separately)."""
        payload = self._decode(token, expected_type=TokenKind.ACCESS)
        sub = payload.get("sub")
        email = payload.get("email")
        role = payload.get("role")
        jti = payload.get("jti")
        if not isinstance(sub, str) or not isinstance(email, str) or not isinstance(role, str):
            raise InvalidTokenError("Invalid access token claims")
        if not isinstance(jti, str) or not jti:
            raise InvalidTokenError("Invalid access token claims")
        return AccessTokenClaims(user_id=UUID(sub), email=email, role=role, jti=jti)

    async def is_access_token_revoked(self, jti: str) -> bool:
        """Return True when ``jti`` is present in the Redis blacklist."""
        try:
            return bool(await self._client().exists(f"{JWT_BLACKLIST_PREFIX}{jti}"))
        except Exception:
            logger.exception("JWT blacklist lookup failed; treating token as valid")
            return False

    async def revoke_access_token(self, token: str) -> bool:
        """
        Blacklist an access token's ``jti`` until its natural expiry.

        Decodes without enforcing ``exp`` so near-expired tokens can still be revoked.
        Returns True when a blacklist entry was written.
        """
        try:
            payload = jwt.decode(
                token,
                self._secret,
                algorithms=[self._algorithm],
                options={"verify_exp": False},
            )
        except InvalidTokenError:
            return False

        if payload.get("type") != TokenKind.ACCESS:
            return False
        jti = payload.get("jti")
        if not isinstance(jti, str) or not jti:
            return False

        exp = payload.get("exp")
        if isinstance(exp, int | float):
            ttl = max(int(exp - time.time()), 1)
        else:
            ttl = int(self._access_expire.total_seconds())

        try:
            await self._client().set(f"{JWT_BLACKLIST_PREFIX}{jti}", "1", ex=ttl)
        except Exception:
            logger.exception("Failed to write JWT blacklist entry")
            return False
        return True

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

    def create_mcp_oauth_state(
        self,
        *,
        client_redirect_uri: str,
        code_challenge: str,
        code_challenge_method: str,
        client_state: str | None,
    ) -> str:
        """Return signed state for the MCP agent OAuth round-trip."""
        payload = {
            "client_redirect_uri": client_redirect_uri,
            "code_challenge": code_challenge,
            "code_challenge_method": code_challenge_method,
            "client_state": client_state,
            "type": TokenKind.MCP_OAUTH_STATE,
            "exp": datetime.now(UTC) + self._state_expire,
            "iat": datetime.now(UTC),
        }
        return jwt.encode(payload, self._secret, algorithm=self._algorithm)

    def verify_mcp_oauth_state(self, token: str) -> McpOAuthStateClaims:
        """Decode and validate MCP agent OAuth state."""
        payload = self._decode(token, expected_type=TokenKind.MCP_OAUTH_STATE)
        client_redirect_uri = payload.get("client_redirect_uri")
        code_challenge = payload.get("code_challenge")
        code_challenge_method = payload.get("code_challenge_method")
        client_state = payload.get("client_state")
        if not isinstance(client_redirect_uri, str) or not isinstance(code_challenge, str):
            raise InvalidTokenError("Invalid MCP OAuth state claims")
        if not isinstance(code_challenge_method, str):
            raise InvalidTokenError("Invalid MCP OAuth state claims")
        if client_state is not None and not isinstance(client_state, str):
            raise InvalidTokenError("Invalid MCP OAuth state claims")
        return McpOAuthStateClaims(
            client_redirect_uri=client_redirect_uri,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            client_state=client_state,
        )

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
