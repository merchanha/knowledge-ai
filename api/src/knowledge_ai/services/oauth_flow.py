"""Orchestrates Google OAuth login, callback, and SPA token handoff."""

import json
import secrets
from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode
from uuid import UUID

from knowledge_ai.core.redis import get_redis
from knowledge_ai.models.user import User
from knowledge_ai.services.casbin_permission import CasbinPermissionService
from knowledge_ai.services.jwt import JWTService
from knowledge_ai.services.oauth import OAuthService
from knowledge_ai.services.pkce import PKCEError, PKCEService
from knowledge_ai.services.user import UserService

MCP_AUTH_CODE_PREFIX = "mcp:auth_code:"


@dataclass(frozen=True)
class AuthTokens:
    """Access and refresh tokens issued after successful login."""

    access_token: str
    refresh_token: str
    expires_in: int


@dataclass(frozen=True)
class McpAuthorizationResult:
    """Authorization code handoff back to the MCP client redirect URI."""

    authorization_code: str
    client_redirect_uri: str
    client_state: str | None


class OAuthFlowService:
    """SPA Google OAuth: login redirect and callback token issuance."""

    def __init__(
        self,
        oauth_service: OAuthService,
        jwt_service: JWTService,
        user_service: UserService,
        permission_service: CasbinPermissionService,
        *,
        allowed_redirect_origins: list[str],
        mcp_google_redirect_uri: str,
        mcp_auth_code_expire_seconds: int,
    ) -> None:
        self._oauth = oauth_service
        self._jwt = jwt_service
        self._users = user_service
        self._permissions = permission_service
        self._allowed_redirect_origins = allowed_redirect_origins
        self._mcp_google_redirect_uri = mcp_google_redirect_uri
        self._mcp_auth_code_expire_seconds = mcp_auth_code_expire_seconds

    @property
    def default_redirect_uri(self) -> str:
        """First allowed SPA callback, used when OAuth state cannot be decoded."""
        return self._allowed_redirect_origins[0]

    def validate_redirect_uri(self, redirect_uri: str) -> None:
        """Ensure the SPA callback URL is explicitly allowed."""
        if redirect_uri not in self._allowed_redirect_origins:
            msg = "redirect_uri is not allowed"
            raise ValueError(msg)

    def validate_mcp_client_redirect_uri(self, redirect_uri: str) -> None:
        """Ensure the MCP client's OAuth redirect URI is allowed."""
        self.validate_redirect_uri(redirect_uri)

    def resolve_mcp_client_redirect_from_state(self, state: str | None) -> str:
        """Best-effort MCP client redirect for error paths when state may be invalid."""
        if state is None:
            return self.default_redirect_uri
        try:
            return self._jwt.verify_mcp_oauth_state(state).client_redirect_uri
        except Exception:
            return self.default_redirect_uri

    def build_login_redirect(self, *, redirect_uri: str) -> str:
        """Return Google authorization URL for the SPA callback."""
        self.validate_redirect_uri(redirect_uri)
        state = self._jwt.create_oauth_state(redirect_uri=redirect_uri)
        return self._oauth.create_authorization_url(state=state)

    async def handle_callback(self, *, code: str, state: str) -> tuple[AuthTokens, str]:
        """
        Exchange Google code, upsert user, return tokens and SPA redirect URI.

        Returns:
            (tokens, spa_redirect_uri) for the controller to set cookie + fragment redirect.
        """
        state_claims = self._jwt.verify_oauth_state(state)
        self.validate_redirect_uri(state_claims.redirect_uri)

        google_token = await self._oauth.exchange_code(code)
        profile = await self._oauth.fetch_userinfo(google_token)
        user = await self._upsert_user(profile)

        access_token, expires_in = self._jwt.create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role.value,
        )
        refresh_token = self._jwt.create_refresh_token(user_id=user.id)
        tokens = AuthTokens(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
        )
        return tokens, state_claims.redirect_uri

    def build_mcp_authorize_redirect(
        self,
        *,
        client_redirect_uri: str,
        code_challenge: str,
        code_challenge_method: str,
        client_state: str | None,
    ) -> str:
        """Return Google authorization URL for the MCP agent PKCE flow."""
        self.validate_mcp_client_redirect_uri(client_redirect_uri)
        if code_challenge_method != "S256":
            msg = "Only S256 code_challenge_method is supported"
            raise ValueError(msg)

        state = self._jwt.create_mcp_oauth_state(
            client_redirect_uri=client_redirect_uri,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            client_state=client_state,
        )
        return self._oauth.create_authorization_url(
            state=state,
            redirect_uri=self._mcp_google_redirect_uri,
        )

    async def handle_mcp_callback(
        self,
        *,
        code: str,
        state: str,
    ) -> McpAuthorizationResult:
        """Exchange Google code and issue a one-time MCP authorization code."""
        state_claims = self._jwt.verify_mcp_oauth_state(state)
        self.validate_mcp_client_redirect_uri(state_claims.client_redirect_uri)

        google_token = await self._oauth.exchange_code(
            code,
            redirect_uri=self._mcp_google_redirect_uri,
        )
        profile = await self._oauth.fetch_userinfo(google_token)
        user = await self._upsert_user(profile)

        authorization_code = secrets.token_urlsafe(32)
        payload = {
            "user_id": str(user.id),
            "code_challenge": state_claims.code_challenge,
            "code_challenge_method": state_claims.code_challenge_method,
            "client_redirect_uri": state_claims.client_redirect_uri,
        }
        redis = get_redis()
        await redis.set(
            f"{MCP_AUTH_CODE_PREFIX}{authorization_code}",
            json.dumps(payload),
            ex=self._mcp_auth_code_expire_seconds,
        )
        return McpAuthorizationResult(
            authorization_code=authorization_code,
            client_redirect_uri=state_claims.client_redirect_uri,
            client_state=state_claims.client_state,
        )

    async def exchange_mcp_authorization_code(
        self,
        *,
        code: str,
        redirect_uri: str,
        code_verifier: str,
    ) -> AuthTokens:
        """Verify PKCE and return JWT tokens for an MCP agent."""
        self.validate_mcp_client_redirect_uri(redirect_uri)

        redis = get_redis()
        raw_payload = await redis.getdel(f"{MCP_AUTH_CODE_PREFIX}{code}")
        if raw_payload is None:
            msg = "Invalid or expired authorization code"
            raise ValueError(msg)

        payload = json.loads(raw_payload)
        user_id = UUID(payload["user_id"])
        code_challenge = payload["code_challenge"]
        code_challenge_method = payload["code_challenge_method"]
        stored_redirect_uri = payload["client_redirect_uri"]

        if stored_redirect_uri != redirect_uri:
            msg = "redirect_uri does not match authorization request"
            raise ValueError(msg)

        try:
            PKCEService.verify_code_challenge(
                verifier=code_verifier,
                challenge=code_challenge,
                method=code_challenge_method,
            )
        except PKCEError as exc:
            raise ValueError(str(exc)) from exc

        user = await self._users.get_by_id(user_id)
        if user is None or not user.is_active:
            msg = "User not found or inactive"
            raise ValueError(msg)

        access_token, expires_in = self._jwt.create_access_token(
            user_id=user.id,
            email=user.email,
            role=user.role.value,
        )
        refresh_token = self._jwt.create_refresh_token(user_id=user.id)
        return AuthTokens(
            access_token=access_token,
            refresh_token=refresh_token,
            expires_in=expires_in,
        )

    @staticmethod
    def build_mcp_client_redirect(
        redirect_uri: str,
        *,
        authorization_code: str,
        client_state: str | None,
    ) -> str:
        """Build the MCP client redirect with an authorization code."""
        params: dict[str, str] = {"code": authorization_code}
        if client_state is not None:
            params["state"] = client_state
        return f"{redirect_uri}?{urlencode(params)}"

    @staticmethod
    def build_mcp_client_error_redirect(
        redirect_uri: str,
        *,
        error: str,
        client_state: str | None = None,
    ) -> str:
        """Build the MCP client redirect with an OAuth error."""
        params: dict[str, str] = {"error": error}
        if client_state is not None:
            params["state"] = client_state
        return f"{redirect_uri}?{urlencode(params)}"

    @staticmethod
    def build_spa_redirect(redirect_uri: str, *, access_token: str) -> str:
        """Build SPA callback URL with access token in the fragment."""
        fragment = urlencode({"token": access_token})
        return f"{redirect_uri}#{fragment}"

    @staticmethod
    def build_spa_error_redirect(redirect_uri: str, *, error: str) -> str:
        """Build SPA callback URL with error in the fragment."""
        fragment = urlencode({"error": error})
        return f"{redirect_uri}#{fragment}"

    async def _upsert_user(self, profile: dict[str, Any]) -> User:
        google_sub = profile.get("sub")
        email = profile.get("email")
        if not isinstance(google_sub, str) or not isinstance(email, str):
            msg = "Google profile missing sub or email"
            raise ValueError(msg)
        full_name = profile.get("name")
        if full_name is not None and not isinstance(full_name, str):
            full_name = None
        user = await self._users.upsert_from_google(
            google_sub=google_sub,
            email=email,
            full_name=full_name,
        )
        await self._permissions.sync_user_role(user)
        return user
