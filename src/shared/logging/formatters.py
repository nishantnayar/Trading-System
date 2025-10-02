"""
Log formatting utilities
"""

import json
from datetime import datetime
from typing import Any
from typing import Any as LogRecord
from typing import Dict, Optional


def format_log_record(record: LogRecord) -> Dict[str, Any]:
    """
    Format log record for structured logging

    Args:
        record: Loguru record object

    Returns:
        Dict: Formatted log record
    """
    formatted_record = {
        "timestamp": record["time"].isoformat(),
        "level": record["level"].name,
        "message": record["message"],
        "module": record["name"],
        "function": record["function"],
        "line": record["line"],
    }

    # Add service information if available
    if "service" in record["extra"]:
        formatted_record["service"] = record["extra"]["service"]

    # Add correlation ID if available
    if "correlation_id" in record["extra"]:
        formatted_record["correlation_id"] = record["extra"]["correlation_id"]

    # Add any additional extra fields
    for key, value in record["extra"].items():
        if key not in ["service", "correlation_id"]:
            formatted_record[key] = value

    # Add exception information if present
    if record["exception"]:
        formatted_record["exception"] = {
            "type": record["exception"].type.__name__,
            "value": str(record["exception"].value),
            "traceback": record["exception"].traceback,
        }

    return formatted_record


def extract_metadata(record: LogRecord) -> Dict[str, Any]:
    """
    Extract metadata from log record

    Args:
        record: Loguru record object

    Returns:
        Dict: Extracted metadata
    """
    metadata = {}

    # Extract service information
    if "service" in record["extra"]:
        metadata["service"] = record["extra"]["service"]

    # Extract correlation ID
    if "correlation_id" in record["extra"]:
        metadata["correlation_id"] = record["extra"]["correlation_id"]

    # Extract performance metrics
    if "execution_time_ms" in record["extra"]:
        metadata["execution_time_ms"] = record["extra"]["execution_time_ms"]

    if "memory_usage_mb" in record["extra"]:
        metadata["memory_usage_mb"] = record["extra"]["memory_usage_mb"]

    # Extract trading-specific metadata
    trading_fields = [
        "trade_id",
        "order_id",
        "symbol",
        "quantity",
        "price",
        "side",
        "strategy",
        "execution_time_ms",
        "status",
        "error_message",
    ]

    for field in trading_fields:
        if field in record["extra"]:
            metadata[field] = record["extra"][field]

    # Extract any other custom metadata
    for key, value in record["extra"].items():
        if key not in ["service", "correlation_id"] and key not in trading_fields:
            metadata[key] = value

    return metadata


def format_for_database(record: LogRecord) -> Dict[str, Any]:
    """
    Format log record for database storage

    Args:
        record: Loguru record object

    Returns:
        Dict: Database-formatted record
    """
    # Base record
    db_record = {
        "timestamp": record["time"],
        "level": record["level"].name,
        "message": record["message"],
        "service": record["extra"].get("service", "unknown"),
        "correlation_id": record["extra"].get("correlation_id"),
        "metadata": extract_metadata(record),
    }

    # Add event type if available
    if "event_type" in record["extra"]:
        db_record["event_type"] = record["extra"]["event_type"]

    return db_record


def format_for_file(record: LogRecord) -> str:
    """
    Format log record for file output

    Args:
        record: Loguru record object

    Returns:
        str: Formatted log string
    """
    # Use the default Loguru format
    return record["message"]


def create_structured_message(message: str, **kwargs) -> str:
    """
    Create structured log message with metadata

    Args:
        message: Base log message
        **kwargs: Additional metadata

    Returns:
        str: Structured message
    """
    if not kwargs:
        return message

    # Create structured message
    structured_data = {k: v for k, v in kwargs.items() if v is not None}

    if structured_data:
        return f"{message} | {json.dumps(structured_data, default=str)}"

    return message


def format_performance_log(
    operation: str,
    execution_time_ms: float,
    memory_usage_mb: Optional[float] = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    Format performance log entry

    Args:
        operation: Operation name
        execution_time_ms: Execution time in milliseconds
        memory_usage_mb: Memory usage in MB (optional)
        **kwargs: Additional metadata

    Returns:
        Dict: Formatted performance log
    """
    performance_log = {
        "log_type": "performance",
        "operation": operation,
        "execution_time_ms": execution_time_ms,
        "timestamp": datetime.utcnow().isoformat(),
    }

    if memory_usage_mb is not None:
        performance_log["memory_usage_mb"] = memory_usage_mb

    # Add any additional metadata
    performance_log.update(kwargs)

    return performance_log


def format_trading_log(
    trade_id: str, symbol: str, side: str, quantity: float, price: float, **kwargs
) -> Dict[str, Any]:
    """
    Format trading log entry

    Args:
        trade_id: Trade identifier
        symbol: Trading symbol
        side: Buy or sell
        quantity: Trade quantity
        price: Trade price
        **kwargs: Additional metadata

    Returns:
        Dict: Formatted trading log
    """
    trading_log = {
        "log_type": "trading",
        "trade_id": trade_id,
        "symbol": symbol,
        "side": side,
        "quantity": quantity,
        "price": price,
        "timestamp": datetime.utcnow().isoformat(),
    }

    # Add any additional metadata
    trading_log.update(kwargs)

    return trading_log
