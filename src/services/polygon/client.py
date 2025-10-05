"""
Polygon.io API Client
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from dateutil.parser import parse as parse_datetime
from loguru import logger
from polygon import RESTClient
from polygon.rest.models import Agg

from src.config.settings import get_settings

from .exceptions import (
    PolygonAPIError,
    PolygonAuthenticationError,
    PolygonConnectionError,
    PolygonDataError,
    PolygonRateLimitError,
)
from .models import PolygonAggregateBar, PolygonMarketStatus, PolygonTickerDetails


class PolygonClient:
    """Polygon.io API Client for market data"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
    ):
        """
        Initialize Polygon client

        Args:
            api_key: Polygon API key
            base_url: Polygon API base URL
        """
        settings = get_settings()
        self.api_key = api_key or settings.polygon_api_key
        self.base_url = base_url or settings.polygon_base_url

        if not self.api_key:
            raise PolygonAuthenticationError("Polygon API key not provided")

        try:
            self.client = RESTClient(api_key=self.api_key)
            logger.info("Polygon client initialized successfully")
        except Exception as e:
            raise PolygonConnectionError(
                f"Failed to initialize Polygon client: {str(e)}"
            )

    async def get_aggregates(
        self,
        ticker: str,
        multiplier: int = 1,
        timespan: str = "day",
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
        adjusted: bool = True,
        sort: str = "asc",
        limit: int = 5000,
    ) -> List[PolygonAggregateBar]:
        """
        Get aggregate bars (OHLCV) for a ticker

        Args:
            ticker: Stock symbol
            multiplier: Size of the timespan multiplier
            timespan: Size of the time window (minute, hour, day, week, month, quarter, year)
            from_date: Start date (YYYY-MM-DD)
            to_date: End date (YYYY-MM-DD)
            adjusted: Whether results are adjusted for splits
            sort: Sort order (asc, desc)
            limit: Maximum number of results

        Returns:
            List of aggregate bars
        """
        try:
            # Default to last 30 days if no dates provided
            if not from_date:
                from_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
            if not to_date:
                to_date = datetime.now().strftime("%Y-%m-%d")

            logger.info(
                f"Fetching aggregates for {ticker} from {from_date} to {to_date}"
            )

            # Get aggregates from Polygon API
            aggs = self.client.get_aggs(
                ticker=ticker,
                multiplier=multiplier,
                timespan=timespan,
                from_=from_date,
                to=to_date,
                adjusted=adjusted,
                sort=sort,
                limit=limit,
            )

            # Convert to our data model
            bars = []
            for agg in aggs:
                try:
                    bar = PolygonAggregateBar(
                        ticker=ticker,
                        timestamp=datetime.fromtimestamp(
                            agg.timestamp / 1000, tz=timezone.utc
                        ).astimezone(),
                        open=float(agg.open),
                        high=float(agg.high),
                        low=float(agg.low),
                        close=float(agg.close),
                        volume=int(agg.volume),
                        vwap=float(agg.vwap) if agg.vwap else None,
                        transactions=(
                            int(agg.transactions) if agg.transactions else None
                        ),
                    )
                    bars.append(bar)
                except Exception as e:
                    logger.warning(f"Failed to parse aggregate bar: {e}")
                    continue

            logger.info(f"Successfully fetched {len(bars)} aggregate bars for {ticker}")
            return bars

        except Exception as e:
            if "401" in str(e) or "Unauthorized" in str(e):
                raise PolygonAuthenticationError(f"Authentication failed: {str(e)}")
            elif "429" in str(e) or "rate limit" in str(e).lower():
                raise PolygonRateLimitError(f"Rate limit exceeded: {str(e)}")
            elif "connection" in str(e).lower() or "timeout" in str(e).lower():
                raise PolygonConnectionError(f"Connection error: {str(e)}")
            else:
                raise PolygonAPIError(f"Failed to get aggregates: {str(e)}")

    async def get_ticker_details(self, ticker: str) -> PolygonTickerDetails:
        """
        Get ticker details

        Args:
            ticker: Stock symbol

        Returns:
            Ticker details
        """
        try:
            logger.info(f"Fetching ticker details for {ticker}")

            details = self.client.get_ticker_details(ticker=ticker)

            ticker_details = PolygonTickerDetails(
                ticker=details.ticker,
                name=details.name,
                market=details.market,
                locale=details.locale,
                primary_exchange=details.primary_exchange,
                type=details.type,
                active=details.active,
                currency_name=details.currency_name,
                cik=details.cik,
                composite_figi=details.composite_figi,
                share_class_figi=details.share_class_figi,
                last_updated_utc=(
                    parse_datetime(str(getattr(details, "last_updated_utc", None)))
                    if hasattr(details, "last_updated_utc")
                    and getattr(details, "last_updated_utc", None)
                    else None
                ),
            )

            logger.info(f"Successfully fetched ticker details for {ticker}")
            return ticker_details

        except Exception as e:
            if "401" in str(e) or "Unauthorized" in str(e):
                raise PolygonAuthenticationError(f"Authentication failed: {str(e)}")
            elif "404" in str(e) or "not found" in str(e).lower():
                raise PolygonDataError(f"Ticker {ticker} not found: {str(e)}")
            else:
                raise PolygonAPIError(f"Failed to get ticker details: {str(e)}")

    async def get_market_status(self) -> PolygonMarketStatus:
        """
        Get market status

        Returns:
            Market status information
        """
        try:
            logger.info("Fetching market status")

            status = self.client.get_market_status()

            market_status = PolygonMarketStatus(
                market=status.market,
                server_time=parse_datetime(status.server_time),
                exchanges=status.exchanges,
                currencies=status.currencies,
            )

            logger.info("Successfully fetched market status")
            return market_status

        except Exception as e:
            if "401" in str(e) or "Unauthorized" in str(e):
                raise PolygonAuthenticationError(f"Authentication failed: {str(e)}")
            else:
                raise PolygonAPIError(f"Failed to get market status: {str(e)}")

    async def get_daily_bars(
        self,
        ticker: str,
        days_back: int = 30,
    ) -> List[PolygonAggregateBar]:
        """
        Get daily bars for a ticker (convenience method)

        Args:
            ticker: Stock symbol
            days_back: Number of days to look back

        Returns:
            List of daily aggregate bars
        """
        to_date = datetime.now().strftime("%Y-%m-%d")
        from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

        return await self.get_aggregates(
            ticker=ticker,
            multiplier=1,
            timespan="day",
            from_date=from_date,
            to_date=to_date,
        )

    async def get_hourly_bars(
        self,
        ticker: str,
        days_back: int = 7,
    ) -> List[PolygonAggregateBar]:
        """
        Get hourly bars for a ticker (convenience method)

        Args:
            ticker: Stock symbol
            days_back: Number of days to look back

        Returns:
            List of hourly aggregate bars
        """
        to_date = datetime.now().strftime("%Y-%m-%d")
        from_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")

        return await self.get_aggregates(
            ticker=ticker,
            multiplier=1,
            timespan="hour",
            from_date=from_date,
            to_date=to_date,
        )

    async def health_check(self) -> bool:
        """
        Check if Polygon API is accessible

        Returns:
            True if API is accessible, False otherwise
        """
        try:
            await self.get_market_status()
            return True
        except Exception as e:
            logger.error(f"Polygon API health check failed: {e}")
            return False
