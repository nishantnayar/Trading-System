"""
Application Settings Configuration
"""

from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings with environment variable support"""

    # Application Configuration
    app_name: str = Field(default="Trading System", env="APP_NAME")
    app_version: str = Field(default="1.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # Database Configuration
    postgres_host: str = Field(default="localhost", env="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, env="POSTGRES_PORT")
    postgres_user: str = Field(default="postgres", env="POSTGRES_USER")
    postgres_password: str = Field(default="", env="POSTGRES_PASSWORD")
    trading_db_name: str = Field(default="trading_system", env="TRADING_DB_NAME")
    prefect_db_name: str = Field(default="Prefect", env="PREFECT_DB_NAME")

    # Redis Configuration
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")

    # Alpaca API Configuration
    alpaca_api_key: str = Field(default="", env="ALPACA_API_KEY")
    alpaca_secret_key: str = Field(default="", env="ALPACA_SECRET_KEY")
    alpaca_base_url: str = Field(
        default="https://paper-api.alpaca.markets", env="ALPACA_BASE_URL"
    )
    alpaca_data_url: str = Field(
        default="https://data.alpaca.markets", env="ALPACA_DATA_URL"
    )

    # Prefect Configuration
    prefect_api_url: str = Field(default="http://localhost:4200", env="PREFECT_API_URL")
    prefect_database_url: str = Field(
        default="", env="PREFECT_API_DATABASE_CONNECTION_URL"
    )

    # Security Configuration
    secret_key: str = Field(default="", env="SECRET_KEY")
    jwt_secret_key: str = Field(default="", env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(
        default=30, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )

    # Trading Configuration
    paper_trading: bool = Field(default=True, env="PAPER_TRADING")
    max_position_size: float = Field(default=0.15, env="MAX_POSITION_SIZE")
    max_daily_loss: float = Field(default=0.05, env="MAX_DAILY_LOSS")
    max_drawdown: float = Field(default=0.10, env="MAX_DRAWDOWN")

    # Risk Management
    risk_enabled: bool = Field(default=True, env="RISK_ENABLED")
    circuit_breaker_enabled: bool = Field(default=True, env="CIRCUIT_BREAKER_ENABLED")
    max_orders_per_hour: int = Field(default=50, env="MAX_ORDERS_PER_HOUR")
    max_orders_per_day: int = Field(default=200, env="MAX_ORDERS_PER_DAY")

    # Logging Configuration
    log_file_path: str = Field(default="logs/trading.log", env="LOG_FILE_PATH")
    log_retention_days: int = Field(default=30, env="LOG_RETENTION_DAYS")
    log_rotation_size: str = Field(default="10MB", env="LOG_ROTATION_SIZE")

    # Email Configuration (Optional)
    smtp_host: Optional[str] = Field(default=None, env="SMTP_HOST")
    smtp_port: Optional[int] = Field(default=None, env="SMTP_PORT")
    smtp_username: Optional[str] = Field(default=None, env="SMTP_USERNAME")
    smtp_password: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    smtp_from_email: Optional[str] = Field(default=None, env="SMTP_FROM_EMAIL")

    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get the global settings instance"""
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
