"""
Polygon.io API Data Models
"""

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class PolygonAggregateBar(BaseModel):
    """Single aggregate bar (OHLCV) from Polygon.io"""

    ticker: str = Field(description="Stock symbol")
    timestamp: datetime = Field(description="Bar timestamp")
    open: float = Field(description="Opening price")
    high: float = Field(description="High price")
    low: float = Field(description="Low price")
    close: float = Field(description="Closing price")
    volume: int = Field(description="Trading volume")
    vwap: Optional[float] = Field(
        default=None, description="Volume weighted average price"
    )
    transactions: Optional[int] = Field(
        default=None, description="Number of transactions"
    )

    class Config:
        """Pydantic configuration"""

        json_encoders = {datetime: lambda v: v.isoformat()}


class PolygonTickerDetails(BaseModel):
    """Ticker details from Polygon.io"""

    ticker: str = Field(description="Stock symbol")
    name: str = Field(description="Company name")
    market: str = Field(description="Market identifier")
    locale: str = Field(description="Locale identifier")
    primary_exchange: str = Field(description="Primary exchange")
    type: str = Field(description="Security type")
    active: bool = Field(description="Whether ticker is active")
    currency_name: str = Field(description="Currency name")
    cik: Optional[str] = Field(default=None, description="CIK identifier")
    composite_figi: Optional[str] = Field(default=None, description="Composite FIGI")
    share_class_figi: Optional[str] = Field(
        default=None, description="Share class FIGI"
    )
    last_updated_utc: Optional[datetime] = Field(
        default=None, description="Last updated timestamp"
    )


class PolygonMarketStatus(BaseModel):
    """Market status from Polygon.io"""

    market: str = Field(description="Market identifier")
    server_time: datetime = Field(description="Server timestamp")
    exchanges: Any = Field(description="Exchange statuses")
    currencies: Any = Field(description="Currency statuses")


class PolygonResponse(BaseModel):
    """Base response wrapper for Polygon API"""

    status: str = Field(description="Response status")
    request_id: Optional[str] = Field(default=None, description="Request identifier")
    count: Optional[int] = Field(default=None, description="Number of results")
    next_url: Optional[str] = Field(default=None, description="Next page URL")


class PolygonAggregatesResponse(PolygonResponse):
    """Response wrapper for aggregates data"""

    results: List[dict] = Field(description="Aggregate bar results")
    adjusted: bool = Field(default=True, description="Whether data is adjusted")


class PolygonTickerDetailsResponse(PolygonResponse):
    """Response wrapper for ticker details"""

    results: PolygonTickerDetails = Field(description="Ticker details")


class PolygonMarketStatusResponse(PolygonResponse):
    """Response wrapper for market status"""

    results: PolygonMarketStatus = Field(description="Market status")
