"""Directory tree REST API — thin controllers over DirectoryService."""

from __future__ import annotations

import io
import uuid
from collections.abc import Awaitable
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from knowledge_ai.core.deps import (
    get_casbin_permission_service,
    get_current_user,
    get_directory_service,
    get_download_service,
    require_directory_permission,
)
from knowledge_ai.models.directory import Directory
from knowledge_ai.models.user import User
from knowledge_ai.schemas.directory import (
    DirectoryCreate,
    DirectoryMove,
    DirectoryRead,
    DirectoryRename,
)
from knowledge_ai.schemas.permissions import DirectoryPermission
from knowledge_ai.services.casbin_permission import CasbinPermissionService
from knowledge_ai.services.directory import (
    DirectoryConflictError,
    DirectoryNotFoundError,
    DirectoryService,
    DirectoryValidationError,
)
from knowledge_ai.services.download import DownloadService

router = APIRouter(tags=["directories"])


def _to_directory_read(directory: Directory) -> DirectoryRead:
    return DirectoryRead.model_validate(directory)


async def _run_directory_op[T](awaitable: Awaitable[T]) -> T:
    """Map domain exceptions from DirectoryService to HTTP errors."""
    try:
        return await awaitable
    except DirectoryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except DirectoryConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except DirectoryValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


async def _require_directory_permissions(
    *,
    user: User,
    perm_service: CasbinPermissionService,
    directory_ids: list[uuid.UUID],
    permission: DirectoryPermission,
) -> None:
    """Raise 403 unless the user has ``permission`` on every directory id."""
    for directory_id in directory_ids:
        allowed = await perm_service.check_directory_permission(
            user,
            directory_id,
            permission,
        )
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Directory {permission.value} permission required",
            )


async def _require_project_tree_read(
    project_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    directory_service: Annotated[DirectoryService, Depends(get_directory_service)],
    perm_service: Annotated[CasbinPermissionService, Depends(get_casbin_permission_service)],
) -> User:
    """Require READ on the project root before listing the full tree."""
    root = await directory_service.get_root_for_project(project_id)
    if root is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} has no root directory",
        )
    await _require_directory_permissions(
        user=user,
        perm_service=perm_service,
        directory_ids=[root.id],
        permission=DirectoryPermission.READ,
    )
    return user


@router.get(
    "/projects/{project_id}/directories/tree",
    response_model=list[DirectoryRead],
)
async def list_project_directory_tree(
    project_id: uuid.UUID,
    _user: Annotated[User, Depends(_require_project_tree_read)],
    directory_service: Annotated[DirectoryService, Depends(get_directory_service)],
) -> list[DirectoryRead]:
    """Return a flat directory list for the project (build tree client-side via parent_id)."""
    directories = await directory_service.list_by_project(project_id)
    return [_to_directory_read(directory) for directory in directories]


@router.get(
    "/directories/{directory_id}/children",
    response_model=list[DirectoryRead],
)
async def list_directory_children(
    directory_id: uuid.UUID,
    _user: Annotated[User, Depends(require_directory_permission(DirectoryPermission.READ))],
    directory_service: Annotated[DirectoryService, Depends(get_directory_service)],
) -> list[DirectoryRead]:
    """Return immediate child directories ordered by name."""
    await _run_directory_op(directory_service.require_by_id(directory_id))
    children = await directory_service.list_children(directory_id)
    return [_to_directory_read(child) for child in children]


@router.get(
    "/directories/{directory_id}/breadcrumbs",
    response_model=list[DirectoryRead],
)
async def list_directory_breadcrumbs(
    directory_id: uuid.UUID,
    _user: Annotated[User, Depends(require_directory_permission(DirectoryPermission.READ))],
    directory_service: Annotated[DirectoryService, Depends(get_directory_service)],
) -> list[DirectoryRead]:
    """Return ancestors from project root through the target directory."""
    chain = await _run_directory_op(directory_service.get_breadcrumb_chain(directory_id))
    return [_to_directory_read(directory) for directory in chain]


@router.post(
    "/directories/{directory_id}/children",
    response_model=DirectoryRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_directory_child(
    directory_id: uuid.UUID,
    body: DirectoryCreate,
    _user: Annotated[User, Depends(require_directory_permission(DirectoryPermission.WRITE))],
    directory_service: Annotated[DirectoryService, Depends(get_directory_service)],
) -> DirectoryRead:
    """Create a child directory under ``directory_id`` (the parent)."""
    parent = await _run_directory_op(directory_service.require_by_id(directory_id))
    created = await _run_directory_op(
        directory_service.create(
            project_id=parent.project_id,
            parent_id=directory_id,
            name=body.name,
        ),
    )
    return _to_directory_read(created)


@router.patch(
    "/directories/{directory_id}",
    response_model=DirectoryRead,
)
async def rename_directory(
    directory_id: uuid.UUID,
    body: DirectoryRename,
    _user: Annotated[User, Depends(require_directory_permission(DirectoryPermission.WRITE))],
    directory_service: Annotated[DirectoryService, Depends(get_directory_service)],
) -> DirectoryRead:
    """Rename a directory in place."""
    renamed = await _run_directory_op(
        directory_service.rename(directory_id, name=body.name),
    )
    return _to_directory_read(renamed)


@router.patch(
    "/directories/{directory_id}/move",
    response_model=DirectoryRead,
)
async def move_directory(
    directory_id: uuid.UUID,
    body: DirectoryMove,
    user: Annotated[User, Depends(get_current_user)],
    directory_service: Annotated[DirectoryService, Depends(get_directory_service)],
    perm_service: Annotated[CasbinPermissionService, Depends(get_casbin_permission_service)],
) -> DirectoryRead:
    """Move a directory under a new parent within the same project."""
    await _require_directory_permissions(
        user=user,
        perm_service=perm_service,
        directory_ids=[directory_id, body.new_parent_id],
        permission=DirectoryPermission.WRITE,
    )
    moved = await _run_directory_op(
        directory_service.move(directory_id, new_parent_id=body.new_parent_id),
    )
    return _to_directory_read(moved)


@router.delete(
    "/directories/{directory_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_directory(
    directory_id: uuid.UUID,
    _user: Annotated[User, Depends(require_directory_permission(DirectoryPermission.MANAGE))],
    directory_service: Annotated[DirectoryService, Depends(get_directory_service)],
) -> None:
    """Delete a directory and its subtree (root cannot be deleted)."""
    await _run_directory_op(directory_service.delete(directory_id))


@router.get("/directories/{directory_id}/download")
async def download_directory_subtree(
    directory_id: uuid.UUID,
    _user: Annotated[User, Depends(require_directory_permission(DirectoryPermission.READ))],
    download_service: Annotated[DownloadService, Depends(get_download_service)],
) -> StreamingResponse:
    """Download the directory subtree as a ZIP archive."""
    try:
        zip_bytes, filename = await download_service.build_subtree_zip(directory_id)
    except DirectoryNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return StreamingResponse(
        io.BytesIO(zip_bytes),
        media_type="application/zip",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
