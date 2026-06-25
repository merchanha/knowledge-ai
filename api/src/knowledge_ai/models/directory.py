"""Directory ORM model — self-referential tree scoped to a project."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from knowledge_ai.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from knowledge_ai.models.knowledge_neuron import KnowledgeNeuron
    from knowledge_ai.models.project import Project

ROOT_DIRECTORY_NAME = "Root"


class Directory(Base, TimestampMixin):
    """A node in a project's directory tree (adjacency list via parent_id)."""

    __tablename__ = "directories"
    __table_args__ = (
        UniqueConstraint(
            "project_id",
            "parent_id",
            "name",
            name="uq_directories_project_parent_name",
        ),
        Index(
            "ix_directories_project_root",
            "project_id",
            unique=True,
            postgresql_where="parent_id IS NULL",
        ),
    )

    project_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("directories.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)

    project: Mapped[Project] = relationship(back_populates="directories")
    parent: Mapped[Directory | None] = relationship(
        "Directory",
        remote_side="Directory.id",
        back_populates="children",
        foreign_keys=[parent_id],
    )
    children: Mapped[list[Directory]] = relationship(
        "Directory",
        back_populates="parent",
        foreign_keys=[parent_id],
        cascade="all, delete-orphan",
    )
    knowledge_neurons: Mapped[list[KnowledgeNeuron]] = relationship(
        "KnowledgeNeuron",
        back_populates="directory",
        cascade="all, delete-orphan",
    )

    @property
    def is_root(self) -> bool:
        """True when this directory is the project root (no parent)."""
        return self.parent_id is None
