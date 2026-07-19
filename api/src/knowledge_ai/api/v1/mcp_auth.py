"""MCP agent OAuth controllers — PKCE authorization code flow."""

from typing import Annotated

from fastapi import APIRouter, Depends, Form, HTTPException, Query, status
from fastapi.responses import RedirectResponse
from jwt.exceptions import InvalidTokenError

from knowledge_ai.core.config import Settings, get_settings
from knowledge_ai.core.deps import get_oauth_flow_service
from knowledge_ai.schemas.mcp_auth import McpTokenResponse
from knowledge_ai.services.oauth_flow import OAuthFlowService

router = APIRouter(prefix="/auth/mcp", tags=["mcp-auth"])


@router.get("/authorize")
async def mcp_authorize(
    flow: Annotated[OAuthFlowService, Depends(get_oauth_flow_service)],
    settings: Annotated[Settings, Depends(get_settings)],
    response_type: Annotated[str, Query()],
    redirect_uri: Annotated[str, Query()],
    code_challenge: Annotated[str, Query()],
    code_challenge_method: Annotated[str, Query()] = "S256",
    state: Annotated[str | None, Query()] = None,
    client_id: Annotated[str | None, Query()] = None,
) -> RedirectResponse:
    """Start Google OAuth for an MCP agent using PKCE."""
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth is not configured",
        )
    if response_type != "code":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only response_type=code is supported",
        )
    if client_id is not None and client_id != settings.mcp_client_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Unknown client_id",
        )

    try:
        authorize_url = flow.build_mcp_authorize_redirect(
            client_redirect_uri=redirect_uri,
            code_challenge=code_challenge,
            code_challenge_method=code_challenge_method,
            client_state=state,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return RedirectResponse(url=authorize_url, status_code=status.HTTP_302_FOUND)


@router.get("/callback")
async def mcp_callback(
    flow: Annotated[OAuthFlowService, Depends(get_oauth_flow_service)],
    code: Annotated[str | None, Query()] = None,
    state: Annotated[str | None, Query()] = None,
    error: Annotated[str | None, Query()] = None,
) -> RedirectResponse:
    """Google redirects here; issue an MCP authorization code to the client."""
    fallback_redirect = flow.resolve_mcp_client_redirect_from_state(state)

    if error is not None:
        return RedirectResponse(
            url=OAuthFlowService.build_mcp_client_error_redirect(
                fallback_redirect,
                error=error,
            ),
            status_code=status.HTTP_302_FOUND,
        )
    if code is None or state is None:
        return RedirectResponse(
            url=OAuthFlowService.build_mcp_client_error_redirect(
                fallback_redirect,
                error="missing_params",
            ),
            status_code=status.HTTP_302_FOUND,
        )

    try:
        result = await flow.handle_mcp_callback(code=code, state=state)
    except (ValueError, InvalidTokenError):
        return RedirectResponse(
            url=OAuthFlowService.build_mcp_client_error_redirect(
                fallback_redirect,
                error="auth_failed",
            ),
            status_code=status.HTTP_302_FOUND,
        )

    redirect_url = OAuthFlowService.build_mcp_client_redirect(
        result.client_redirect_uri,
        authorization_code=result.authorization_code,
        client_state=result.client_state,
    )
    return RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)


@router.post("/token", response_model=McpTokenResponse)
async def mcp_token(
    flow: Annotated[OAuthFlowService, Depends(get_oauth_flow_service)],
    grant_type: Annotated[str, Form()],
    code: Annotated[str, Form()],
    redirect_uri: Annotated[str, Form()],
    code_verifier: Annotated[str, Form()],
    client_id: Annotated[str | None, Form()] = None,
) -> McpTokenResponse:
    """Exchange an authorization code + PKCE verifier for JWT access tokens."""
    if grant_type != "authorization_code":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only authorization_code grant is supported",
        )

    try:
        tokens = await flow.exchange_mcp_authorization_code(
            code=code,
            redirect_uri=redirect_uri,
            code_verifier=code_verifier,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    return McpTokenResponse(
        access_token=tokens.access_token,
        expires_in=tokens.expires_in,
        refresh_token=tokens.refresh_token,
    )
