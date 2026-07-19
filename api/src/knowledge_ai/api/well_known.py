"""OAuth discovery metadata for MCP clients."""

from typing import Annotated

from fastapi import APIRouter, Depends

from knowledge_ai.core.config import Settings, get_settings
from knowledge_ai.schemas.mcp_auth import (
    OAuthAuthorizationServerMetadata,
    OAuthProtectedResourceMetadata,
)

router = APIRouter(tags=["well-known"])


@router.get(
    "/.well-known/oauth-authorization-server",
    response_model=OAuthAuthorizationServerMetadata,
)
async def oauth_authorization_server_metadata(
    settings: Annotated[Settings, Depends(get_settings)],
) -> OAuthAuthorizationServerMetadata:
    """Tell MCP clients where to authorize and exchange tokens."""
    issuer = settings.mcp_issuer_url.rstrip("/")
    return OAuthAuthorizationServerMetadata(
        issuer=issuer,
        authorization_endpoint=f"{issuer}/api/v1/auth/mcp/authorize",
        token_endpoint=f"{issuer}/api/v1/auth/mcp/token",
    )


@router.get(
    "/.well-known/oauth-protected-resource",
    response_model=OAuthProtectedResourceMetadata,
)
async def oauth_protected_resource_metadata(
    settings: Annotated[Settings, Depends(get_settings)],
) -> OAuthProtectedResourceMetadata:
    """Advertise the MCP resource server and its authorization server."""
    issuer = settings.mcp_issuer_url.rstrip("/")
    return OAuthProtectedResourceMetadata(
        resource=f"{issuer}/mcp",
        authorization_servers=[issuer],
    )
