"""Optional Sentry initialization for FastAPI, SQLAlchemy, Celery, and httpx."""

from __future__ import annotations

import logging

import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.httpx import HttpxIntegration
from sentry_sdk.integrations.sqlalchemy import SqlalchemyIntegration
from sentry_sdk.integrations.starlette import StarletteIntegration

from knowledge_ai.core.config import Settings

logger = logging.getLogger(__name__)


def init_sentry(settings: Settings) -> None:
    """Initialize Sentry when ``SENTRY_DSN`` is set; otherwise no-op."""
    if not settings.sentry_dsn:
        logger.debug("Sentry disabled — SENTRY_DSN is empty")
        return

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.sentry_environment,
        release=settings.app_version,
        traces_sample_rate=settings.sentry_traces_sample_rate,
        integrations=[
            StarletteIntegration(),
            FastApiIntegration(),
            SqlalchemyIntegration(),
            CeleryIntegration(propagate_traces=True),
            HttpxIntegration(),
        ],
    )
    logger.info(
        "Sentry initialized (env=%s, traces_sample_rate=%s)",
        settings.sentry_environment,
        settings.sentry_traces_sample_rate,
    )
