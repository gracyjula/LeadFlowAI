"""Application configuration loaded from environment variables."""

import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings with environment variable loading."""

    # OpenRouter
    OPENROUTER_API_KEY: str = "your-openrouter-api-key-here"
    OPENROUTER_MODEL: str = "gpt-4o-mini"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    # Database
    DATABASE_URL: str = "sqlite:///./leadflow.db"

    # App
    APP_NAME: str = "LeadFlowAI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()