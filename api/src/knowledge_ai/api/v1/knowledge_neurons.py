"""KnowledgeNeuron REST API — thin controllers over KnowledgeNeuronService."""

from __future__ import annotations

import uuid
from collections.abc import Awaitable
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from knowledge_ai.core.deps import (
    get_casbin_permission_service,
    get_current_user,
    get_embedding_service,
    get_knowledge_neuron_service,
    require_directory_permission,
)
from knowledge_ai.models.knowledge_neuron import KnowledgeNeuron
from knowledge_ai.models.user import User
from knowledge_ai.schemas.knowledge_neuron import (
    KnowledgeNeuronCreate,
    KnowledgeNeuronRead,
    KnowledgeNeuronSearchResult,
    KnowledgeNeuronUpdate,
)
from knowledge_ai.schemas.permissions import DirectoryPermission
from knowledge_ai.services.casbin_permission import CasbinPermissionService
from knowledge_ai.services.embedding import EmbeddingService
from knowledge_ai.services.knowledge_neuron import (
    KnowledgeNeuronNotFoundError,
    KnowledgeNeuronService,
    KnowledgeNeuronValidationError,
)

router = APIRouter(tags=["knowledge-neurons"])


def _to_neuron_read(neuron: KnowledgeNeuron) -> KnowledgeNeuronRead:
    has_embedding = getattr(neuron, "embedding", None) is not None
    return KnowledgeNeuronRead(
        id=neuron.id,
        directory_id=neuron.directory_id,
        title=neuron.title,
        content=neuron.content,
        metadata=neuron.metadata_json,
        has_embedding=has_embedding,
    )


async def _run_neuron_op[T](awaitable: Awaitable[T]) -> T:
    """Map domain exceptions from KnowledgeNeuronService to HTTP errors."""
    try:
        return await awaitable
    except KnowledgeNeuronNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc
    except KnowledgeNeuronValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


async def _require_neuron_directory_permission(
    *,
    neuron_id: uuid.UUID,
    permission: DirectoryPermission,
    user: User,
    neuron_service: KnowledgeNeuronService,
    perm_service: CasbinPermissionService,
) -> KnowledgeNeuron:
    """Load a neuron and require ``permission`` on its parent directory."""
    neuron = await _run_neuron_op(neuron_service.require_by_id(neuron_id))
    allowed = await perm_service.check_directory_permission(
        user,
        neuron.directory_id,
        permission,
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Directory {permission.value} permission required",
        )
    return neuron


@router.get(
    "/knowledge-neurons",
    response_model=list[KnowledgeNeuronSearchResult],
)
async def search_knowledge_neurons(
    user: Annotated[User, Depends(get_current_user)],
    perm_service: Annotated[CasbinPermissionService, Depends(get_casbin_permission_service)],
    embedding_service: Annotated[EmbeddingService, Depends(get_embedding_service)],
    search_term: Annotated[str, Query(min_length=1)],
    limit: Annotated[int, Query(ge=1, le=50)] = 10,
    min_similarity: Annotated[float | None, Query(ge=0.0, le=1.0)] = None,
) -> list[KnowledgeNeuronSearchResult]:
    """Semantic search over KnowledgeNeurons in directories the user can READ."""
    directory_ids = await perm_service.get_readable_directory_ids(user)
    results = await embedding_service.search(
        query=search_term,
        directory_ids=directory_ids,
        limit=limit,
        min_similarity=min_similarity,
    )
    return [
        KnowledgeNeuronSearchResult(
            id=row.neuron.id,
            directory_id=row.neuron.directory_id,
            title=row.neuron.title,
            content=row.neuron.content,
            metadata=row.neuron.metadata_json,
            similarity=row.similarity,
        )
        for row in results
    ]


@router.get(
    "/directories/{directory_id}/knowledge-neurons",
    response_model=list[KnowledgeNeuronRead],
)
async def list_directory_knowledge_neurons(
    directory_id: uuid.UUID,
    _user: Annotated[User, Depends(require_directory_permission(DirectoryPermission.READ))],
    neuron_service: Annotated[KnowledgeNeuronService, Depends(get_knowledge_neuron_service)],
) -> list[KnowledgeNeuronRead]:
    """List KnowledgeNeurons stored in a directory."""
    neurons = await _run_neuron_op(neuron_service.list_by_directory(directory_id))
    return [_to_neuron_read(neuron) for neuron in neurons]


@router.get(
    "/knowledge-neurons/{neuron_id}",
    response_model=KnowledgeNeuronRead,
)
async def get_knowledge_neuron(
    neuron_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    neuron_service: Annotated[KnowledgeNeuronService, Depends(get_knowledge_neuron_service)],
    perm_service: Annotated[CasbinPermissionService, Depends(get_casbin_permission_service)],
) -> KnowledgeNeuronRead:
    """Return a single KnowledgeNeuron."""
    neuron = await _require_neuron_directory_permission(
        neuron_id=neuron_id,
        permission=DirectoryPermission.READ,
        user=user,
        neuron_service=neuron_service,
        perm_service=perm_service,
    )
    return _to_neuron_read(neuron)


@router.post(
    "/directories/{directory_id}/knowledge-neurons",
    response_model=KnowledgeNeuronRead,
    status_code=status.HTTP_201_CREATED,
)
async def create_knowledge_neuron(
    directory_id: uuid.UUID,
    body: KnowledgeNeuronCreate,
    _user: Annotated[User, Depends(require_directory_permission(DirectoryPermission.WRITE))],
    neuron_service: Annotated[KnowledgeNeuronService, Depends(get_knowledge_neuron_service)],
) -> KnowledgeNeuronRead:
    """Create a KnowledgeNeuron inside a directory."""
    created = await _run_neuron_op(
        neuron_service.create(
            directory_id=directory_id,
            title=body.title,
            content=body.content,
            metadata=body.metadata,
        ),
    )
    return _to_neuron_read(created)


@router.patch(
    "/knowledge-neurons/{neuron_id}",
    response_model=KnowledgeNeuronRead,
)
async def update_knowledge_neuron(
    neuron_id: uuid.UUID,
    body: KnowledgeNeuronUpdate,
    user: Annotated[User, Depends(get_current_user)],
    neuron_service: Annotated[KnowledgeNeuronService, Depends(get_knowledge_neuron_service)],
    perm_service: Annotated[CasbinPermissionService, Depends(get_casbin_permission_service)],
) -> KnowledgeNeuronRead:
    """Update a KnowledgeNeuron."""
    await _require_neuron_directory_permission(
        neuron_id=neuron_id,
        permission=DirectoryPermission.WRITE,
        user=user,
        neuron_service=neuron_service,
        perm_service=perm_service,
    )
    updated = await _run_neuron_op(
        neuron_service.update(
            neuron_id,
            title=body.title,
            content=body.content,
            metadata=body.metadata,
        ),
    )
    return _to_neuron_read(updated)


@router.delete(
    "/knowledge-neurons/{neuron_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_knowledge_neuron(
    neuron_id: uuid.UUID,
    user: Annotated[User, Depends(get_current_user)],
    neuron_service: Annotated[KnowledgeNeuronService, Depends(get_knowledge_neuron_service)],
    perm_service: Annotated[CasbinPermissionService, Depends(get_casbin_permission_service)],
) -> None:
    """Delete a KnowledgeNeuron."""
    await _require_neuron_directory_permission(
        neuron_id=neuron_id,
        permission=DirectoryPermission.MANAGE,
        user=user,
        neuron_service=neuron_service,
        perm_service=perm_service,
    )
    await _run_neuron_op(neuron_service.delete(neuron_id))
