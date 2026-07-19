"""ContextBuilder — assemble ProjectContext from exposed project trees."""

from __future__ import annotations

from collections import defaultdict
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from knowledge_ai.models.command import Command
from knowledge_ai.models.directory import Directory
from knowledge_ai.models.knowledge_neuron import KnowledgeNeuron
from knowledge_ai.models.user import User
from knowledge_ai.schemas.project_context import (
    ProjectCommandSummary,
    ProjectContext,
    ProjectDirectoryNode,
    ProjectNeuronSummary,
    ProjectTree,
)
from knowledge_ai.services.command import CommandService
from knowledge_ai.services.directory import DirectoryService
from knowledge_ai.services.membership import MembershipService


class ContextBuilder:
    """Build ProjectContext for projects the user exposed to MCP agents."""

    def __init__(
        self,
        session: AsyncSession,
        membership_service: MembershipService,
        directory_service: DirectoryService,
        command_service: CommandService,
    ) -> None:
        self._session = session
        self._membership = membership_service
        self._directories = directory_service
        self._commands = command_service

    async def build_for_user(self, user: User) -> ProjectContext:
        """Return layered directory trees for ``is_context_exposed`` projects."""
        account_projects = await self._membership.list_projects_for_user(user.id)
        exposed = [
            account_project
            for account_project in account_projects
            if account_project.membership.is_context_exposed
        ]

        projects: list[ProjectTree] = []
        for account_project in exposed:
            project = account_project.project
            root = await self._directories.get_root_for_project(project.id)
            if root is None:
                continue

            directories = await self._directories.list_by_project(project.id)
            neurons = await self._list_neurons_for_project(project.id)
            commands = await self._commands.list_by_project(project.id)
            root_node = self._build_directory_tree(
                root_id=root.id,
                directories=directories,
                neurons=neurons,
                commands=commands,
            )
            projects.append(
                ProjectTree(
                    project_id=project.id,
                    project_name=project.name,
                    root=root_node,
                ),
            )

        return ProjectContext(projects=projects)

    async def _list_neurons_for_project(self, project_id: UUID) -> list[KnowledgeNeuron]:
        directory_ids = [
            directory.id for directory in await self._directories.list_by_project(project_id)
        ]
        if not directory_ids:
            return []
        result = await self._session.execute(
            select(KnowledgeNeuron)
            .where(KnowledgeNeuron.directory_id.in_(directory_ids))
            .order_by(KnowledgeNeuron.title),
        )
        return list(result.scalars().all())

    def _build_directory_tree(
        self,
        *,
        root_id: UUID,
        directories: list[Directory],
        neurons: list[KnowledgeNeuron],
        commands: list[Command],
    ) -> ProjectDirectoryNode:
        by_parent: dict[UUID | None, list[Directory]] = defaultdict(list)
        for directory in directories:
            by_parent[directory.parent_id].append(directory)

        neurons_by_directory: dict[UUID, list[KnowledgeNeuron]] = defaultdict(list)
        for neuron in neurons:
            neurons_by_directory[neuron.directory_id].append(neuron)

        commands_by_directory: dict[UUID, list[Command]] = defaultdict(list)
        for command in commands:
            commands_by_directory[command.directory_id].append(command)

        directory_by_id = {directory.id: directory for directory in directories}

        def build_node(directory_id: UUID) -> ProjectDirectoryNode:
            directory = directory_by_id[directory_id]
            child_directories = sorted(
                by_parent.get(directory_id, []),
                key=lambda item: item.name,
            )
            return ProjectDirectoryNode(
                id=directory.id,
                name=directory.name,
                children=[build_node(child.id) for child in child_directories],
                knowledge_neurons=[
                    ProjectNeuronSummary(
                        id=neuron.id,
                        title=neuron.title,
                        content=neuron.content,
                        metadata=neuron.metadata_json,
                    )
                    for neuron in sorted(
                        neurons_by_directory.get(directory_id, []),
                        key=lambda item: item.title,
                    )
                ],
                commands=[
                    ProjectCommandSummary(
                        id=command.id,
                        title=command.title,
                        content=command.content,
                        metadata=command.metadata_json,
                    )
                    for command in sorted(
                        commands_by_directory.get(directory_id, []),
                        key=lambda item: item.title,
                    )
                ],
            )

        return build_node(root_id)
