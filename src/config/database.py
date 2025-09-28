"""
Database Configuration for Trading System
Implements the separate database strategy for Prefect 3.4.14 compatibility.
"""

import os
from typing import Dict, Optional
from sqlalchemy import create_engine, Engine
from sqlalchemy.pool import QueuePool
from pydantic_settings import BaseSettings
from pydantic import Field


class DatabaseConfig(BaseSettings):
    """Database configuration following the separate database strategy"""
    
    # Trading System Database Configuration
    postgres_host: str = Field(default="localhost", env="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, env="POSTGRES_PORT")
    postgres_user: str = Field(default="postgres", env="POSTGRES_USER")
    postgres_password: str = Field(default="", env="POSTGRES_PASSWORD")
    
    # Trading System Database
    trading_db_name: str = Field(default="trading_system", env="TRADING_DB_NAME")
    
    # Prefect Database
    prefect_db_name: str = Field(default="Prefect", env="PREFECT_DB_NAME")
    
    # Redis Configuration
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=0, env="REDIS_DB")
    redis_url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    
    # Connection Pool Settings
    pool_size: int = Field(default=10, env="DB_POOL_SIZE")
    max_overflow: int = Field(default=20, env="DB_MAX_OVERFLOW")
    pool_timeout: int = Field(default=30, env="DB_POOL_TIMEOUT")
    pool_recycle: int = Field(default=3600, env="DB_POOL_RECYCLE")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields from environment
    
    @property
    def trading_db_url(self) -> str:
        """Trading System Database URL"""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.trading_db_name}"
        )
    
    @property
    def prefect_db_url(self) -> str:
        """Prefect Database URL"""
        return (
            f"postgresql://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.prefect_db_name}"
        )
    
    @property
    def prefect_async_db_url(self) -> str:
        """Prefect Async Database URL for Prefect 3.4.14"""
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.prefect_db_name}"
        )
    
    @property
    def schemas(self) -> Dict[str, str]:
        """Service-specific schemas mapping"""
        return {
            'data_ingestion': 'data_ingestion',
            'strategy_engine': 'strategy_engine',
            'execution': 'execution',
            'risk_management': 'risk_management',
            'analytics': 'analytics',
            'notification': 'notification',
            'logging': 'logging',
            'shared': 'shared'
        }
    
    def get_engine(self, database: str = "trading", schema: Optional[str] = None) -> Engine:
        """
        Get SQLAlchemy engine for specified database and schema
        
        Args:
            database: Either 'trading' or 'prefect'
            schema: Optional schema name for trading database
            
        Returns:
            SQLAlchemy Engine instance
        """
        if database == "trading":
            url = self.trading_db_url
        elif database == "prefect":
            url = self.prefect_db_url
        else:
            raise ValueError(f"Invalid database: {database}. Must be 'trading' or 'prefect'")
        
        # Add schema to URL if specified
        if schema and database == "trading":
            url += f"?options=-csearch_path={schema}"
        
        return create_engine(
            url,
            poolclass=QueuePool,
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_timeout=self.pool_timeout,
            pool_recycle=self.pool_recycle,
            echo=False,  # Set to True for SQL debugging
        )
    
    def get_service_engine(self, service: str) -> Engine:
        """
        Get engine for specific service with appropriate schema
        
        Args:
            service: Service name (data_ingestion, strategy_engine, etc.)
            
        Returns:
            SQLAlchemy Engine instance
        """
        if service not in self.schemas:
            raise ValueError(f"Unknown service: {service}. Available: {list(self.schemas.keys())}")
        
        return self.get_engine("trading", self.schemas[service])
    
    def get_shared_engine(self) -> Engine:
        """Get engine for shared schema"""
        return self.get_engine("trading", "shared")
    
    def get_prefect_engine(self) -> Engine:
        """Get engine for Prefect database"""
        return self.get_engine("prefect")


# Global configuration instance
db_config = DatabaseConfig()


def get_database_config() -> DatabaseConfig:
    """Get the global database configuration instance"""
    return db_config


def get_engine(database: str = "trading", schema: Optional[str] = None) -> Engine:
    """Convenience function to get database engine"""
    return db_config.get_engine(database, schema)


def get_service_engine(service: str) -> Engine:
    """Convenience function to get service-specific engine"""
    return db_config.get_service_engine(service)


def get_shared_engine() -> Engine:
    """Convenience function to get shared schema engine"""
    return db_config.get_shared_engine()


def get_prefect_engine() -> Engine:
    """Convenience function to get Prefect engine"""
    return db_config.get_prefect_engine()
