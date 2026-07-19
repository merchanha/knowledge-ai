"""Request-scoped MCP user context for tool handlers."""

import os
from contextvars import ContextVar, Token
from uuid import UUID

from knowledge_ai.core.database import get_session_factory
from knowledge_ai.models.user import User
from knowledge_ai.services.user import UserService

_current_mcp_user: ContextVar[User | None] = ContextVar("mcp_user", default=None)


def set_current_mcp_user(user: User) -> Token[User | None]:
    """Bind the authenticated user for the current MCP request."""
    return _current_mcp_user.set(user)


def reset_current_mcp_user(token: Token[User | None]) -> None:
    """Clear the MCP user context after the request completes."""
    _current_mcp_user.reset(token)


def get_current_mcp_user() -> User:
    """Return the user authenticated by ``MCPAuthMiddleware``."""
    user = _current_mcp_user.get()
    if user is not None:
        return user
    msg = "MCP tool invoked without an authenticated user"
    raise RuntimeError(msg)


async def resolve_mcp_user() -> User:
    """Return the HTTP-authenticated user or a stdio dev user from env."""
    user = _current_mcp_user.get()
    if user is not None:
        return user

    stdio_user_id = os.environ.get("MCP_STDIO_USER_ID")
    if stdio_user_id is None:
        msg = "MCP tool invoked without an authenticated user"
        raise RuntimeError(msg)

    session_factory = get_session_factory()
    async with session_factory() as session:
        loaded = await UserService(session).get_by_id(UUID(stdio_user_id))
        if loaded is None or not loaded.is_active:
            msg = "MCP_STDIO_USER_ID does not reference an active user"
            raise RuntimeError(msg)
        return loaded
