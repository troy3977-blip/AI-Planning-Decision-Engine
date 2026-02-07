# config/settings.py
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """
    Centralized configuration loaded from .env and environment variables.

    Priority (highest to lowest):
      1) Environment variables
      2) .env file
      3) Defaults here
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # OpenAI
    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")
    openai_model: str = Field("gpt-4.1-mini", alias="OPENAI_MODEL")

    # App
    app_env: str = Field("local", alias="APP_ENV")
    log_level: str = Field("INFO", alias="LOG_LEVEL")


settings = Settings()