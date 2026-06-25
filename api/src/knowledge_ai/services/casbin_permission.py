"""Casbin-backed authorization for global roles and directory permissions."""

from __future__ import annotations

import uuid
from enum import StrEnum
from pathlib import Path

import casbin
import casbin_async_sqlalchemy_adapter
from sqlalchemy.ext.asyncio import AsyncSession

from knowledge_ai.core.config import Settings
from knowledge_ai.models.casbin_rule import CasbinRule
from knowledge_ai.models.user import User, UserRole
from knowledge_ai.schemas.permissions import DirectoryPermission

_MODEL_PATH = Path(__file__).resolve().parent.parent / "casbin" / "rbac_model.conf"
_ADMIN_ROLE = UserRole.ADMIN.value
_DIRECTORY_PREFIX = "directory:"


class CasbinPermissionService:
    """Enforce RBAC and directory-scoped policies stored in PostgreSQL."""

    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self._session = session
        self._settings = settings
        self._enforcer: casbin.AsyncEnforcer | None = None

    @staticmethod
    def directory_object(directory_id: uuid.UUID) -> str:
        """Casbin object key for a directory resource."""
        return f"{_DIRECTORY_PREFIX}{directory_id}"

    @staticmethod
    def parse_directory_object(obj: str) -> uuid.UUID | None:
        """Parse a directory object key; return None if not a directory resource."""
        if not obj.startswith(_DIRECTORY_PREFIX):
            return None
        try:
            return uuid.UUID(obj.removeprefix(_DIRECTORY_PREFIX))
        except ValueError:
            return None

    async def get_enforcer(self) -> casbin.AsyncEnforcer:
        """Return a request-scoped AsyncEnforcer bound to the current DB session."""
        if self._enforcer is None:
            adapter = casbin_async_sqlalchemy_adapter.Adapter(
                self._settings.database_url,
                db_class=CasbinRule,
                db_session=self._session,
            )
            self._enforcer = casbin.AsyncEnforcer(str(_MODEL_PATH), adapter)
            await self._enforcer.load_policy()
        return self._enforcer

    async def ensure_base_policies(self) -> None:
        """Seed the global admin allow-all policy if missing."""
        enforcer = await self.get_enforcer()
        if not enforcer.has_policy(_ADMIN_ROLE, "*", "*"):
            await enforcer.add_policy(_ADMIN_ROLE, "*", "*")

    async def sync_user_role(self, user: User) -> None:
        """Mirror ``users.role`` into Casbin grouping policies (``g`` rules)."""
        enforcer = await self.get_enforcer()
        subject = str(user.id)
        for role in (UserRole.ADMIN, UserRole.USER):
            if enforcer.has_role_for_user(subject, role.value):
                await enforcer.delete_role_for_user(subject, role.value)
        await enforcer.add_role_for_user(subject, user.role.value)

    def is_admin(self, user: User) -> bool:
        """Fast path: application-wide admin from the users table."""
        return user.role == UserRole.ADMIN

    async def enforce(self, *, subject: str, obj: str, act: str) -> bool:
        """Check whether ``subject`` may perform ``act`` on ``obj``."""
        enforcer = await self.get_enforcer()
        return bool(enforcer.enforce(subject, obj, act))

    async def check_directory_permission(
        self,
        user: User,
        directory_id: uuid.UUID,
        permission: DirectoryPermission | StrEnum,
    ) -> bool:
        """Return True if the user may perform ``permission`` on ``directory_id``."""
        if self.is_admin(user):
            return True
        act = permission.value if isinstance(permission, StrEnum) else str(permission)
        return await self.enforce(
            subject=str(user.id),
            obj=self.directory_object(directory_id),
            act=act,
        )

    async def grant_directory_permission(
        self,
        *,
        user_id: uuid.UUID,
        directory_id: uuid.UUID,
        permission: DirectoryPermission,
    ) -> bool:
        """Add a directory policy; return False if it already exists."""
        enforcer = await self.get_enforcer()
        return bool(
            await enforcer.add_policy(
                str(user_id),
                self.directory_object(directory_id),
                permission.value,
            )
        )

    async def revoke_directory_permission(
        self,
        *,
        user_id: uuid.UUID,
        directory_id: uuid.UUID,
        permission: DirectoryPermission,
    ) -> bool:
        """Remove a directory policy; return False if it was not present."""
        enforcer = await self.get_enforcer()
        return bool(
            await enforcer.remove_policy(
                str(user_id),
                self.directory_object(directory_id),
                permission.value,
            )
        )

    async def list_directory_permissions_for_user(
        self,
        user_id: uuid.UUID,
    ) -> list[tuple[uuid.UUID, DirectoryPermission]]:
        """Return explicit directory grants for a user (not role-inherited)."""
        enforcer = await self.get_enforcer()
        subject = str(user_id)
        entries: list[tuple[uuid.UUID, DirectoryPermission]] = []
        for rule in await enforcer.get_permissions_for_user(subject):
            if len(rule) < 3:
                continue
            directory_id = self.parse_directory_object(rule[1])
            if directory_id is None:
                continue
            try:
                perm = DirectoryPermission(rule[2])
            except ValueError:
                continue
            entries.append((directory_id, perm))
        return entries

    async def get_readable_directory_ids(self, user: User) -> list[uuid.UUID] | None:
        """Return directory ids the user may READ, or None when admin (all directories)."""
        if self.is_admin(user):
            return None
        grants = await self.list_directory_permissions_for_user(user.id)
        return [directory_id for directory_id, _ in grants]

    async def reload_policy(self) -> None:
        """Reload policies from PostgreSQL after grant/revoke in another session."""
        enforcer = await self.get_enforcer()
        await enforcer.load_policy()
