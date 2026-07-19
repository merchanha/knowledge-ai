"""Pydantic models for MCP agent OAuth and discovery endpoints."""

from pydantic import BaseModel, Field


class OAuthAuthorizationServerMetadata(BaseModel):
    """RFC 8414 metadata served at ``/.well-known/oauth-authorization-server``."""

    issuer: str
    authorization_endpoint: str
    token_endpoint: str
    response_types_supported: list[str] = Field(default=["code"])
    grant_types_supported: list[str] = Field(
        default=["authorization_code", "refresh_token"],
    )
    code_challenge_methods_supported: list[str] = Field(default=["S256"])
    scopes_supported: list[str] = Field(default=["openid", "email", "profile"])


class OAuthProtectedResourceMetadata(BaseModel):
    """RFC 9728 metadata for the MCP resource server."""

    resource: str
    authorization_servers: list[str]
    scopes_supported: list[str] = Field(default=["openid", "email", "profile"])


class McpTokenRequest(BaseModel):
    """Token endpoint body for the authorization_code grant."""

    grant_type: str
    code: str
    redirect_uri: str
    code_verifier: str
    client_id: str | None = None


class McpTokenResponse(BaseModel):
    """OAuth token response for MCP agents."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: str | None = None
