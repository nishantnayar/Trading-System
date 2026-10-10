"""
Market data access for the strategy engine, backtests, discovery and Pair Lab.

This is the one place that reads close prices from data_ingestion.market_data -
do not add per-module queries.

PRICE_SOURCE ('yahoo_adjusted') holds split/dividend-adjusted 1h bars for the
whole universe. The daily Yahoo flow loads them, and refresh_pair_prices_task
in pairs_flow.py upserts fresh bars for active pair/basket symbols before each
cycle, so live trading, discovery and backtests all read the same series.
Timestamps are UTC (bar open time).
"""

from datetime import date, datetime, time, timedelta, timezone
from typing import Dict, List

import pandas as pd
from loguru import logger
from sqlalchemy import and_, select, text

from src.shared.database.base import db_readonly_session
from src.shared.database.models.market_data import MarketData

PRICE_SOURCE = "yahoo_adjusted"


def get_price_series(symbol: str, limit: int = 500) -> pd.Series:
    """
    Return the last `limit` hourly adjusted close prices for `symbol`.

    Returns a pd.Series of float close prices indexed by UTC-aware
    timestamps, sorted oldest-first. Returns an empty Series if no data exists.
    """
    sql = text("""
        SELECT timestamp, close
        FROM data_ingestion.market_data
        WHERE symbol     = :symbol
          AND data_source = :src
          AND close IS NOT NULL
        ORDER BY timestamp DESC
        LIMIT :lim
        """)
    try:
        with db_readonly_session() as session:
            rows = session.execute(
                sql,
                {"symbol": symbol, "src": PRICE_SOURCE, "lim": limit},
            ).fetchall()
    except Exception as exc:
        logger.error(f"DB error fetching price series for {symbol}: {exc}")
        return pd.Series(dtype=float, name=symbol)

    if not rows:
        logger.warning(f"No {PRICE_SOURCE} bars in DB for {symbol}")
        return pd.Series(dtype=float, name=symbol)

    # rows are newest-first; reverse so the Series is oldest-first
    timestamps = [r[0] for r in reversed(rows)]
    closes = [float(r[1]) for r in reversed(rows)]

    idx = pd.DatetimeIndex(pd.to_datetime(timestamps, utc=True), name="timestamp")
    series = pd.Series(closes, index=idx, name=symbol, dtype=float)

    logger.debug(
        f"get_price_series({symbol}): {len(series)} bars "
        f"{series.index[0]} -> {series.index[-1]} last_close={series.iloc[-1]:.4f}"
    )
    return series


def get_close_panel(
    symbols: List[str],
    start_date: date,
    end_date: date,
    data_source: str = PRICE_SOURCE,
) -> pd.DataFrame:
    """
    Hourly close prices for `symbols` between start_date and end_date
    (both inclusive, UTC calendar days).

    Returns a DataFrame indexed by UTC timestamp with one column per symbol
    (NaN where a symbol has no bar). Empty DataFrame if nothing matched.
    """
    start_ts = datetime.combine(start_date, time.min, tzinfo=timezone.utc)
    end_ts = datetime.combine(
        end_date + timedelta(days=1), time.min, tzinfo=timezone.utc
    )
    with db_readonly_session() as session:
        stmt = (
            select(MarketData.timestamp, MarketData.symbol, MarketData.close)
            .where(
                and_(
                    MarketData.symbol.in_(symbols),
                    MarketData.data_source == data_source,
                    MarketData.timestamp >= start_ts,
                    MarketData.timestamp < end_ts,
                    MarketData.close.isnot(None),
                )
            )
            .order_by(MarketData.timestamp)
        )
        rows = session.execute(stmt).fetchall()

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows, columns=["timestamp", "symbol", "close"])
    df["close"] = df["close"].astype(float)
    pivot = df.pivot_table(
        index="timestamp", columns="symbol", values="close", aggfunc="last"
    )
    pivot.index = pd.to_datetime(pivot.index, utc=True)
    pivot.sort_index(inplace=True)
    if not isinstance(pivot, pd.DataFrame):
        raise TypeError("internal: pivot_table must return DataFrame")
    return pivot


def get_close_series(
    symbols: List[str],
    start_date: date,
    end_date: date,
    data_source: str = PRICE_SOURCE,
) -> Dict[str, pd.Series]:
    """Per-symbol close series (NaNs dropped) - see get_close_panel()."""
    panel = get_close_panel(symbols, start_date, end_date, data_source)
    return {
        sym: (
            panel[sym].dropna().rename(sym)
            if sym in panel.columns
            else pd.Series(dtype=float, name=sym)
        )
        for sym in symbols
    }
