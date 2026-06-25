"""Background tasks for KnowledgeNeuron embedding."""

from __future__ import annotations

import asyncio
import logging
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from knowledge_ai.core.celery_app import celery_app
from knowledge_ai.core.config import settings
from knowledge_ai.services.embedding import EmbeddingService
from knowledge_ai.services.knowledge_neuron import KnowledgeNeuronNotFoundError

logger = logging.getLogger(__name__)


async def _run_with_session(coro_factory: object) -> None:
    engine = create_async_engine(settings.database_url, poolclass=NullPool)
    session_factory = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
    try:
        async with session_factory() as session:
            await coro_factory(session)  # type: ignore[operator]
            await session.commit()
    finally:
        await engine.dispose()


@celery_app.task(name="knowledge_ai.tasks.embedding.embed_knowledge_neuron")  # type: ignore[untyped-decorator]
def embed_knowledge_neuron(neuron_id: str) -> None:
    """Generate and store a pgvector embedding for one KnowledgeNeuron."""

    async def _embed(session: AsyncSession) -> None:
        service = EmbeddingService(session, settings)
        try:
            await service.embed_knowledge_neuron(UUID(neuron_id))
        except KnowledgeNeuronNotFoundError:
            logger.warning("Skipping embed for missing KnowledgeNeuron %s", neuron_id)
        except Exception:
            logger.exception("Failed to embed KnowledgeNeuron %s", neuron_id)
            raise

    asyncio.run(_run_with_session(_embed))
