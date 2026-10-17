"""
IntelliMaint AI — Application Configuration

Loads and validates environment variables using Pydantic Settings.
"""

from __future__ import annotations
import os
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    # Application Info
    APP_NAME: str = "IntelliMaint AI — Predictive Maintenance Platform"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = Field(default="development", description="Environment mode")
    DEBUG: bool = Field(default=True, description="Debug mode")
    SECRET_KEY: str = Field(
        default="intellimaint-development-secret-key-32chars-minimum-token",
        description="Application secret key",
    )

    # API Gateway
    API_HOST: str = "127.0.0.1"
    API_PORT: int = 8000
    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: list[str] = ["http://localhost:8501", "http://127.0.0.1:8501"]

    # Database
    # Primary: PostgreSQL (e.g. postgresql+psycopg2://user:pass@localhost:5432/intellimaint_db)
    # Fallback: SQLite (sqlite:///./intellimaint.db)
    DATABASE_URL: str = Field(
        default="sqlite:///./intellimaint.db",
        description="Database connection URL",
    )

    # Frontend (Streamlit)
    STREAMLIT_SERVER_PORT: int = 8501
    BACKEND_API_BASE_URL: str = "http://127.0.0.1:8000/api/v1"

    # Logging
    LOG_LEVEL: str = "INFO"

    # Paths
    BASE_DIR_PATH: Path = BASE_DIR
    MODEL_DIR_PATH: Path = BASE_DIR / "ml" / "models"
    DATA_DIR_PATH: Path = BASE_DIR / "ml" / "data"

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()
