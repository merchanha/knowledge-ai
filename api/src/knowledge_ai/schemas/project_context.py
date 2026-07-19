"""ProjectContext schema — layered directory tree for MCP agents."""

from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel, Field


class ProjectNeuronSummary(BaseModel):
    """KnowledgeNeuron leaf included in ProjectContext."""

    id: uuid.UUID
    title: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProjectCommandSummary(BaseModel):
    """Command leaf included in ProjectContext."""

    id: uuid.UUID
    title: str
    content: str
    metadata: dict[str, Any] = Field(default_factory=dict)


class ProjectDirectoryNode(BaseModel):
    """One directory node with child folders and attached knowledge."""

    id: uuid.UUID
    name: str
    children: list[ProjectDirectoryNode] = Field(default_factory=list)
    knowledge_neurons: list[ProjectNeuronSummary] = Field(default_factory=list)
    commands: list[ProjectCommandSummary] = Field(default_factory=list)


class ProjectTree(BaseModel):
    """Exposed project subtree rooted at the project directory tree."""

    project_id: uuid.UUID
    project_name: str
    root: ProjectDirectoryNode


class ProjectContext(BaseModel):
    """Aggregated MCP payload for all user-exposed projects."""

    projects: list[ProjectTree] = Field(default_factory=list)
