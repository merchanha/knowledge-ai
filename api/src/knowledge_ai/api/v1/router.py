"""Aggregate router for API v1."""

from fastapi import APIRouter

from knowledge_ai.api.v1 import auth, health

api_v1_router = APIRouter()
api_v1_router.include_router(health.router)
api_v1_router.include_router(auth.router)
