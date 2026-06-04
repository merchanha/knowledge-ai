"""FastAPI dependencies for authentication and services."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt.exceptions import InvalidTokenError
from sqlalchemy.ext.asyncio import AsyncSession

from knowledge_ai.core.config import Settings, get_settings
from knowledge_ai.core.database import get_db
from knowledge_ai.models.user import User
from knowledge_ai.services.jwt import JWTService
from knowledge_ai.services.oauth import OAuthService
from knowledge_ai.services.oauth_flow import OAuthFlowService
from knowledge_ai.services.user import UserService

_bearer_scheme = HTTPBearer(auto_error=False)


def get_jwt_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> JWTService:
    """JWT service for the current request settings."""
    return JWTService(settings)


def get_oauth_service(
    settings: Annotated[Settings, Depends(get_settings)],
) -> OAuthService:
    """Google OAuth client for the current request settings."""
    return OAuthService(settings)


def get_user_service(session: Annotated[AsyncSession, Depends(get_db)]) -> UserService:
    """User service bound to the request database session."""
    return UserService(session)


def get_oauth_flow_service(
    session: Annotated[AsyncSession, Depends(get_db)],
    settings: Annotated[Settings, Depends(get_settings)],
    oauth_service: Annotated[OAuthService, Depends(get_oauth_service)],
    jwt_service: Annotated[JWTService, Depends(get_jwt_service)],
) -> OAuthFlowService:
    """OAuth flow orchestrator for the current request."""
    return OAuthFlowService(
        oauth_service,
        jwt_service,
        UserService(session),
        allowed_redirect_origins=settings.cors_origins,
    )


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer_scheme)],
    session: Annotated[AsyncSession, Depends(get_db)],
    jwt_service: Annotated[JWTService, Depends(get_jwt_service)],
) -> User:
    """Require a valid Bearer access token and return the active user."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        claims = jwt_service.verify_access_token(credentials.credentials)
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = await UserService(session).get_by_id(claims.user_id)
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user
