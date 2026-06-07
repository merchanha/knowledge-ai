"""Admin-only controllers (application-wide role gate)."""

from typing import Annotated

from fastapi import APIRouter, Depends

from knowledge_ai.core.deps import get_user_service, require_admin
from knowledge_ai.models.user import User
from knowledge_ai.schemas.auth import UserResponse
from knowledge_ai.services.user import UserService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=list[UserResponse])
async def list_users(
    _admin: Annotated[User, Depends(require_admin)],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> list[UserResponse]:
    """List all users (admin only). Full user management ships in Week 11."""
    users = await user_service.list_all()
    return [UserResponse.model_validate(user) for user in users]
