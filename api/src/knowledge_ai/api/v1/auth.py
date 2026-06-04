"""Authentication controllers — Google OAuth and JWT refresh."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import RedirectResponse
from jwt.exceptions import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

from knowledge_ai.core.config import Settings, get_settings
from knowledge_ai.core.database import get_db
from knowledge_ai.core.deps import (
    get_current_user,
    get_jwt_service,
    get_oauth_flow_service,
)
from knowledge_ai.models.user import User
from knowledge_ai.schemas.auth import TokenResponse, UserResponse
from knowledge_ai.services.jwt import JWTService
from knowledge_ai.services.oauth_flow import OAuthFlowService
from knowledge_ai.services.user import UserService

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_refresh_cookie(response: Response, *, refresh_token: str, settings: Settings) -> None:
    max_age = settings.jwt_refresh_token_expire_days * 24 * 60 * 60
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=refresh_token,
        httponly=True,
        secure=settings.refresh_cookie_secure,
        samesite=settings.refresh_cookie_samesite,
        path=settings.refresh_cookie_path,
        max_age=max_age,
    )


def _clear_refresh_cookie(response: Response, settings: Settings) -> None:
    response.delete_cookie(
        key=settings.refresh_cookie_name,
        path=settings.refresh_cookie_path,
    )


def _spa_redirect_from_state(
    state: str | None,
    *,
    jwt_service: JWTService,
    flow: OAuthFlowService,
) -> str:
    """Best-effort SPA redirect for error paths when state may be invalid."""
    if state is None:
        return flow.default_redirect_uri
    try:
        return jwt_service.verify_oauth_state(state).redirect_uri
    except InvalidTokenError:
        return flow.default_redirect_uri


@router.get("/google/login")
async def google_login(
    redirect_uri: Annotated[str, Query(description="SPA OAuth callback URL")],
    flow: Annotated[OAuthFlowService, Depends(get_oauth_flow_service)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> RedirectResponse:
    """Redirect the browser to Google OAuth; state binds the SPA callback URL."""
    if not settings.google_client_id or not settings.google_client_secret:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Google OAuth is not configured",
        )
    try:
        authorize_url = flow.build_login_redirect(redirect_uri=redirect_uri)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    return RedirectResponse(url=authorize_url, status_code=status.HTTP_302_FOUND)


@router.get("/google/callback")
async def google_callback(
    flow: Annotated[OAuthFlowService, Depends(get_oauth_flow_service)],
    jwt_service: Annotated[JWTService, Depends(get_jwt_service)],
    settings: Annotated[Settings, Depends(get_settings)],
    code: Annotated[str | None, Query()] = None,
    state: Annotated[str | None, Query()] = None,
    error: Annotated[str | None, Query()] = None,
) -> RedirectResponse:
    """Google redirects here; issue tokens and send the SPA to redirect_uri#token=."""
    spa_redirect = _spa_redirect_from_state(state, jwt_service=jwt_service, flow=flow)

    if error is not None:
        return RedirectResponse(
            url=OAuthFlowService.build_spa_error_redirect(spa_redirect, error=error),
            status_code=status.HTTP_302_FOUND,
        )
    if code is None or state is None:
        return RedirectResponse(
            url=OAuthFlowService.build_spa_error_redirect(spa_redirect, error="missing_params"),
            status_code=status.HTTP_302_FOUND,
        )

    try:
        tokens, spa_redirect = await flow.handle_callback(code=code, state=state)
    except (ValueError, InvalidTokenError):
        return RedirectResponse(
            url=OAuthFlowService.build_spa_error_redirect(spa_redirect, error="auth_failed"),
            status_code=status.HTTP_302_FOUND,
        )

    redirect_url = OAuthFlowService.build_spa_redirect(
        spa_redirect,
        access_token=tokens.access_token,
    )
    response = RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)
    _set_refresh_cookie(response, refresh_token=tokens.refresh_token, settings=settings)
    return response


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: Request,
    jwt_service: Annotated[JWTService, Depends(get_jwt_service)],
    session: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> TokenResponse:
    """Issue a new access token using the httpOnly refresh cookie."""
    raw_refresh = request.cookies.get(settings.refresh_cookie_name)
    if raw_refresh is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token missing",
        )

    try:
        user_id = jwt_service.verify_refresh_token(raw_refresh)
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        ) from exc

    user = await UserService(session).get_by_id(user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
        )

    access_token, expires_in = jwt_service.create_access_token(
        user_id=user.id,
        email=user.email,
        role=user.role.value,
    )
    return TokenResponse(access_token=access_token, expires_in=expires_in)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    response: Response,
    settings: Annotated[Settings, Depends(get_settings)],
) -> None:
    """Clear the refresh cookie (token blacklist added in Week 22)."""
    _clear_refresh_cookie(response, settings)


@router.get("/me", response_model=UserResponse)
async def get_me(user: Annotated[User, Depends(get_current_user)]) -> UserResponse:
    """Return the authenticated user (protected route example)."""
    return UserResponse.model_validate(user)
