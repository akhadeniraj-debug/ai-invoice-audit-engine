"""Configuration settings for DocAudit-Core using Pydantic BaseSettings."""

import os
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # General App Config
    APP_NAME: str = "DocAudit-Core"
    APP_ENV: str = os.getenv("DOCAUDIT_ENV", "development")
    DEBUG: bool = False
    PORT: int = 8000

    # Relational Database (defaults to local SQLite; overridden by DATABASE_URL env or Docker MySQL)
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///docaudit.db",
    )

    # AWS Configuration
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    AWS_S3_BUCKET_NAME: str = os.getenv("AWS_S3_BUCKET_NAME", "docaudit-raw-documents")
    AWS_ACCESS_KEY_ID: Optional[str] = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY: Optional[str] = os.getenv("AWS_SECRET_ACCESS_KEY")

    # LLM Settings (Groq, Gemini, OpenAI)
    GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY")
    GROQ_MODEL: str = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
    GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
    OPENAI_API_KEY: Optional[str] = os.getenv("OPENAI_API_KEY")


settings = Settings()

