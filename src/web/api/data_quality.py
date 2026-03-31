"""
Data Quality API  -  ingestion timestamps, staleness, and alert endpoints.

Source of truth: data_ingestion.market_data (yahoo only).
symbol_data_status is not reliably updated so is not used here.
"""

from datetime import date, datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from sqlalchemy import func, select

from src.shared.database.base import db_transaction
from src.shared.database.models.market_data import MarketData

router = APIRouter(prefix="/api/data-quality", tags=["data-quality"])

# Warn if last market_data row is older than this many calendar days.
# 2 covers the weekend gap (Friday data seen on Sunday/Monday).
STALE_DAYS_THRESHOLD = 2
DATA_SOURCE = "yahoo"


class SymbolIngestionStatus(BaseModel):
    symbol: str
    last_date: date
    days_since_last_bar: int
    record_count: int
    is_stale: bool


class DataQualitySummary(BaseModel):
    total_symbols: int
    stale_symbols: int
    ok_symbols: int
    last_ingestion_at: Optional[datetime]
    as_of: datetime


@router.get("/summary", response_model=DataQualitySummary)
async def get_data_quality_summary() -> DataQualitySummary:
    """Overall yahoo ingestion health based on market_data timestamps."""
    try:
        today = date.today()
        with db_transaction() as session:
            rows = session.execute(
                select(
                    MarketData.symbol,
                    func.max(MarketData.timestamp).label("last_ts"),
                )
                .where(MarketData.data_source == DATA_SOURCE)
                .group_by(MarketData.symbol)
            ).fetchall()

            total = len(rows)
            stale = sum(
                1
                for r in rows
                if (today - r.last_ts.date()).days > STALE_DAYS_THRESHOLD
            )

            last_ingestion = session.scalar(
                select(func.max(MarketData.created_at)).where(
                    MarketData.data_source == DATA_SOURCE
                )
            )

            return DataQualitySummary(
                total_symbols=total,
                stale_symbols=stale,
                ok_symbols=total - stale,
                last_ingestion_at=last_ingestion,
                as_of=datetime.now(timezone.utc),
            )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get data quality summary: {e}"
        )


@router.get("/ingestion-status", response_model=List[SymbolIngestionStatus])
async def get_ingestion_status() -> List[SymbolIngestionStatus]:
    """Per-symbol last bar date and staleness flag, from market_data."""
    try:
        today = date.today()
        with db_transaction() as session:
            rows = session.execute(
                select(
                    MarketData.symbol,
                    func.max(MarketData.timestamp).label("last_ts"),
                    func.count(MarketData.id).label("record_count"),
                )
                .where(MarketData.data_source == DATA_SOURCE)
                .group_by(MarketData.symbol)
                .order_by(MarketData.symbol)
            ).fetchall()

            result = []
            for r in rows:
                last_date = r.last_ts.date()
                days = (today - last_date).days
                result.append(
                    SymbolIngestionStatus(
                        symbol=r.symbol,
                        last_date=last_date,
                        days_since_last_bar=days,
                        record_count=r.record_count,
                        is_stale=days > STALE_DAYS_THRESHOLD,
                    )
                )
            return result
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get ingestion status: {e}"
        )


@router.get("/alerts", response_model=List[SymbolIngestionStatus])
async def get_data_quality_alerts() -> List[SymbolIngestionStatus]:
    """Return only stale symbols (last bar older than threshold)."""
    all_statuses = await get_ingestion_status()
    return [s for s in all_statuses if s.is_stale]
