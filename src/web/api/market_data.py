"""
Market Data API endpoints for trading dashboard
"""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import and_, desc, func, select

from src.shared.database.base import db_transaction
from src.shared.database.models.market_data import MarketData
from src.shared.database.models.symbols import Symbol

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


class MarketDataStats(BaseModel):
    """Market data statistics"""

    total_records: int
    symbols_count: int
    date_range: dict
    latest_update: Optional[datetime]


class SymbolInfo(BaseModel):
    """Symbol information"""

    symbol: str
    name: Optional[str]
    exchange: Optional[str]
    sector: Optional[str]
    status: str
    record_count: int


@router.get("/stats", response_model=MarketDataStats)
async def get_market_data_stats() -> MarketDataStats:
    """Get market data statistics"""
    try:
        with db_transaction() as session:
            # Total records count
            total_records = session.scalar(select(func.count(MarketData.id)))

            # Unique symbols count
            symbols_count = session.scalar(
                select(func.count(func.distinct(MarketData.symbol)))
            )

            # Date range
            date_range_result = session.execute(
                select(
                    func.min(MarketData.timestamp).label("min_date"),
                    func.max(MarketData.timestamp).label("max_date"),
                )
            ).fetchone()

            # Latest update
            latest_update = session.scalar(select(func.max(MarketData.created_at)))

            return MarketDataStats(
                total_records=total_records or 0,
                symbols_count=symbols_count or 0,
                date_range={
                    "min_date": (
                        date_range_result.min_date.isoformat()
                        if date_range_result and date_range_result.min_date
                        else None
                    ),
                    "max_date": (
                        date_range_result.max_date.isoformat()
                        if date_range_result and date_range_result.max_date
                        else None
                    ),
                },
                latest_update=latest_update,
            )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get market data stats: {str(e)}"
        )


@router.get("/symbols", response_model=List[SymbolInfo])
async def get_available_symbols() -> List[SymbolInfo]:
    """Get list of available symbols with their data counts"""
    try:
        with db_transaction() as session:
            # Get symbols with their record counts
            query = session.execute(
                select(
                    MarketData.symbol, func.count(MarketData.id).label("record_count")
                )
                .group_by(MarketData.symbol)
                .order_by(MarketData.symbol)
            )

            symbols_data = []
            for row in query.fetchall():
                # Get additional symbol info if available
                symbol_info = session.scalar(
                    select(Symbol).where(Symbol.symbol == row.symbol)
                )

                symbols_data.append(
                    SymbolInfo(
                        symbol=row.symbol,
                        name=(
                            str(symbol_info.name)
                            if symbol_info and symbol_info.name
                            else None
                        ),
                        exchange=(
                            str(symbol_info.exchange)
                            if symbol_info and symbol_info.exchange
                            else None
                        ),
                        sector=(
                            str(symbol_info.sector)
                            if symbol_info and symbol_info.sector
                            else None
                        ),
                        status=str(symbol_info.status) if symbol_info else "unknown",
                        record_count=row.record_count,
                    )
                )

            return symbols_data

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get symbols: {str(e)}")


@router.get("/data/{symbol}", response_model=List[MarketDataResponse])
async def get_market_data(
    symbol: str,
    limit: Optional[int] = Query(
        default=None, ge=1, le=5000, description="Number of records to return (no limit if not specified)"
    ),
    offset: int = Query(default=0, ge=0, description="Number of records to skip"),
    start_date: Optional[str] = Query(
        default=None, description="Start date (ISO format)"
    ),
    end_date: Optional[str] = Query(default=None, description="End date (ISO format)"),
    data_source: Optional[str] = Query(
        default=None, description="Data source filter (polygon, yahoo, alpaca)"
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
            for record in records:
                market_data.append(
                    MarketDataResponse(
                        symbol=record.symbol,
                        timestamp=record.timestamp,
                        open=float(record.open) if record.open else None,
                        high=float(record.high) if record.high else None,
                        low=float(record.low) if record.low else None,
                        close=float(record.close) if record.close else None,
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
        default=None, description="Data source filter (polygon, yahoo, alpaca)"
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


@router.get("/data/{symbol}/count")
async def get_market_data_count(symbol: str) -> dict:
    """Get the count of market data records for a specific symbol"""
    try:
        symbol = symbol.upper()

        with db_transaction() as session:
            count = session.scalar(
                select(func.count(MarketData.id)).where(MarketData.symbol == symbol)
            )

            return {"symbol": symbol, "count": count or 0}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get count for {symbol}: {str(e)}"
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
