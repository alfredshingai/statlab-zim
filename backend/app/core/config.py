"""Configuration system for StatLab Zim backend.

Uses pydantic-settings to load from environment variables and .env file.
Milestone 1: Backend foundation — environment-variable support.
"""

from __future__ import annotations

from functools import lru_cache
from typing import List

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment.

    Environment variables take precedence over .env file.
    All variables can be overridden via `STATLAB_` prefix or direct name.
    """

    # App
    PROJECT_NAME: str = "StatLab Zim API"
    VERSION: str = "0.1.0"
    DESCRIPTION: str = "StatLab Zim — statistical analysis API (Version 2)"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"  # development | staging | production

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000  # Render overrides via $PORT env var at runtime

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8501",
    ]

    # File upload (Milestone 2 & 6)
    MAX_UPLOAD_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: List[str] = [".csv"]
    # Derived bytes limit (used at runtime)
    @property
    def MAX_UPLOAD_SIZE_BYTES(self) -> int:
        return self.MAX_UPLOAD_SIZE_MB * 1024 * 1024

    # Database (Milestone 3)
    DATABASE_URL: str = "sqlite:///./statlab.db"
    # For Postgres: postgresql+psycopg2://user:password@db:5432/statlab
    # Set via env var DATABASE_URL

    # Auth (Milestone 5)
    SECRET_KEY: str = "dev-secret-change-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7
    ALGORITHM: str = "HS256"

    # AI (Version 3) — provider-agnostic, no vendor lock-in
    OPENAI_API_KEY: str | None = None
    OPENAI_MODEL: str = "gpt-4o-mini"
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.1"
    AI_PROVIDER: str = "mock"  # mock | openai | ollama — mock is deterministic & free for tests
    AI_MAX_TOKENS: int = 800

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v):
        if isinstance(v, str):
            # Allow comma-separated string from env var
            return [i.strip() for i in v.split(",") if i.strip()]
        return v


@lru_cache
def get_settings() -> Settings:
    """Cached settings instance (singleton)."""
    return Settings()
