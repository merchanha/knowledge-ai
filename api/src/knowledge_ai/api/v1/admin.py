"""Admin-only controllers (application-wide role gate)."""

import uuid
from collections.abc import Awaitable
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from knowledge_ai.core.deps import (
    get_casbin_permission_service,
    get_user_service,
    require_admin,
)
from knowledge_ai.models.user import User
from knowledge_ai.schemas.auth import UserResponse, UserUpdate
from knowledge_ai.services.casbin_permission import CasbinPermissionService
from knowledge_ai.services.user import UserNotFoundError, UserService

router = APIRouter(prefix="/admin", tags=["admin"])


async def _run_user_op[T](awaitable: Awaitable[T]) -> T:
    """Map domain exceptions from UserService to HTTP errors."""
    try:
        return await awaitable
    except UserNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    _admin: Annotated[User, Depends(require_admin)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> list[UserResponse]:
    """List all users (admin only)."""
    users = await user_service.list_all()
    return [UserResponse.model_validate(user) for user in users]


@router.patch("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: uuid.UUID,
    body: UserUpdate,
    _admin: Annotated[User, Depends(require_admin)],
    user_service: Annotated[UserService, Depends(get_user_service)],
    perm_service: Annotated[CasbinPermissionService, Depends(get_casbin_permission_service)],
) -> UserResponse:
    """Update application-wide role or active status (admin only)."""
    updated = await _run_user_op(
        user_service.update(
            user_id,
            role=body.role,
            is_active=body.is_active,
        ),
    )
    if body.role is not None:
        await perm_service.sync_user_role(updated)
    return UserResponse.model_validate(updated)
