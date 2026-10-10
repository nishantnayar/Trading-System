"""
Application Settings Configuration
"""

import os
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # Alpaca API Configuration
    alpaca_api_key: str = Field(default="", alias="ALPACA_API_KEY")
    alpaca_secret_key: str = Field(default="", alias="ALPACA_SECRET_KEY")
    # Email Configuration (Optional)
    smtp_host: Optional[str] = Field(default=None, alias="SMTP_HOST")
    smtp_port: Optional[int] = Field(default=None, alias="SMTP_PORT")
    smtp_username: Optional[str] = Field(default=None, alias="SMTP_USERNAME")
    smtp_password: Optional[str] = Field(default=None, alias="SMTP_PASSWORD")
    smtp_from_email: Optional[str] = Field(default=None, alias="SMTP_FROM_EMAIL")
    smtp_to_email: Optional[str] = Field(default=None, alias="SMTP_TO_EMAIL")

    # Prefect Configuration (Essential)
    prefect_api_url: str = Field(
        default="http://localhost:4200/api", alias="PREFECT_API_URL"
    )

    prefect_db_connection_url: str = Field(
        default="postgresql+asyncpg://postgres:password@localhost:5432/prefect",
        alias="PREFECT_API_DATABASE_CONNECTION_URL",
    )

    prefect_work_pool_data_ingestion: str = Field(
        default="data-ingestion-pool", alias="PREFECT_WORK_POOL_DATA_INGESTION"
    )

    class Config:
        # Allow disabling .env file reading via environment variable (useful for tests)
        env_file = None if os.getenv("DISABLE_ENV_FILE") == "true" else ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from environment


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
