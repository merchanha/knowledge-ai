"""KnowledgeNeuron ORM model — stored knowledge documents in directory folders."""

from __future__ import annotations

import uuid
from typing import TYPE_CHECKING, Any

from pgvector.sqlalchemy import Vector
from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from knowledge_ai.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from knowledge_ai.models.directory import Directory


class KnowledgeNeuron(Base, TimestampMixin):
    """A knowledge document stored inside a directory folder."""

    __tablename__ = "knowledge_neurons"

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
    embedding: Mapped[list[float] | None] = mapped_column(Vector(1024), nullable=True)

    directory: Mapped[Directory] = relationship(back_populates="knowledge_neurons")
