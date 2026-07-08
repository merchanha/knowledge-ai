"""User persistence for authentication flows."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from knowledge_ai.models.user import User, UserRole


class UserError(Exception):
    """Base error for user domain operations."""


class UserNotFoundError(UserError):
    """Raised when a user id does not exist."""


class UserValidationError(UserError):
    """Raised when user input violates domain rules."""


class UserService:
    """User lookups, upsert on Google login, and admin updates."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        """Load a user by primary key."""
        return await self._session.get(User, user_id)

    async def require_by_id(self, user_id: UUID) -> User:
        """Load a user or raise ``UserNotFoundError``."""
        user = await self.get_by_id(user_id)
        if user is None:
            raise UserNotFoundError(f"User {user_id} not found")
        return user

    async def list_all(self) -> list[User]:
        """Return all users ordered by email (admin listing)."""
        result = await self._session.execute(select(User).order_by(User.email))
        return list(result.scalars().all())

    async def update(
        self,
        user_id: UUID,
        *,
        role: UserRole | None = None,
        is_active: bool | None = None,
    ) -> User:
        """Update application-wide role or active status (admin)."""
        user = await self.require_by_id(user_id)

        if role is not None:
            user.role = role

        if is_active is not None:
            user.is_active = is_active

        await self._session.flush()
        await self._session.refresh(user)
        return user

    async def upsert_from_google(
        self,
        *,
        google_sub: str,
        email: str,
        full_name: str | None,
    ) -> User:
        """Create or update a user from Google OpenID claims."""
        result = await self._session.execute(
            select(User).where(User.google_sub == google_sub),
        )
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                google_sub=google_sub,
                email=email,
                full_name=full_name,
                role=UserRole.USER,
                is_active=True,
            )
            self._session.add(user)
        else:
            user.email = email
            user.full_name = full_name

        await self._session.flush()
        return user
