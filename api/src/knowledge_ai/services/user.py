"""User persistence for authentication flows."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from knowledge_ai.models.user import User, UserRole


class UserService:
    """User lookups and upsert on Google login."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_id(self, user_id: UUID) -> User | None:
        """Load a user by primary key."""
        return await self._session.get(User, user_id)

    async def list_all(self) -> list[User]:
        """Return all users ordered by email (admin listing)."""
        result = await self._session.execute(select(User).order_by(User.email))
        return list(result.scalars().all())

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
