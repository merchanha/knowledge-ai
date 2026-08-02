"""Transactional email via Resend + Jinja2 templates."""

from __future__ import annotations

import logging
from pathlib import Path

from jinja2 import Environment, FileSystemLoader, select_autoescape

from knowledge_ai.core.config import Settings

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = Path(__file__).resolve().parents[1] / "templates" / "email"


class EmailService:
    """Send optional transactional emails; no-ops when Resend is not configured."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._env = Environment(
            loader=FileSystemLoader(str(_TEMPLATES_DIR)),
            autoescape=select_autoescape(["html", "xml"]),
        )

    @property
    def enabled(self) -> bool:
        return bool(self._settings.resend_api_key)

    async def send_welcome(self, *, to_email: str, full_name: str | None) -> bool:
        """Welcome a newly created user after first Google login."""
        display = full_name or to_email
        html = self._env.get_template("welcome.html").render(
            name=display,
            app_url=self._settings.app_public_url,
        )
        return await self._send(
            to_email=to_email,
            subject="Welcome to Knowledge-AI",
            html=html,
        )

    async def send_permission_granted(
        self,
        *,
        to_email: str,
        full_name: str | None,
        directory_name: str,
        permission: str,
    ) -> bool:
        """Notify a user that directory access was granted."""
        display = full_name or to_email
        html = self._env.get_template("permission_granted.html").render(
            name=display,
            directory_name=directory_name,
            permission=permission,
            app_url=self._settings.app_public_url,
        )
        return await self._send(
            to_email=to_email,
            subject=f"Access granted: {directory_name}",
            html=html,
        )

    async def _send(self, *, to_email: str, subject: str, html: str) -> bool:
        if not self.enabled:
            logger.info("Skipping email %r — RESEND_API_KEY not set", subject)
            return False

        try:
            import resend

            resend.api_key = self._settings.resend_api_key
            await resend.Emails.send_async(
                {
                    "from": self._settings.email_from,
                    "to": [to_email],
                    "subject": subject,
                    "html": html,
                },
            )
            logger.info("Sent email %r to %s", subject, to_email)
            return True
        except Exception:
            logger.exception("Failed to send email %r to %s", subject, to_email)
            return False
