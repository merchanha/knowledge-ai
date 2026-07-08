"""Project membership ORM model."""

import uuid
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from knowledge_ai.models.base import Base, TimestampMixin, str_enum_values

if TYPE_CHECKING:
    from knowledge_ai.models.project import Project
    from knowledge_ai.models.user import User


class ProjectMembershipRole(StrEnum):
    """Role of a user within a project."""

    OWNER = "owner"
    MEMBER = "member"


class ProjectMembership(Base, TimestampMixin):
    """Links a user to a project with a project-level role."""

    __tablename__ = "project_memberships"
    __table_args__ = (
        UniqueConstraint("user_id", "project_id",
                         name="uq_project_memberships_user_project"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    role: Mapped[ProjectMembershipRole] = mapped_column(
        Enum(
            ProjectMembershipRole,
            name="project_membership_role",
            native_enum=True,
            values_callable=str_enum_values,
        ),
        default=ProjectMembershipRole.MEMBER,
        nullable=False,
    )
    is_context_exposed: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        nullable=False,
    )

    project: Mapped["Project"] = relationship(back_populates="memberships")
    user: Mapped["User"] = relationship()
