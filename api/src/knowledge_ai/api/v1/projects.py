"""Project and membership REST API — thin controllers over domain services."""

from __future__ import annotations

import uuid
from collections.abc import Awaitable
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from knowledge_ai.core.deps import (
    get_current_user,
    get_membership_service,
    get_project_service,
    require_admin,
    require_project_member,
    require_project_owner_or_admin,
)
from knowledge_ai.models.project import Project
from knowledge_ai.models.user import User, UserRole
from knowledge_ai.schemas.membership import MembershipCreate, MembershipRead
from knowledge_ai.schemas.project import ProjectCreate, ProjectRead, ProjectUpdate
from knowledge_ai.services.membership import (
    MembershipConflictError,
    MembershipNotFoundError,
    MembershipService,
    MembershipValidationError,
)
from knowledge_ai.services.project import (
    ProjectNotFoundError,
    ProjectService,
    ProjectValidationError,
)

router = APIRouter(tags=["projects"])


def _to_project_read(project: Project) -> ProjectRead:
    return ProjectRead.model_validate(project)


async def _run_project_op[T](awaitable: Awaitable[T]) -> T:
    """Map domain exceptions from ProjectService to HTTP errors."""
    try:
        return await awaitable
    except ProjectNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except ProjectValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


async def _run_membership_op[T](awaitable: Awaitable[T]) -> T:
    """Map domain exceptions from MembershipService to HTTP errors."""
    try:
        return await awaitable
    except MembershipNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except MembershipConflictError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc)) from exc
    except MembershipValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get("/projects", response_model=list[ProjectRead])
async def list_projects(
    user: Annotated[User, Depends(get_current_user)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
    membership_service: Annotated[MembershipService, Depends(get_membership_service)],
) -> list[ProjectRead]:
    """List projects: all for admin, member projects for regular users."""
    if user.role == UserRole.ADMIN:
        projects = await _run_project_op(project_service.list_all())
    else:
        account_projects = await membership_service.list_projects_for_user(user.id)
        projects = [entry.project for entry in account_projects]
    return [_to_project_read(project) for project in projects]


@router.post(
    "/projects",
    response_model=ProjectRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_project(
    body: ProjectCreate,
    _admin: Annotated[User, Depends(require_admin)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> ProjectRead:
    """Create a project and its root directory (admin only)."""
    created = await _run_project_op(
        project_service.create(name=body.name, description=body.description),
    )
    return _to_project_read(created)


@router.get("/projects/{project_id}", response_model=ProjectRead)
async def get_project(
    project_id: uuid.UUID,
    _member: Annotated[User, Depends(require_project_member)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> ProjectRead:
    """Return a single project (admin or member)."""
    project = await _run_project_op(project_service.require_by_id(project_id))
    return _to_project_read(project)


@router.patch("/projects/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: uuid.UUID,
    body: ProjectUpdate,
    _actor: Annotated[User, Depends(require_project_owner_or_admin)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> ProjectRead:
    """Update project name or description (admin or project owner)."""
    updated = await _run_project_op(
        project_service.update(
            project_id,
            name=body.name,
            description=body.description,
        ),
    )
    return _to_project_read(updated)


@router.delete(
    "/projects/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_project(
    project_id: uuid.UUID,
    _admin: Annotated[User, Depends(require_admin)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> None:
    """Delete a project and all nested data (admin only)."""
    await _run_project_op(project_service.delete(project_id))


@router.post("/projects/{project_id}/archive", response_model=ProjectRead)
async def archive_project(
    project_id: uuid.UUID,
    _admin: Annotated[User, Depends(require_admin)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> ProjectRead:
    """Archive a project (admin only)."""
    project = await _run_project_op(project_service.archive(project_id))
    return _to_project_read(project)


@router.post("/projects/{project_id}/unarchive", response_model=ProjectRead)
async def unarchive_project(
    project_id: uuid.UUID,
    _admin: Annotated[User, Depends(require_admin)],
    project_service: Annotated[ProjectService, Depends(get_project_service)],
) -> ProjectRead:
    """Restore an archived project (admin only)."""
    project = await _run_project_op(project_service.unarchive(project_id))
    return _to_project_read(project)


@router.get("/projects/{project_id}/members", response_model=list[MembershipRead])
async def list_project_members(
    project_id: uuid.UUID,
    _member: Annotated[User, Depends(require_project_member)],
    membership_service: Annotated[MembershipService, Depends(get_membership_service)],
) -> list[MembershipRead]:
    """List members of a project (admin or member)."""
    members = await _run_membership_op(membership_service.list_members(project_id))
    return [MembershipRead.model_validate(member) for member in members]


@router.post(
    "/projects/{project_id}/members",
    response_model=MembershipRead,
    status_code=status.HTTP_201_CREATED,
)
async def add_project_member(
    project_id: uuid.UUID,
    body: MembershipCreate,
    _actor: Annotated[User, Depends(require_project_owner_or_admin)],
    membership_service: Annotated[MembershipService, Depends(get_membership_service)],
) -> MembershipRead:
    """Add a member and auto-grant MANAGE on the project root directory."""
    membership = await _run_membership_op(
        membership_service.add_member(
            project_id=project_id,
            user_id=body.user_id,
            role=body.role,
        ),
    )
    return MembershipRead.model_validate(membership)


@router.delete(
    "/projects/{project_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_project_member(
    project_id: uuid.UUID,
    user_id: uuid.UUID,
    _actor: Annotated[User, Depends(require_project_owner_or_admin)],
    membership_service: Annotated[MembershipService, Depends(get_membership_service)],
) -> None:
    """Remove a member and revoke MANAGE on the project root directory."""
    await _run_membership_op(
        membership_service.remove_member(project_id=project_id, user_id=user_id),
    )
