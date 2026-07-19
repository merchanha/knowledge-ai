"""Google OAuth 2.0 client (authorization code flow)."""

from typing import Any

from authlib.integrations.httpx_client import AsyncOAuth2Client

from knowledge_ai.core.config import Settings

GOOGLE_AUTHORIZE_URL = "https://accounts.google.com/o/oauth2/v2/auth"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://openidconnect.googleapis.com/v1/userinfo"
GOOGLE_SCOPES = "openid email profile"


class OAuthService:
    """Low-level Google OAuth HTTP operations via Authlib."""

    def __init__(self, settings: Settings) -> None:
        self._client_id = settings.google_client_id
        self._client_secret = settings.google_client_secret
        self._redirect_uri = settings.google_redirect_uri

    def create_authorization_url(
        self,
        *,
        state: str,
        redirect_uri: str | None = None,
    ) -> str:
        """Build the Google consent screen URL."""
        callback_uri = redirect_uri or self._redirect_uri
        client = AsyncOAuth2Client(
            client_id=self._client_id,
            client_secret=self._client_secret,
            redirect_uri=callback_uri,
            scope=GOOGLE_SCOPES,
        )
        uri, _ = client.create_authorization_url(
            GOOGLE_AUTHORIZE_URL,
            state=state,
            access_type="online",
            prompt="select_account",
        )
        return str(uri)

    async def exchange_code(
        self,
        code: str,
        *,
        redirect_uri: str | None = None,
    ) -> dict[str, Any]:
        """Trade authorization code for Google token response."""
        callback_uri = redirect_uri or self._redirect_uri
        async with AsyncOAuth2Client(
            client_id=self._client_id,
            client_secret=self._client_secret,
            redirect_uri=callback_uri,
        ) as client:
            token: dict[str, Any] = await client.fetch_token(GOOGLE_TOKEN_URL, code=code)
            return token

    async def fetch_userinfo(self, token: dict[str, Any]) -> dict[str, Any]:
        """Return OpenID userinfo for a Google access token."""
        async with AsyncOAuth2Client(
            client_id=self._client_id,
            client_secret=self._client_secret,
            token=token,
        ) as client:
            response = await client.get(GOOGLE_USERINFO_URL)
            response.raise_for_status()
            data: dict[str, Any] = response.json()
            return data
