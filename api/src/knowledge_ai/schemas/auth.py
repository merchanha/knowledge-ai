"""Pydantic models for authentication endpoints."""

import uuid
from datetime import datetime

from pydantic import BaseModel

from knowledge_ai.models.user import UserRole


class TokenResponse(BaseModel):
    """JWT access token returned to the SPA."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(BaseModel):
    """Authenticated user profile."""

    id: uuid.UUID
    email: str
    full_name: str | None
    role: UserRole
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
