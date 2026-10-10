"""
Market Data API endpoints for trading dashboard
"""

import math
from datetime import datetime
from typing import List, Optional, Union

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import and_, desc, func, select

from src.shared.database.base import db_transaction
from src.shared.database.models.market_data import MarketData

router = APIRouter(prefix="/api/market-data", tags=["market-data"])


class MarketDataResponse(BaseModel):
    """Market data response model"""

    symbol: str
    timestamp: datetime
    open: Optional[float]
    high: Optional[float]
    low: Optional[float]
    close: Optional[float]
    volume: Optional[int]
    data_source: str


@router.get("/data/{symbol}", response_model=List[MarketDataResponse])
async def get_market_data(
    symbol: str,
    limit: Optional[int] = Query(
        default=None, ge=1, le=5000,
        description="Number of records to return (no limit if not specified)"
    ),
    offset: int = Query(default=0, ge=0, description="Number of records to skip"),
    start_date: Optional[str] = Query(
        default=None, description="Start date (ISO format)"
    ),
    end_date: Optional[str] = Query(default=None, description="End date (ISO format)"),
    data_source: Optional[str] = Query(
        default=None, description="Data source filter (yahoo, yahoo_adjusted)"
    ),
) -> List[MarketDataResponse]:
    """Get market data for a specific symbol"""
    try:
        symbol = symbol.upper()

        # Parse date strings if provided
        start_dt = None
        end_dt = None
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))

        with db_transaction() as session:
            # Build query
            query = select(MarketData).where(MarketData.symbol == symbol)

            # Add data source filter if provided
            if data_source:
                query = query.where(MarketData.data_source == data_source.lower())

            # Add date filters if provided
            if start_dt:
                query = query.where(MarketData.timestamp >= start_dt)
            if end_dt:
                query = query.where(MarketData.timestamp <= end_dt)

            # Order by timestamp descending (most recent first)
            query = query.order_by(desc(MarketData.timestamp))

            # Add pagination
            query = query.offset(offset)
            if limit is not None:
                query = query.limit(limit)

            # Execute query
            result = session.execute(query)
            records = result.scalars().all()

            # Convert to response model
            market_data = []

            def _safe_float(val: Union[str, float, int, None]) -> Optional[float]:
                if val is None:
                    return None
                f = float(val)
                return None if math.isnan(f) or math.isinf(f) else f

            for record in records:
                market_data.append(
                    MarketDataResponse(
                        symbol=record.symbol,
                        timestamp=record.timestamp,
                        open=_safe_float(record.open),
                        high=_safe_float(record.high),
                        low=_safe_float(record.low),
                        close=_safe_float(record.close),
                        volume=record.volume,
                        data_source=record.data_source,
                    )
                )

            return market_data

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get market data for {symbol}: {str(e)}"
        )


@router.get("/data/{symbol}/latest", response_model=MarketDataResponse)
async def get_latest_market_data(
    symbol: str,
    data_source: Optional[str] = Query(
        default=None, description="Data source filter (yahoo, yahoo_adjusted)"
    ),
) -> MarketDataResponse:
    """Get the latest market data for a specific symbol"""
    try:
        symbol = symbol.upper()

        with db_transaction() as session:
            # Get latest record for symbol
            query = select(MarketData).where(MarketData.symbol == symbol)

            # Add data source filter if provided
            if data_source:
                query = query.where(MarketData.data_source == data_source.lower())

            query = query.order_by(desc(MarketData.timestamp)).limit(1)

            result = session.execute(query)
            record = result.scalar_one_or_none()

            if not record:
                raise HTTPException(
                    status_code=404, detail=f"No data found for symbol {symbol}"
                )

            return MarketDataResponse(
                symbol=record.symbol,
                timestamp=record.timestamp,
                open=float(record.open) if record.open else None,
                high=float(record.high) if record.high else None,
                low=float(record.low) if record.low else None,
                close=float(record.close) if record.close else None,
                volume=record.volume,
                data_source=record.data_source,
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get latest market data for {symbol}: {str(e)}",
        )


@router.get("/data/{symbol}/sources")
async def get_available_sources(symbol: str) -> dict:
    """Get available data sources for a specific symbol"""
    try:
        symbol = symbol.upper()

        with db_transaction() as session:
            # Get distinct data sources for this symbol
            query = (
                select(MarketData.data_source, func.count(MarketData.id).label("count"))
                .where(MarketData.symbol == symbol)
                .group_by(MarketData.data_source)
                .order_by(MarketData.data_source)
            )

            result = session.execute(query)
            sources = [
                {"source": row.data_source, "record_count": row.count}
                for row in result.fetchall()
            ]

            return {"symbol": symbol, "sources": sources}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get sources for {symbol}: {str(e)}",
        )


@router.get("/data/{symbol}/ohlc", response_model=dict)
async def get_ohlc_summary(symbol: str) -> dict:
    """Get OHLC summary for a specific symbol"""
    try:
        symbol = symbol.upper()

        with db_transaction() as session:
            # Get latest record
            latest_query = (
                select(MarketData)
                .where(MarketData.symbol == symbol)
                .order_by(desc(MarketData.timestamp))
                .limit(1)
            )

            latest_record = session.execute(latest_query).scalar_one_or_none()

            if not latest_record:
                raise HTTPException(
                    status_code=404, detail=f"No data found for symbol {symbol}"
                )

            # Get previous record for change calculation
            previous_query = (
                select(MarketData)
                .where(
                    and_(
                        MarketData.symbol == symbol,
                        MarketData.timestamp < latest_record.timestamp,
                    )
                )
                .order_by(desc(MarketData.timestamp))
                .limit(1)
            )

            previous_record = session.execute(previous_query).scalar_one_or_none()

            # Calculate price change
            price_change = None
            price_change_percent = None

            if previous_record and latest_record.close and previous_record.close:
                price_change = float(latest_record.close - previous_record.close)
                price_change_percent = (
                    price_change / float(previous_record.close)
                ) * 100

            return {
                "symbol": symbol,
                "timestamp": latest_record.timestamp,
                "open": float(latest_record.open) if latest_record.open else None,
                "high": float(latest_record.high) if latest_record.high else None,
                "low": float(latest_record.low) if latest_record.low else None,
                "close": float(latest_record.close) if latest_record.close else None,
                "volume": latest_record.volume,
                "price_change": price_change,
                "price_change_percent": price_change_percent,
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get OHLC summary for {symbol}: {str(e)}"
        )
