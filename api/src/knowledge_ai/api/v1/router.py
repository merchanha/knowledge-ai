"""Aggregate router for API v1."""

from fastapi import APIRouter

from knowledge_ai.api.v1 import health

api_v1_router = APIRouter()
api_v1_router.include_router(health.router)
