"""MCP server — tool registration and transports."""

from __future__ import annotations

from typing import Any
from uuid import UUID

from mcp.server.fastmcp import FastMCP

from knowledge_ai.core.config import settings
from knowledge_ai.core.database import get_session_factory
from knowledge_ai.core.mcp_context import resolve_mcp_user
from knowledge_ai.schemas.permissions import DirectoryPermission
from knowledge_ai.services.casbin_permission import CasbinPermissionService
from knowledge_ai.services.command import CommandService
from knowledge_ai.services.context_builder import ContextBuilder
from knowledge_ai.services.embedding import EmbeddingService
from knowledge_ai.services.membership import MembershipService


def create_mcp_server() -> FastMCP:
    """Build the Knowledge-AI MCP server with search and context tools."""
    server = FastMCP(
        "Knowledge-AI",
        instructions=(
            "Knowledge management tools for coding agents: semantic search over "
            "KnowledgeNeurons, command browsing, and ProjectContext retrieval."
        ),
        streamable_http_path="/",
    )

    @server.tool()
    async def search_knowledge_neurons(query: str, limit: int = 10) -> list[dict[str, Any]]:
        """Semantic search over KnowledgeNeurons in directories the user can READ."""
        user = await resolve_mcp_user()
        bounded_limit = max(1, min(limit, 50))
        session_factory = get_session_factory()
        async with session_factory() as session:
            perm_service = CasbinPermissionService(session, settings)
            embedding_service = EmbeddingService(session, settings)
            directory_ids = await perm_service.get_readable_directory_ids(user)
            results = await embedding_service.search(
                query=query,
                directory_ids=directory_ids,
                limit=bounded_limit,
            )
            return [
                {
                    "id": str(row.neuron.id),
                    "directory_id": str(row.neuron.directory_id),
                    "title": row.neuron.title,
                    "content": row.neuron.content,
                    "metadata": row.neuron.metadata_json,
                    "similarity": row.similarity,
                }
                for row in results
            ]

    @server.tool()
    async def list_commands(directory_id: str | None = None) -> list[dict[str, Any]]:
        """List Commands in a directory or across all readable directories."""
        user = await resolve_mcp_user()
        session_factory = get_session_factory()
        async with session_factory() as session:
            perm_service = CasbinPermissionService(session, settings)
            command_service = CommandService(session)
            if directory_id is not None:
                parsed_directory_id = UUID(directory_id)
                allowed = await perm_service.check_directory_permission(
                    user,
                    parsed_directory_id,
                    DirectoryPermission.READ,
                )
                if not allowed:
                    return []
                commands = await command_service.list_by_directory(parsed_directory_id)
            else:
                directory_ids = await perm_service.get_readable_directory_ids(user)
                commands = await command_service.list_in_directories(directory_ids)

            return [
                {
                    "id": str(command.id),
                    "directory_id": str(command.directory_id),
                    "title": command.title,
                    "content": command.content,
                    "metadata": command.metadata_json,
                }
                for command in commands
            ]

    @server.tool()
    async def get_project_context() -> dict[str, Any]:
        """Return ProjectContext for projects where is_context_exposed is enabled."""
        user = await resolve_mcp_user()
        session_factory = get_session_factory()
        async with session_factory() as session:
            perm_service = CasbinPermissionService(session, settings)
            membership_service = MembershipService(session, perm_service)
            from knowledge_ai.services.directory import DirectoryService

            builder = ContextBuilder(
                session,
                membership_service,
                DirectoryService(session),
                CommandService(session),
            )
            context = await builder.build_for_user(user)
            return context.model_dump(mode="json")

    return server


mcp_server = create_mcp_server()
