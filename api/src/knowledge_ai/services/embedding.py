"""Voyage AI embedding client and pgvector semantic search."""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from uuid import UUID

import httpx
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from knowledge_ai.core.config import Settings
from knowledge_ai.core.redis import get_redis
from knowledge_ai.models.knowledge_neuron import KnowledgeNeuron
from knowledge_ai.services.knowledge_neuron import KnowledgeNeuronNotFoundError

logger = logging.getLogger(__name__)

VOYAGE_EMBED_URL = "https://api.voyageai.com/v1/embeddings"
QUERY_CACHE_PREFIX = "embedding:query:"
QUERY_CACHE_TTL_SECONDS = 300


@dataclass(frozen=True)
class SearchResult:
    """A KnowledgeNeuron matched by vector similarity."""

    neuron: KnowledgeNeuron
    similarity: float


class EmbeddingService:
    """Embed text via Voyage AI and run pgvector similarity search."""

    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self._session = session
        self._settings = settings

    @property
    def dimensions(self) -> int:
        return self._settings.voyage_embedding_dimensions

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Call Voyage AI and return embedding vectors for each input text."""
        if not texts:
            return []
        if not self._settings.voyage_api_key:
            raise RuntimeError("VOYAGE_API_KEY is not configured")

        payload = {
            "input": texts,
            "model": self._settings.voyage_model,
            "input_type": "document",
        }
        headers = {
            "Authorization": f"Bearer {self._settings.voyage_api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(VOYAGE_EMBED_URL, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        embeddings = sorted(data["data"], key=lambda row: row["index"])
        return [list[float](row["embedding"]) for row in embeddings]

    async def embed_query(self, query: str) -> list[float]:
        """Embed a search query, using Redis cache when available."""
        normalized = query.strip()
        cache_key = self._query_cache_key(normalized)
        redis = get_redis()
        cached = await redis.get(cache_key)
        if cached is not None:
            return list[float](json.loads(cached))

        if not self._settings.voyage_api_key:
            raise RuntimeError("VOYAGE_API_KEY is not configured")

        payload = {
            "input": [normalized],
            "model": self._settings.voyage_model,
            "input_type": "query",
        }
        headers = {
            "Authorization": f"Bearer {self._settings.voyage_api_key}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(VOYAGE_EMBED_URL, json=payload, headers=headers)
            response.raise_for_status()
            data = response.json()

        vector: list[float] = list(data["data"][0]["embedding"])
        await redis.set(cache_key, json.dumps(vector), ex=QUERY_CACHE_TTL_SECONDS)
        return vector

    async def embed_knowledge_neuron(self, neuron_id: UUID) -> None:
        """Generate and persist an embedding for a KnowledgeNeuron."""
        neuron = await self._session.get(KnowledgeNeuron, neuron_id)
        if neuron is None:
            raise KnowledgeNeuronNotFoundError(f"KnowledgeNeuron {neuron_id} not found")

        embed_text = f"{neuron.title}\n\n{neuron.content}"
        vector = (await self.embed_texts([embed_text]))[0]
        neuron.embedding = vector
        await self._session.flush()

    async def clear_embedding(self, neuron_id: UUID) -> None:
        """Remove the stored embedding vector for a KnowledgeNeuron."""
        neuron = await self._session.get(KnowledgeNeuron, neuron_id)
        if neuron is None:
            return
        neuron.embedding = None
        await self._session.flush()

    async def search(
        self,
        *,
        query: str,
        directory_ids: list[UUID] | None,
        limit: int,
    ) -> list[SearchResult]:
        """Return top-k KnowledgeNeurons by cosine similarity within allowed directories."""
        query_vector = await self.embed_query(query)
        vector_literal = self._vector_literal(query_vector)

        if directory_ids is not None and not directory_ids:
            return []

        sql = """
            SELECT
                kn.id,
                1 - (kn.embedding <=> CAST(:query_vector AS vector)) AS similarity
            FROM knowledge_neurons kn
            WHERE kn.embedding IS NOT NULL
        """
        params: dict[str, object] = {
            "query_vector": vector_literal,
            "limit": limit,
        }
        if directory_ids is not None:
            sql += " AND kn.directory_id = ANY(CAST(:directory_ids AS uuid[]))"
            params["directory_ids"] = [str(directory_id) for directory_id in directory_ids]

        sql += """
            ORDER BY kn.embedding <=> CAST(:query_vector AS vector)
            LIMIT :limit
        """

        result = await self._session.execute(text(sql), params)
        rows = result.all()
        if not rows:
            return []

        neuron_ids = [row.id for row in rows]
        similarity_by_id = {row.id: float(row.similarity) for row in rows}
        neurons_result = await self._session.execute(
            select(KnowledgeNeuron).where(KnowledgeNeuron.id.in_(neuron_ids)),
        )
        neurons_by_id = {neuron.id: neuron for neuron in neurons_result.scalars().all()}

        return [
            SearchResult(
                neuron=neurons_by_id[neuron_id],
                similarity=similarity_by_id[neuron_id],
            )
            for neuron_id in neuron_ids
            if neuron_id in neurons_by_id
        ]

    def _query_cache_key(self, query: str) -> str:
        digest = hashlib.sha256(query.encode()).hexdigest()
        return f"{QUERY_CACHE_PREFIX}{self._settings.voyage_model}:{digest}"

    def _vector_literal(self, vector: list[float]) -> str:
        return "[" + ",".join(str(value) for value in vector) + "]"
