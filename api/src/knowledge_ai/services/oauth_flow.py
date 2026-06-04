"""Orchestrates Google OAuth login, callback, and SPA token handoff."""

from dataclasses import dataclass
from typing import Any
from urllib.parse import urlencode

from knowledge_ai.models.user import User
from knowledge_ai.services.jwt import JWTService
from knowledge_ai.services.oauth import OAuthService
from knowledge_ai.services.user import UserService


@dataclass(frozen=True)
class AuthTokens:
    """Access and refresh tokens issued after successful login."""

    access_token: str
    refresh_token: str
    expires_in: int


class OAuthFlowService:
    """SPA Google OAuth: login redirect and callback token issuance."""

    def __init__(
        self,
        oauth_service: OAuthService,
        jwt_service: JWTService,
        user_service: UserService,
        *,
        allowed_redirect_origins: list[str],
    ) -> None:
        self._oauth = oauth_service
        self._jwt = jwt_service
        self._users = user_service
        self._allowed_redirect_origins = allowed_redirect_origins

    @property
    def default_redirect_uri(self) -> str:
        """First allowed SPA callback, used when OAuth state cannot be decoded."""
        return self._allowed_redirect_origins[0]

    def validate_redirect_uri(self, redirect_uri: str) -> None:
        """Ensure the SPA callback URL is explicitly allowed."""
        if redirect_uri not in self._allowed_redirect_origins:
            msg = "redirect_uri is not allowed"
            raise ValueError(msg)

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
        return await self._users.upsert_from_google(
            google_sub=google_sub,
            email=email,
            full_name=full_name,
        )
