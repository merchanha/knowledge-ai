"""Project ORM model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from knowledge_ai.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from knowledge_ai.models.directory import Directory


class Project(Base, TimestampMixin):
    """Top-level container for directories, neurons, and commands."""

    __tablename__ = "projects"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_archived: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    directories: Mapped[list[Directory]] = relationship(
        back_populates="project",
        cascade="all, delete-orphan",
    )
