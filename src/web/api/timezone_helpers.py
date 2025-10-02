"""
Timezone-aware API response helpers

This module provides utilities for formatting timestamps in API responses
with proper timezone handling for the trading system UI.

Author: Nishant Nayar
Email: nishant.nayar@hotmail.com
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel

from src.shared.utils.timezone import (
    ensure_utc_timestamp,
    format_for_display,
    format_trading_time,
    to_central,
    to_eastern,
)


class TimestampResponse(BaseModel):
    """Pydantic model for timezone-aware timestamp responses"""

    timestamp: str
    timezone: str = "America/Chicago"  # Central timezone
    timestamp_utc: str
    timestamp_trading: str

    @classmethod
    def from_datetime(cls, dt: datetime):
        """
        Create TimestampResponse from datetime

        Args:
            dt: Datetime to format

        Returns:
            TimestampResponse with formatted timestamps
        """
        # Ensure UTC for consistent processing
        utc_dt = ensure_utc_timestamp(dt)

        return cls(
            timestamp=format_for_display(utc_dt),
            timezone="America/Chicago",
            timestamp_utc=utc_dt.isoformat(),
            timestamp_trading=format_trading_time(utc_dt),
        )


def format_api_timestamp(dt: datetime) -> str:
    """
    Format timestamp for API responses (Central timezone)

    Args:
        dt: Datetime to format

    Returns:
        Formatted timestamp string in Central timezone
    """
    return format_for_display(dt)


def format_trading_timestamp(dt: datetime) -> str:
    """
    Format timestamp for trading context (Eastern timezone)

    Args:
        dt: Datetime to format

    Returns:
        Formatted timestamp string in Eastern timezone
    """
    return format_trading_time(dt)


def format_api_response_with_timestamps(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format API response with timezone-aware timestamps

    Args:
        data: Response data dictionary

    Returns:
        Formatted response with timezone-aware timestamps
    """
    formatted_data = data.copy()

    # Common timestamp field names to format
    timestamp_fields = [
        "timestamp",
        "created_at",
        "updated_at",
        "executed_at",
        "trade_time",
        "order_time",
        "market_time",
        "last_updated",
    ]

    for field in timestamp_fields:
        if field in formatted_data and formatted_data[field]:
            try:
                dt = formatted_data[field]
                if isinstance(dt, str):
                    # Parse ISO string
                    dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))

                # Create timezone-aware response
                formatted_data[field] = TimestampResponse.from_datetime(dt).dict()
            except Exception:
                # If formatting fails, keep original value
                pass

    return formatted_data


def format_list_response_with_timestamps(
    data: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """
    Format list response with timezone-aware timestamps

    Args:
        data: List of response data dictionaries

    Returns:
        List of formatted responses with timezone-aware timestamps
    """
    return [format_api_response_with_timestamps(item) for item in data]


def get_current_time_info() -> Dict[str, str]:
    """
    Get current time information in all relevant timezones

    Returns:
        Dictionary with current time in different timezones
    """
    from src.shared.utils.timezone import now_central, now_eastern, now_utc

    utc_time = now_utc()
    central_time = now_central()
    eastern_time = now_eastern()

    return {
        "utc": utc_time.isoformat(),
        "central": central_time.strftime("%Y-%m-%d %H:%M:%S %Z"),
        "eastern": eastern_time.strftime("%Y-%m-%d %H:%M:%S %Z"),
        "market_status": get_market_status_info(),
    }


def get_market_status_info() -> Dict[str, Any]:
    """
    Get current market status information

    Returns:
        Dictionary with market status details
    """
    from src.shared.utils.timezone import (
        get_last_market_close,
        get_next_market_open,
        is_market_hours,
        is_weekend,
        now_eastern,
    )

    current_time = now_eastern()

    return {
        "is_market_hours": is_market_hours(current_time),
        "is_weekend": is_weekend(current_time),
        "next_market_open": get_next_market_open(current_time).isoformat(),
        "last_market_close": get_last_market_close(current_time).isoformat(),
        "current_time_eastern": current_time.strftime("%Y-%m-%d %H:%M:%S %Z"),
    }


def format_trade_timestamp(trade_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format trade data with timezone-aware timestamps

    Args:
        trade_data: Trade data dictionary

    Returns:
        Formatted trade data with timezone-aware timestamps
    """
    formatted_trade = trade_data.copy()

    # Format execution timestamp
    if "executed_at" in formatted_trade and formatted_trade["executed_at"]:
        try:
            dt = formatted_trade["executed_at"]
            if isinstance(dt, str):
                dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))

            formatted_trade["executed_at"] = TimestampResponse.from_datetime(dt).dict()
        except Exception:
            pass

    # Format order timestamp
    if "order_time" in formatted_trade and formatted_trade["order_time"]:
        try:
            dt = formatted_trade["order_time"]
            if isinstance(dt, str):
                dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))

            formatted_trade["order_time"] = TimestampResponse.from_datetime(dt).dict()
        except Exception:
            pass

    return formatted_trade


def format_market_data_timestamp(market_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format market data with timezone-aware timestamps

    Args:
        market_data: Market data dictionary

    Returns:
        Formatted market data with timezone-aware timestamps
    """
    formatted_data = market_data.copy()

    # Format timestamp
    if "timestamp" in formatted_data and formatted_data["timestamp"]:
        try:
            dt = formatted_data["timestamp"]
            if isinstance(dt, str):
                dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))

            formatted_data["timestamp"] = TimestampResponse.from_datetime(dt).dict()
        except Exception:
            pass

    return formatted_data


def format_log_entry_timestamp(log_entry: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format log entry with timezone-aware timestamps

    Args:
        log_entry: Log entry dictionary

    Returns:
        Formatted log entry with timezone-aware timestamps
    """
    formatted_log = log_entry.copy()

    # Format timestamp
    if "timestamp" in formatted_log and formatted_log["timestamp"]:
        try:
            dt = formatted_log["timestamp"]
            if isinstance(dt, str):
                dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))

            formatted_log["timestamp"] = TimestampResponse.from_datetime(dt).dict()
        except Exception:
            pass

    return formatted_log


def create_timezone_aware_response(
    data: Union[Dict[str, Any], List[Dict[str, Any]]], include_time_info: bool = True
) -> Dict[str, Any]:
    """
    Create a complete timezone-aware API response

    Args:
        data: Response data
        include_time_info: Whether to include current time information

    Returns:
        Complete timezone-aware response
    """
    response = {"data": data, "success": True}

    if include_time_info:
        response["time_info"] = get_current_time_info()

    return response
