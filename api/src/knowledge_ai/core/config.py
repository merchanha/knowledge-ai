"""Application settings loaded from environment variables."""

from functools import lru_cache
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Runtime configuration for the Knowledge-AI API."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Knowledge-AI API"
    app_version: str = "0.1.0"
    debug: bool = False

    cors_origins: list[str] = Field(default=["http://localhost:5173"])

    google_client_id: str = Field(default="")
    google_client_secret: str = Field(default="")
    google_redirect_uri: str = Field(
        default="http://localhost:8000/api/v1/auth/google/callback",
    )

    jwt_secret_key: str = Field(default="change-me-in-production")
    jwt_algorithm: str = "HS256"
    jwt_access_token_expire_minutes: int = 15
    jwt_refresh_token_expire_days: int = 7
    oauth_state_expire_minutes: int = 10

    refresh_cookie_name: str = "refresh_token"
    refresh_cookie_path: str = "/api/v1/auth"
    refresh_cookie_secure: bool = False
    refresh_cookie_samesite: Literal["lax", "strict", "none"] = "lax"

    database_url: str = Field(
        default="postgresql+asyncpg://knowledge_ai:knowledge_ai@localhost:5432/knowledge_ai",
    )
    redis_url: str = Field(default="redis://localhost:6379/0")

    voyage_api_key: str = Field(default="")
    voyage_model: str = Field(default="voyage-code-3")
    voyage_embedding_dimensions: int = Field(default=1024)
    # Drop weak nearest-neighbors so gibberish queries do not look like hits.
    search_min_similarity: float = Field(default=0.45, ge=0.0, le=1.0)

    mcp_issuer_url: str = Field(default="http://localhost:8000")
    mcp_client_id: str = Field(default="knowledge-ai-mcp")
    mcp_google_redirect_uri: str = Field(
        default="http://localhost:8000/api/v1/auth/mcp/callback",
    )
    mcp_auth_code_expire_minutes: int = 10

    # Rate limiting (Week 22) — Redis fixed-window counters
    rate_limit_enabled: bool = True
    rate_limit_window_seconds: int = Field(default=60, ge=1)
    rate_limit_search_per_window: int = Field(default=30, ge=1)
    rate_limit_auth_per_window: int = Field(default=20, ge=1)

    # Sentry (Week 22) — empty DSN skips init
    sentry_dsn: str = Field(default="")
    sentry_traces_sample_rate: float = Field(default=0.1, ge=0.0, le=1.0)
    sentry_environment: str = Field(default="development")

    # Transactional email via Resend (Week 22)
    resend_api_key: str = Field(default="")
    email_from: str = Field(default="Knowledge-AI <onboarding@resend.dev>")
    app_public_url: str = Field(default="http://localhost:5173")


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()


settings = get_settings()
