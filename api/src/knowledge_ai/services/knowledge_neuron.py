"""KnowledgeNeuron business logic — CRUD scoped to directory folders."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from knowledge_ai.models.knowledge_neuron import KnowledgeNeuron
from knowledge_ai.services.directory import DirectoryService


class KnowledgeNeuronError(Exception):
    """Base error for KnowledgeNeuron domain operations."""


class KnowledgeNeuronNotFoundError(KnowledgeNeuronError):
    """Raised when a KnowledgeNeuron id does not exist."""


class KnowledgeNeuronValidationError(KnowledgeNeuronError):
    """Raised when input violates domain rules."""


class KnowledgeNeuronService:
    """CRUD operations for KnowledgeNeurons stored in directory folders."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session
        self._directories = DirectoryService(session)

    async def get_by_id(self, neuron_id: UUID) -> KnowledgeNeuron | None:
        """Load a KnowledgeNeuron by primary key."""
        return await self._session.get(KnowledgeNeuron, neuron_id)

    async def require_by_id(self, neuron_id: UUID) -> KnowledgeNeuron:
        """Load a KnowledgeNeuron or raise ``KnowledgeNeuronNotFoundError``."""
        neuron = await self.get_by_id(neuron_id)
        if neuron is None:
            raise KnowledgeNeuronNotFoundError(f"KnowledgeNeuron {neuron_id} not found")
        return neuron

    async def list_by_directory(self, directory_id: UUID) -> list[KnowledgeNeuron]:
        """Return KnowledgeNeurons in a directory ordered by title."""
        await self._directories.require_by_id(directory_id)
        result = await self._session.execute(
            select(KnowledgeNeuron)
            .where(KnowledgeNeuron.directory_id == directory_id)
            .order_by(KnowledgeNeuron.title),
        )
        return list(result.scalars().all())

    async def create(
        self,
        *,
        directory_id: UUID,
        title: str,
        content: str,
        metadata: dict[str, Any] | None = None,
    ) -> KnowledgeNeuron:
        """Create a KnowledgeNeuron inside ``directory_id``."""
        normalized_title = title.strip()
        normalized_content = content.strip()
        if not normalized_title:
            raise KnowledgeNeuronValidationError("Title cannot be empty")
        if not normalized_content:
            raise KnowledgeNeuronValidationError("Content cannot be empty")

        await self._directories.require_by_id(directory_id)

        neuron = KnowledgeNeuron(
            directory_id=directory_id,
            title=normalized_title,
            content=normalized_content,
            metadata_json=metadata or {},
        )
        self._session.add(neuron)
        await self._session.flush()
        self._enqueue_embed(neuron.id)
        return neuron

    async def update(
        self,
        neuron_id: UUID,
        *,
        title: str | None = None,
        content: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> KnowledgeNeuron:
        """Update fields on an existing KnowledgeNeuron."""
        neuron = await self.require_by_id(neuron_id)

        if title is not None:
            normalized_title = title.strip()
            if not normalized_title:
                raise KnowledgeNeuronValidationError("Title cannot be empty")
            neuron.title = normalized_title

        if content is not None:
            normalized_content = content.strip()
            if not normalized_content:
                raise KnowledgeNeuronValidationError("Content cannot be empty")
            neuron.content = normalized_content

        if metadata is not None:
            neuron.metadata_json = metadata

        await self._session.flush()
        self._enqueue_embed(neuron.id)
        return neuron

    async def delete(self, neuron_id: UUID) -> None:
        """Delete a KnowledgeNeuron."""
        neuron = await self.require_by_id(neuron_id)
        await self._session.delete(neuron)
        await self._session.flush()

    @staticmethod
    def _enqueue_embed(neuron_id: UUID) -> None:
        """Schedule a background embedding task (no-op if Celery is unavailable)."""
        try:
            from knowledge_ai.tasks.embedding import embed_knowledge_neuron

            embed_knowledge_neuron.delay(str(neuron_id))
        except Exception:
            pass
