"""Unit tests for EmailService (no network when Resend key is missing)."""

from knowledge_ai.core.config import Settings
from knowledge_ai.services.email import EmailService


async def test_send_welcome_skips_without_api_key() -> None:
    service = EmailService(Settings(resend_api_key=""))
    sent = await service.send_welcome(to_email="a@example.com", full_name="Ada")
    assert sent is False
    assert service.enabled is False


async def test_send_permission_granted_renders_without_key() -> None:
    service = EmailService(Settings(resend_api_key=""))
    sent = await service.send_permission_granted(
        to_email="a@example.com",
        full_name=None,
        directory_name="Docs",
        permission="READ",
    )
    assert sent is False
