"""Application settings loaded from environment variables."""

from functools import lru_cache

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

    database_url: str = Field(
        default="postgresql+asyncpg://knowledge_ai:knowledge_ai@localhost:5432/knowledge_ai",
    )
    redis_url: str = Field(default="redis://localhost:6379/0")


@lru_cache
def get_settings() -> Settings:
    """Return cached settings instance."""
    return Settings()


settings = get_settings()
