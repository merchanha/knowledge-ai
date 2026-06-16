"""Directory permission management (Casbin-backed)."""

import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from knowledge_ai.core.deps import (
    get_casbin_permission_service,
    get_current_user,
    get_directory_service,
    require_admin,
)
from knowledge_ai.models.user import User
from knowledge_ai.schemas.permissions import (
    DirectoryPermissionEntry,
    GrantDirectoryPermissionRequest,
    RevokeDirectoryPermissionRequest,
    UserDirectoryPermissionsResponse,
)
from knowledge_ai.services.casbin_permission import CasbinPermissionService
from knowledge_ai.services.directory import DirectoryService

router = APIRouter(prefix="/permissions", tags=["permissions"])


@router.get("/me", response_model=UserDirectoryPermissionsResponse)
async def list_my_directory_permissions(
    user: Annotated[User, Depends(get_current_user)],
    perm_service: Annotated[CasbinPermissionService, Depends(get_casbin_permission_service)],
) -> UserDirectoryPermissionsResponse:
    """Return directory grants for the authenticated user."""
    rows = await perm_service.list_directory_permissions_for_user(user.id)
    permissions = [
        DirectoryPermissionEntry(directory_id=directory_id, permission=permission)
        for directory_id, permission in rows
    ]
    return UserDirectoryPermissionsResponse(permissions=permissions)


@router.post(
    "/directories/{directory_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def grant_directory_permission(
    directory_id: uuid.UUID,
    body: GrantDirectoryPermissionRequest,
    _admin: Annotated[User, Depends(require_admin)],
    directory_service: Annotated[DirectoryService, Depends(get_directory_service)],
    perm_service: Annotated[CasbinPermissionService, Depends(get_casbin_permission_service)],
) -> None:
    """Grant a user access to a directory (admin only)."""
    if await directory_service.get_by_id(directory_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Directory {directory_id} not found",
        )
    added = await perm_service.grant_directory_permission(
        user_id=body.user_id,
        directory_id=directory_id,
        permission=body.permission,
    )
    if not added:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Permission already granted",
        )


@router.delete(
    "/directories/{directory_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def revoke_directory_permission(
    directory_id: uuid.UUID,
    body: RevokeDirectoryPermissionRequest,
    _admin: Annotated[User, Depends(require_admin)],
    directory_service: Annotated[DirectoryService, Depends(get_directory_service)],
    perm_service: Annotated[CasbinPermissionService, Depends(get_casbin_permission_service)],
) -> None:
    """Revoke a user's directory access (admin only)."""
    if await directory_service.get_by_id(directory_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Directory {directory_id} not found",
        )
    removed = await perm_service.revoke_directory_permission(
        user_id=body.user_id,
        directory_id=directory_id,
        permission=body.permission,
    )
    if not removed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Permission not found",
        )
