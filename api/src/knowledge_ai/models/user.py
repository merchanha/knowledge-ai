"""User ORM model."""

from enum import StrEnum

from sqlalchemy import Boolean, Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from knowledge_ai.models.base import Base, TimestampMixin, str_enum_values


class UserRole(StrEnum):
    """Application-wide user roles."""

    ADMIN = "admin"
    USER = "user"


class User(Base, TimestampMixin):
    """Authenticated user (Google SSO in Week 3)."""

    __tablename__ = "users"

    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    google_sub: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    role: Mapped[UserRole] = mapped_column(
        Enum(
            UserRole,
            name="user_role",
            native_enum=True,
            values_callable=str_enum_values,
        ),
        default=UserRole.USER,
        nullable=False,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
