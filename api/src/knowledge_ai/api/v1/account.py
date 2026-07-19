"""Account REST API — authenticated user's projects and MCP exposure toggles."""

from __future__ import annotations

import uuid
from collections.abc import Awaitable
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from knowledge_ai.core.deps import get_current_user, get_membership_service
from knowledge_ai.models.user import User
from knowledge_ai.schemas.account import AccountProjectExposureUpdate, AccountProjectRead
from knowledge_ai.schemas.membership import MembershipRead
from knowledge_ai.services.membership import MembershipNotFoundError, MembershipService

router = APIRouter(prefix="/account", tags=["account"])


async def _run_membership_op[T](awaitable: Awaitable[T]) -> T:
    """Map domain exceptions from MembershipService to HTTP errors."""
    try:
        return await awaitable
    except MembershipNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get("", response_model=list[AccountProjectRead])
async def get_account(
    user: Annotated[User, Depends(get_current_user)],
    membership_service: Annotated[MembershipService, Depends(get_membership_service)],
) -> list[AccountProjectRead]:
    """Return the caller's projects with membership role and MCP exposure flag."""
    entries = await membership_service.list_projects_for_user(user.id)
    return [
        AccountProjectRead(
            id=entry.project.id,
            name=entry.project.name,
            description=entry.project.description,
            is_archived=entry.project.is_archived,
            membership_role=entry.membership.role,
            is_context_exposed=entry.membership.is_context_exposed,
        )
        for entry in entries
    ]


@router.patch(
    "/projects/{project_id}",
    response_model=MembershipRead,
)
async def update_account_project_exposure(
    project_id: uuid.UUID,
    body: AccountProjectExposureUpdate,
    user: Annotated[User, Depends(get_current_user)],
    membership_service: Annotated[MembershipService, Depends(get_membership_service)],
) -> MembershipRead:
    """Toggle whether MCP agents may receive this project's ProjectContext."""
    membership = await _run_membership_op(
        membership_service.set_context_exposed(
            user_id=user.id,
            project_id=project_id,
            is_context_exposed=body.is_context_exposed,
        ),
    )
    return MembershipRead.model_validate(membership)
