"""Command REST API — thin controllers over CommandService."""

from __future__ import annotations

import uuid
from collections.abc import Awaitable
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from knowledge_ai.core.deps import (
    get_casbin_permission_service,
    get_command_service,
    get_current_user,
    require_directory_permission,
)
from knowledge_ai.models.command import Command
from knowledge_ai.models.user import User
from knowledge_ai.schemas.command import CommandCreate, CommandRead, CommandUpdate
from knowledge_ai.schemas.permissions import DirectoryPermission
from knowledge_ai.services.casbin_permission import CasbinPermissionService
from knowledge_ai.services.command import (
    CommandNotFoundError,
    CommandService,
    CommandValidationError,
)

router = APIRouter(tags=["commands"])


def _to_command_read(command: Command) -> CommandRead:
    return CommandRead(
        id=command.id,
        directory_id=command.directory_id,
        title=command.title,
        content=command.content,
        metadata=command.metadata_json,
    )


async def _run_command_op[T](awaitable: Awaitable[T]) -> T:
    """Map domain exceptions from CommandService to HTTP errors."""
    try:
        return await awaitable
    except CommandNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except CommandValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


async def _require_command_directory_permission(
    *,
    command_id: uuid.UUID,
    permission: DirectoryPermission,
    user: User,
    command_service: CommandService,
    perm_service: CasbinPermissionService,
) -> Command:
    """Load a command and require ``permission`` on its parent directory."""
    command = await _run_command_op(command_service.require_by_id(command_id))
    allowed = await perm_service.check_directory_permission(
        user,
        command.directory_id,
        permission,
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Directory {permission.value} permission required",
        )
    return command


@router.get(
    "/directories/{directory_id}/commands",
    response_model=list[CommandRead],
)
async def list_directory_commands(
    directory_id: uuid.UUID,
    _user: Annotated[User, Depends(require_directory_permission(DirectoryPermission.READ))],
    command_service: Annotated[CommandService, Depends(get_command_service)],
) -> list[CommandRead]:
    """List Commands stored in a directory."""
    commands = await _run_command_op(command_service.list_by_directory(directory_id))
    return [_to_command_read(command) for command in commands]


@router.get(
    "/commands/{command_id}",
    response_model=CommandRead,
)
async def get_command(
    command_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    command_service: Annotated[CommandService, Depends(get_command_service)],
    perm_service: Annotated[CasbinPermissionService, Depends(get_casbin_permission_service)],
) -> CommandRead:
    """Return a single Command."""
    command = await _require_command_directory_permission(
        command_id=command_id,
        permission=DirectoryPermission.READ,
        user=user,
        command_service=command_service,
        perm_service=perm_service,
    )
    return _to_command_read(command)


@router.post(
    "/directories/{directory_id}/commands",
    response_model=CommandRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_command(
    directory_id: uuid.UUID,
    body: CommandCreate,
    _user: Annotated[User, Depends(require_directory_permission(DirectoryPermission.WRITE))],
    command_service: Annotated[CommandService, Depends(get_command_service)],
) -> CommandRead:
    """Create a Command inside a directory."""
    created = await _run_command_op(
        command_service.create(
            directory_id=directory_id,
            title=body.title,
            content=body.content,
            metadata=body.metadata,
        ),
    )
    return _to_command_read(created)


@router.patch(
    "/commands/{command_id}",
    response_model=CommandRead,
)
async def update_command(
    command_id: uuid.UUID,
    body: CommandUpdate,
    user: Annotated[User, Depends(get_current_user)],
    command_service: Annotated[CommandService, Depends(get_command_service)],
    perm_service: Annotated[CasbinPermissionService, Depends(get_casbin_permission_service)],
) -> CommandRead:
    """Update a Command."""
    await _require_command_directory_permission(
        command_id=command_id,
        permission=DirectoryPermission.WRITE,
        user=user,
        command_service=command_service,
        perm_service=perm_service,
    )
    updated = await _run_command_op(
        command_service.update(
            command_id,
            title=body.title,
            content=body.content,
            metadata=body.metadata,
        ),
    )
    return _to_command_read(updated)


@router.delete(
    "/commands/{command_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_command(
    command_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    command_service: Annotated[CommandService, Depends(get_command_service)],
    perm_service: Annotated[CasbinPermissionService, Depends(get_casbin_permission_service)],
) -> None:
    """Delete a Command."""
    await _require_command_directory_permission(
        command_id=command_id,
        permission=DirectoryPermission.MANAGE,
        user=user,
        command_service=command_service,
        perm_service=perm_service,
    )
    await _run_command_op(command_service.delete(command_id))
