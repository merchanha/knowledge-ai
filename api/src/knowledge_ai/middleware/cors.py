"""CORS middleware configuration for the SPA client."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from knowledge_ai.core.config import settings


def setup_cors(app: FastAPI) -> None:
    """Register CORS middleware for allowed frontend origins."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
