"""Command ORM model — reusable instruction snippets in directory folders."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from knowledge_ai.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from knowledge_ai.models.directory import Directory


class Command(Base, TimestampMixin):
    """A reusable instruction snippet stored inside a directory folder."""

    __tablename__ = "commands"

    directory_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("directories.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    metadata_json: Mapped[dict[str, Any]] = mapped_column(
        "metadata",
        JSONB,
        nullable=False,
        server_default="{}",
    )

    directory: Mapped[Directory] = relationship(back_populates="commands")
