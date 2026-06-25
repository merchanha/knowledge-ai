"""Aggregate router for API v1."""

from fastapi import APIRouter

from knowledge_ai.api.v1 import admin, auth, directories, health, knowledge_neurons, permissions

api_v1_router = APIRouter()
api_v1_router.include_router(health.router)
api_v1_router.include_router(auth.router)
api_v1_router.include_router(admin.router)
api_v1_router.include_router(permissions.router)
api_v1_router.include_router(directories.router)
api_v1_router.include_router(knowledge_neurons.router)
