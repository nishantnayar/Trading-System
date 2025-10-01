"""
Main logging setup and configuration
"""
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from loguru import logger as loguru_logger

from .config import load_logging_config, get_service_config, detect_service_from_module, LoggingConfig


class LoggingManager:
    """Manages logging configuration and setup"""
    
    def __init__(self, config: Optional[LoggingConfig] = None):
        self.config = config or load_logging_config()
        self._setup_complete = False
        self._service_loggers: Dict[str, Any] = {}
    
    def setup_logging(self, service_name: Optional[str] = None) -> None:
        """
        Setup Loguru logging with file and database handlers
        
        Args:
            service_name: Optional service name for service-specific setup
        """
        if self._setup_complete:
            return
        
        # Remove default handler
        loguru_logger.remove()
        
        # Setup console handler
        self._setup_console_handler()
        
        # Setup file handlers
        self._setup_file_handlers()
        
        # Setup service-specific handler if provided
        if service_name:
            self._setup_service_handler(service_name)
        
        # Setup database handler if enabled
        if self.config.database.enabled:
            self._setup_database_handler()
        
        self._setup_complete = True
    
    def _setup_console_handler(self) -> None:
        """Setup console logging handler"""
        loguru_logger.add(
            sys.stderr,
            level=self.config.root_level,
            format=self.config.format,
            colorize=True,
            backtrace=True,
            diagnose=True
        )
    
    def _setup_file_handlers(self) -> None:
        """Setup file logging handlers"""
        # Ensure logs directory exists
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # Main log file
        loguru_logger.add(
            self.config.files.main,
            level=self.config.level,
            format=self.config.format,
            rotation=self.config.rotation.size,
            retention=self.config.rotation.retention,
            compression="gz" if self.config.rotation.compression else None,
            backtrace=True,
            diagnose=True
        )
        
        # Error log file
        loguru_logger.add(
            self.config.files.errors,
            level="ERROR",
            format=self.config.format,
            rotation=self.config.rotation.size,
            retention=self.config.retention.error_logs_retention if hasattr(self.config.retention, 'error_logs_retention') else "90 days",
            compression="gz" if self.config.rotation.compression else None,
            backtrace=True,
            diagnose=True
        )
        
        # System log file
        loguru_logger.add(
            self.config.files.system,
            level="INFO",
            format=self.config.format,
            rotation=self.config.rotation.size,
            retention=self.config.rotation.retention,
            compression="gz" if self.config.rotation.compression else None,
            backtrace=True,
            diagnose=True
        )
        
        # Performance log file
        if self.config.performance.enabled:
            loguru_logger.add(
                self.config.files.performance,
                level="INFO",
                format=self.config.format,
                rotation=self.config.rotation.size,
                retention=self.config.rotation.retention,
                compression="gz" if self.config.rotation.compression else None,
                backtrace=True,
                diagnose=True,
                filter=lambda record: record["extra"].get("log_type") == "performance"
            )
    
    def _setup_service_handler(self, service_name: str) -> None:
        """Setup service-specific logging handler"""
        service_config = get_service_config(service_name, self.config)
        
        # Ensure logs directory exists
        logs_dir = Path("logs")
        logs_dir.mkdir(exist_ok=True)
        
        # Service-specific log file
        loguru_logger.add(
            service_config.file,
            level=service_config.level,
            format=self.config.format,
            rotation=self.config.rotation.size,
            retention=self.config.rotation.retention,
            compression="gz" if self.config.rotation.compression else None,
            backtrace=True,
            diagnose=True,
            filter=lambda record: record["extra"].get("service") == service_name
        )
    
    def _setup_database_handler(self) -> None:
        """Setup database logging handler (placeholder for Phase 2)"""
        # This will be implemented in Phase 2
        pass
    
    def get_logger(self, module_name: str) -> Any:
        """
        Get logger for a specific module with automatic service detection
        
        Args:
            module_name: Full module name (e.g., '__main__' or 'src.services.execution.order_manager')
            
        Returns:
            Logger: Configured logger instance
        """
        if not self._setup_complete:
            self.setup_logging()
        
        # Detect service from module name
        service_name = detect_service_from_module(module_name)
        
        # Create logger with service context
        logger = loguru_logger.bind(service=service_name)
        
        return logger
    
    def get_service_logger(self, service_name: str) -> Any:
        """
        Get logger for a specific service
        
        Args:
            service_name: Name of the service
            
        Returns:
            Logger: Configured logger instance
        """
        if not self._setup_complete:
            self.setup_logging(service_name)
        
        # Create logger with service context
        logger = loguru_logger.bind(service=service_name)
        
        return logger


# Global logging manager instance
_logging_manager = LoggingManager()


def setup_logging(config_path: Optional[str] = None, service_name: Optional[str] = None) -> None:
    """
    Setup Loguru logging with file and database handlers
    
    Args:
        config_path: Path to YAML configuration file
        service_name: Optional service name for service-specific setup
    """
    global _logging_manager
    
    if config_path:
        _logging_manager = LoggingManager(load_logging_config(config_path))
    
    _logging_manager.setup_logging(service_name)


def get_logger(module_name: str) -> Any:
    """
    Get logger for a specific module with automatic service detection
    
    Args:
        module_name: Full module name (e.g., '__main__' or 'src.services.execution.order_manager')
        
    Returns:
        Logger: Configured logger instance
    """
    return _logging_manager.get_logger(module_name)


def get_service_logger(service_name: str) -> Any:
    """
    Get logger for a specific service
    
    Args:
        service_name: Name of the service
        
    Returns:
        Logger: Configured logger instance
    """
    return _logging_manager.get_service_logger(service_name)


def get_config() -> LoggingConfig:
    """
    Get current logging configuration
    
    Returns:
        LoggingConfig: Current configuration
    """
    return _logging_manager.config
