"""
Trading System Logging Module

Provides comprehensive logging functionality with:
- Loguru-based file logging
- Service detection and configuration
- Correlation ID tracking
- Performance monitoring
- Structured logging
"""

from .logger import (
    setup_logging,
    get_logger,
    get_service_logger,
    get_config,
    LoggingManager
)

from .config import (
    load_logging_config,
    get_service_config,
    detect_service_from_module,
    LoggingConfig,
    LogRotationConfig,
    LogFilesConfig,
    DatabaseLoggingConfig,
    RetentionConfig,
    ServiceLoggingConfig,
    PerformanceLoggingConfig
)

from .formatters import (
    format_log_record,
    extract_metadata,
    format_for_database,
    format_for_file,
    create_structured_message,
    format_performance_log,
    format_trading_log
)

from .correlation import (
    generate_correlation_id,
    get_correlation_id,
    set_correlation_id,
    clear_correlation_id,
    correlation_context,
    with_correlation_id,
    get_correlation_context,
    format_correlation_message
)

from .performance import (
    log_performance,
    track_execution_time,
    log_memory_usage,
    log_database_query
)

# Re-export loguru logger for convenience
from loguru import logger

__all__ = [
    # Main logging functions
    "setup_logging",
    "get_logger", 
    "get_service_logger",
    "get_config",
    "LoggingManager",
    
    # Configuration
    "load_logging_config",
    "get_service_config",
    "detect_service_from_module",
    "LoggingConfig",
    "LogRotationConfig",
    "LogFilesConfig",
    "DatabaseLoggingConfig",
    "RetentionConfig",
    "ServiceLoggingConfig",
    "PerformanceLoggingConfig",
    
    # Formatters
    "format_log_record",
    "extract_metadata",
    "format_for_database",
    "format_for_file",
    "create_structured_message",
    "format_performance_log",
    "format_trading_log",
    
    # Correlation ID management
    "generate_correlation_id",
    "get_correlation_id",
    "set_correlation_id",
    "clear_correlation_id",
    "correlation_context",
    "with_correlation_id",
    "get_correlation_context",
    "format_correlation_message",
    
    # Performance tracking
    "log_performance",
    "track_execution_time",
    "log_memory_usage",
    "log_database_query",
    
    # Loguru logger
    "logger"
]
