"""FastAPI application entry point."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from knowledge_ai.api.v1.router import api_v1_router
from knowledge_ai.core.config import settings
from knowledge_ai.core.database import dispose_engine
from knowledge_ai.core.redis import close_redis
from knowledge_ai.middleware.cors import setup_cors


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    """Manage application startup and shutdown lifecycle."""
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
    setup_cors(app)
    app.include_router(api_v1_router, prefix="/api/v1")
    return app


app = create_app()
