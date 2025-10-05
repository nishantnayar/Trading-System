"""
Prefect flows for data ingestion
"""

import asyncio
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from loguru import logger
from prefect import flow, task
from prefect.task_runners import ConcurrentTaskRunner

from .historical_loader import HistoricalDataLoader
from .symbols import SymbolService


@task(name="load_historical_data_single_symbol")
async def load_historical_data_single_symbol(
    symbol: str,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    days_back: Optional[int] = None,
    batch_size: int = 100,
    requests_per_minute: int = 2,
    timespan: str = "day",
    multiplier: int = 1,
    incremental: bool = True,
    force_full: bool = False,
) -> Dict[str, Any]:
    """
    Load historical data for a single symbol

    Args:
        symbol: Stock symbol
        from_date: Start date
        to_date: End date
        days_back: Number of days to look back from today
        batch_size: Batch size for database inserts
        requests_per_minute: Maximum requests per minute
        timespan: Data granularity
        multiplier: Number of timespans to aggregate
        incremental: Whether to use incremental loading
        force_full: Force full reload even if incremental data exists

    Returns:
        Dictionary with loading results
    """
    logger.info(f"Starting historical data load for {symbol}")

    loader = HistoricalDataLoader(
        batch_size=batch_size, requests_per_minute=requests_per_minute
    )

    try:
        records_count = await loader.load_symbol_data(
            symbol=symbol,
            from_date=from_date,
            to_date=to_date,
            days_back=days_back,
            timespan=timespan,
            multiplier=multiplier,
            incremental=incremental,
            force_full=force_full,
        )

        result = {
            "symbol": symbol,
            "records_loaded": records_count,
            "status": "success",
            "error": None,
        }

        logger.info(f"Successfully loaded {records_count} records for {symbol}")
        return result

    except Exception as e:
        error_msg = f"Failed to load data for {symbol}: {str(e)}"
        logger.error(error_msg)

        result = {
            "symbol": symbol,
            "records_loaded": 0,
            "status": "failed",
            "error": error_msg,
        }

        return result


@task(name="load_historical_data_batch")
async def load_historical_data_batch(
    symbols: List[str],
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    days_back: Optional[int] = None,
    batch_size: int = 100,
    requests_per_minute: int = 2,
    timespan: str = "day",
    multiplier: int = 1,
    incremental: bool = True,
    force_full: bool = False,
) -> Dict[str, Any]:
    """
    Load historical data for a batch of symbols

    Args:
        symbols: List of stock symbols
        from_date: Start date
        to_date: End date
        days_back: Number of days to look back from today
        batch_size: Batch size for database inserts
        requests_per_minute: Maximum requests per minute
        timespan: Data granularity
        multiplier: Number of timespans to aggregate
        incremental: Whether to use incremental loading
        force_full: Force full reload even if incremental data exists

    Returns:
        Dictionary with batch loading results
    """
    logger.info(f"Starting batch historical data load for {len(symbols)} symbols")

    loader = HistoricalDataLoader(
        batch_size=batch_size, requests_per_minute=requests_per_minute
    )

    stats: Dict[str, Any] = {
        "total_symbols": len(symbols),
        "successful": 0,
        "failed": 0,
        "total_records": 0,
        "results": [],
        "errors": [],
    }

    for i, symbol in enumerate(symbols, 1):
        logger.info(f"Processing symbol {i}/{len(symbols)}: {symbol}")

        try:
            records_count = await loader.load_symbol_data(
                symbol=symbol,
                from_date=from_date,
                to_date=to_date,
                days_back=days_back,
                timespan=timespan,
                multiplier=multiplier,
                incremental=incremental,
                force_full=force_full,
            )

            stats["successful"] += 1
            stats["total_records"] += records_count
            stats["results"].append(
                {
                    "symbol": symbol,
                    "records_loaded": records_count,
                    "status": "success",
                }
            )

            # Add delay between requests to respect rate limits
            if i < len(symbols):
                await asyncio.sleep(60.0 / requests_per_minute)

        except Exception as e:
            stats["failed"] += 1
            error_msg = f"Symbol {symbol}: {str(e)}"
            stats["errors"].append(error_msg)
            stats["results"].append(
                {
                    "symbol": symbol,
                    "records_loaded": 0,
                    "status": "failed",
                    "error": error_msg,
                }
            )

            logger.error(error_msg)
            continue

    logger.info(f"Batch loading completed. Stats: {stats}")
    return stats


@task(name="get_active_symbols")
async def get_active_symbols() -> List[str]:
    """
    Get list of active symbols

    Returns:
        List of active symbol strings
    """
    symbol_service = SymbolService()
    symbols = await symbol_service.get_active_symbols()
    return [str(symbol.symbol) for symbol in symbols]


@task(name="detect_delisted_symbols")
async def detect_delisted_symbols() -> List[str]:
    """
    Detect and mark delisted symbols

    Returns:
        List of delisted symbol strings
    """
    symbol_service = SymbolService()
    delisted_symbols = await symbol_service.detect_delisted_symbols()
    return delisted_symbols


@task(name="get_loading_progress")
async def get_loading_progress(from_date: date, to_date: date) -> Dict[str, Any]:
    """
    Get loading progress for date range

    Args:
        from_date: Start date
        to_date: End date

    Returns:
        Dictionary with progress information
    """
    loader = HistoricalDataLoader()
    progress = await loader.get_loading_progress(from_date, to_date)
    return progress


@flow(
    name="load_historical_data_flow",
    description="Load historical market data from Polygon.io",
    task_runner=ConcurrentTaskRunner(),
)
async def load_historical_data_flow(
    symbols: Optional[List[str]] = None,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    days_back: Optional[int] = None,
    batch_size: int = 100,
    requests_per_minute: int = 2,
    max_concurrent_batches: int = 3,
    symbol_batch_size: int = 50,
    timespan: str = "day",
    multiplier: int = 1,
    incremental: bool = True,
    force_full: bool = False,
) -> Dict[str, Any]:
    """
    Main flow for loading historical market data

    Args:
        symbols: List of symbols to load (if None, loads all active symbols)
        from_date: Start date
        to_date: End date
        days_back: Number of days to look back from today
        batch_size: Batch size for database inserts
        requests_per_minute: Maximum requests per minute
        max_concurrent_batches: Maximum number of concurrent symbol batches
        symbol_batch_size: Number of symbols per batch
        timespan: Data granularity
        multiplier: Number of timespans to aggregate
        incremental: Whether to use incremental loading
        force_full: Force full reload even if incremental data exists

    Returns:
        Dictionary with overall loading results
    """
    logger.info("Starting historical data loading flow")

    # Determine date range
    if days_back:
        to_date = to_date or date.today()
        from_date = from_date or (to_date - timedelta(days=days_back))
    elif not from_date:
        from_date = date.today() - timedelta(days=30)
        to_date = to_date or date.today()

    logger.info(f"Date range: {from_date} to {to_date}")

    # Get symbols to process
    if symbols is None:
        symbols = await get_active_symbols()

    logger.info(f"Processing {len(symbols)} symbols")

    # Split symbols into batches for concurrent processing
    symbol_batches = [
        symbols[i : i + symbol_batch_size]
        for i in range(0, len(symbols), symbol_batch_size)
    ]

    # Process batches concurrently (with limit)
    batch_tasks = []
    for batch in symbol_batches:
        task = load_historical_data_batch(
            symbols=batch,
            from_date=from_date,
            to_date=to_date,
            days_back=days_back,
            batch_size=batch_size,
            requests_per_minute=requests_per_minute,
            timespan=timespan,
            multiplier=multiplier,
            incremental=incremental,
            force_full=force_full,
        )
        batch_tasks.append(task)

        # Limit concurrent batches
        if len(batch_tasks) >= max_concurrent_batches:
            # Wait for some batches to complete
            completed_batches = await asyncio.gather(*batch_tasks)
            batch_tasks = []

    # Process remaining batches
    if batch_tasks:
        completed_batches = await asyncio.gather(*batch_tasks)

    # Aggregate results
    overall_stats: Dict[str, Any] = {
        "total_symbols": len(symbols),
        "successful": 0,
        "failed": 0,
        "total_records": 0,
        "results": [],
        "errors": [],
        "date_range": {"from_date": from_date, "to_date": to_date},
    }

    for batch_result in completed_batches:
        overall_stats["successful"] += batch_result["successful"]
        overall_stats["failed"] += batch_result["failed"]
        overall_stats["total_records"] += batch_result["total_records"]
        overall_stats["results"].extend(batch_result["results"])
        overall_stats["errors"].extend(batch_result["errors"])

    logger.info("Historical data loading flow completed")
    logger.info(f"Overall stats: {overall_stats}")

    return overall_stats


@flow(
    name="daily_data_ingestion_flow",
    description="Daily data ingestion workflow",
)
async def daily_data_ingestion_flow(
    days_back: int = 1,
    batch_size: int = 100,
    requests_per_minute: int = 2,
    incremental: bool = True,
    force_full: bool = False,
) -> Dict[str, Any]:
    """
    Daily data ingestion flow - loads data for the past N days

    Args:
        days_back: Number of days to look back
        batch_size: Batch size for database inserts
        requests_per_minute: Maximum requests per minute
        incremental: Whether to use incremental loading
        force_full: Force full reload even if incremental data exists

    Returns:
        Dictionary with loading results
    """
    logger.info(f"Starting daily data ingestion for {days_back} days back")

    # First, detect any delisted symbols
    delisted_symbols = await detect_delisted_symbols()
    if delisted_symbols:
        logger.info(
            f"Detected {len(delisted_symbols)} delisted symbols: {delisted_symbols}"
        )

    # Load historical data
    result = await load_historical_data_flow(
        symbols=None,  # Load all active symbols
        days_back=days_back,
        batch_size=batch_size,
        requests_per_minute=requests_per_minute,
        incremental=incremental,
        force_full=force_full,
    )

    # Add delisted symbols info to result
    result["delisted_symbols"] = delisted_symbols

    logger.info("Daily data ingestion completed")
    return result


@flow(
    name="backfill_historical_data_flow",
    description="Backfill historical data for a date range",
)
async def backfill_historical_data_flow(
    from_date: date,
    to_date: date,
    symbols: Optional[List[str]] = None,
    batch_size: int = 100,
    requests_per_minute: int = 2,
    incremental: bool = False,  # Backfill is typically full reload
    force_full: bool = True,  # Force full reload for backfill
) -> Dict[str, Any]:
    """
    Backfill historical data for a specific date range

    Args:
        from_date: Start date
        to_date: End date
        symbols: List of symbols to backfill (if None, backfills all active symbols)
        batch_size: Batch size for database inserts
        requests_per_minute: Maximum requests per minute
        incremental: Whether to use incremental loading (typically False for backfill)
        force_full: Force full reload even if incremental data exists (typically True for backfill)

    Returns:
        Dictionary with backfill results
    """
    logger.info(f"Starting historical data backfill from {from_date} to {to_date}")

    result = await load_historical_data_flow(
        symbols=symbols,
        from_date=from_date,
        to_date=to_date,
        batch_size=batch_size,
        requests_per_minute=requests_per_minute,
        incremental=incremental,
        force_full=force_full,
    )

    logger.info("Historical data backfill completed")
    return result


@flow(
    name="symbol_health_check_flow",
    description="Check health of all symbols and detect delisted ones",
)
async def symbol_health_check_flow() -> Dict[str, Any]:
    """
    Check health of all symbols and detect delisted ones

    Returns:
        Dictionary with health check results
    """
    logger.info("Starting symbol health check")

    # Detect delisted symbols
    delisted_symbols = await detect_delisted_symbols()

    # Get symbol statistics
    symbol_service = SymbolService()
    stats = await symbol_service.get_symbol_statistics()

    result = {
        "delisted_symbols": delisted_symbols,
        "symbol_statistics": stats,
        "timestamp": datetime.now(),
    }

    logger.info(f"Symbol health check completed: {result}")
    return result
