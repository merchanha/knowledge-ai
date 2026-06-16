"""ZIP export for directory subtrees."""

from __future__ import annotations

import io
import zipfile
from uuid import UUID

from knowledge_ai.models.directory import Directory
from knowledge_ai.services.directory import DirectoryNotFoundError, DirectoryService


class DownloadService:
    """Build downloadable archives from directory tree structure."""

    def __init__(self, directory_service: DirectoryService) -> None:
        self._directory_service = directory_service

    async def build_subtree_zip(self, directory_id: UUID) -> tuple[bytes, str]:
        """Return ZIP bytes and a filename for the directory subtree."""
        anchor = await self._directory_service.require_by_id(directory_id)
        nodes = await self._collect_subtree(directory_id)
        by_id = {node.id: node for node in nodes}

        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
            for node in nodes:
                relative_path = self._relative_zip_path(node, anchor.id, by_id)
                archive.writestr(f"{relative_path}/", b"")

        return buffer.getvalue(), f"{anchor.name}.zip"

    async def _collect_subtree(self, directory_id: UUID) -> list[Directory]:
        """Breadth-first collection of anchor and all descendants."""
        anchor = await self._directory_service.require_by_id(directory_id)
        nodes = [anchor]
        queue: list[UUID] = [directory_id]

        while queue:
            current_id = queue.pop(0)
            children = await self._directory_service.list_children(current_id)
            nodes.extend(children)
            queue.extend(child.id for child in children)

        return nodes

    @staticmethod
    def _relative_zip_path(
        node: Directory,
        anchor_id: UUID,
        by_id: dict[UUID, Directory],
    ) -> str:
        """Build a ZIP-internal path from the anchor down to ``node``."""
        parts: list[str] = []
        current: Directory | None = node

        while current is not None:
            parts.append(current.name)
            if current.id == anchor_id:
                break
            parent_id = current.parent_id
            if parent_id is None:
                raise DirectoryNotFoundError(
                    f"Directory {node.id} is not under anchor {anchor_id}",
                )
            current = by_id.get(parent_id)
            if current is None:
                raise DirectoryNotFoundError(
                    f"Directory {parent_id} not found while building ZIP path",
                )

        parts.reverse()
        return "/".join(parts)
