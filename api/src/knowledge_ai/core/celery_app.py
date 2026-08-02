"""Celery application and worker configuration."""

from celery import Celery

from knowledge_ai.core.config import settings
from knowledge_ai.core.sentry import init_sentry

init_sentry(settings)

celery_app = Celery(
    "knowledge_ai",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["knowledge_ai.tasks.embedding"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_default_queue="embeddings",
)
