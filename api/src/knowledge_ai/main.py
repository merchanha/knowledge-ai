"""FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from knowledge_ai.api.v1.router import api_v1_router
from knowledge_ai.api.well_known import router as well_known_router
from knowledge_ai.core.config import settings
from knowledge_ai.core.database import dispose_engine, get_session_factory
from knowledge_ai.core.redis import close_redis
from knowledge_ai.core.sentry import init_sentry
from knowledge_ai.mcp.server import mcp_server
from knowledge_ai.middleware.cors import setup_cors
from knowledge_ai.middleware.mcp_auth import MCPAuthMiddleware
from knowledge_ai.middleware.rate_limit import RateLimitMiddleware
from knowledge_ai.services.casbin_permission import CasbinPermissionService

init_sentry(settings)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown lifecycle."""
    session_factory = get_session_factory()
    async with session_factory() as session:
        await CasbinPermissionService(session, settings).ensure_base_policies()
        await session.commit()

    async with mcp_server.session_manager.run():
        yield

    await dispose_engine()
    await close_redis()


def create_app() -> FastAPI:
    """Build and configure the FastAPI application."""
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
        lifespan=lifespan,
    )
    # Starlette middleware is LIFO: last added runs first (outermost).
    # Desired order: CORS → RateLimit → MCPAuth → routes.
    app.add_middleware(MCPAuthMiddleware)
    app.add_middleware(RateLimitMiddleware)
    setup_cors(app)
    app.include_router(well_known_router)
    app.include_router(api_v1_router, prefix="/api/v1")
    app.mount("/mcp", mcp_server.streamable_http_app())
    return app


app = create_app()
