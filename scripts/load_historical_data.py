#!/usr/bin/env python3
"""
Historical Data Loader for Polygon.io

This script loads historical market data from Polygon.io into the database.

Usage:
    python scripts/load_historical_data.py --symbol AAPL --days 365
    python scripts/load_historical_data.py --all-symbols --days 30
    python scripts/load_historical_data.py --symbol AAPL --from-date 2023-01-01 --to-date 2023-12-31
"""

import asyncio
import os
import sys
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional

import click

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from loguru import logger

from src.services.data_ingestion.historical_loader import HistoricalDataLoader
from src.services.data_ingestion.symbols import SymbolService
from src.shared.logging import setup_logging


def _update_symbol_status(
    symbol: str, status: str, error_message: Optional[str] = None
):
    """Update symbol data ingestion status"""
    try:
        symbol_service = SymbolService()
        asyncio.run(
            symbol_service.update_symbol_data_status(
                symbol=symbol,
                date=date.today(),
                data_source="polygon",
                status=status,
                error_message=error_message,
            )
        )
    except Exception as e:
        # Make this non-blocking - log warning but don't fail the main process
        logger.warning(f"Failed to update symbol status for {symbol}: {e}")


async def load_symbol_data(
    symbol: str,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    days_back: Optional[int] = None,
    timespan: str = "day",
    multiplier: int = 1,
    incremental: bool = True,
    force_full: bool = False,
) -> int:
    """Load historical data for a single symbol"""
    loader = HistoricalDataLoader()
    return await loader.load_symbol_data(
        symbol=symbol,
        from_date=from_date,
        to_date=to_date,
        days_back=days_back,
        timespan=timespan,
        multiplier=multiplier,
        incremental=incremental,
        force_full=force_full,
    )


async def load_all_symbols_data(
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    days_back: Optional[int] = None,
    max_symbols: Optional[int] = None,
    timespan: str = "day",
    multiplier: int = 1,
    incremental: bool = True,
    force_full: bool = False,
) -> dict:
    """Load historical data for all active symbols"""
    loader = HistoricalDataLoader()
    return await loader.load_all_symbols_data(
        from_date=from_date,
        to_date=to_date,
        days_back=days_back,
        max_symbols=max_symbols,
        timespan=timespan,
        multiplier=multiplier,
        incremental=incremental,
        force_full=force_full,
    )


@click.command()
@click.option(
    "--symbol",
    type=str,
    help="Stock symbol to load data for (e.g., AAPL)",
)
@click.option(
    "--all-symbols",
    is_flag=True,
    help="Load data for all active symbols",
)
@click.option(
    "--from-date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="Start date (YYYY-MM-DD)",
)
@click.option(
    "--to-date",
    type=click.DateTime(formats=["%Y-%m-%d"]),
    help="End date (YYYY-MM-DD)",
)
@click.option(
    "--days-back",
    type=int,
    help="Number of days to look back from today",
)
@click.option(
    "--batch-size",
    type=int,
    default=100,
    help="Batch size for database inserts",
)
@click.option(
    "--requests-per-minute",
    type=int,
    default=2,
    help="Maximum requests per minute (default 2 for free tier)",
)
@click.option(
    "--max-symbols",
    type=int,
    help="Maximum number of symbols to process (for testing)",
)
@click.option(
    "--timespan",
    type=click.Choice(["minute", "hour", "day", "week", "month", "quarter", "year"]),
    default="day",
    help="Data granularity (default: day)",
)
@click.option(
    "--multiplier",
    type=int,
    default=1,
    help="Number of timespans to aggregate (default: 1)",
)
@click.option(
    "--incremental",
    is_flag=True,
    default=True,
    help="Use incremental loading (load only new data since last successful run)",
)
@click.option(
    "--force-full",
    is_flag=True,
    default=False,
    help="Force full reload even if incremental data exists",
)
@click.option(
    "--health-check",
    is_flag=True,
    help="Run health check and exit",
)
@click.option(
    "--detect-delisted/--no-detect-delisted",
    default=True,
    help="Enable/disable automatic delisting detection (default: enabled)",
)
def main(
    symbol: Optional[str],
    all_symbols: bool,
    from_date: Optional[datetime],
    to_date: Optional[datetime],
    days_back: Optional[int],
    batch_size: int,
    requests_per_minute: int,
    max_symbols: Optional[int],
    timespan: str,
    multiplier: int,
    incremental: bool,
    force_full: bool,
    health_check: bool,
    detect_delisted: bool,
):
    """
    Load historical market data from Polygon.io

    Examples:
        # Load daily data for AAPL for the last 30 days (2 requests/min)
        python scripts/load_historical_data.py --symbol AAPL --days-back 30

        # Load hourly data for AAPL for the last 7 days
        python scripts/load_historical_data.py --symbol AAPL --days-back 7 --timespan hour

        # Load 5-minute data for AAPL for the last 2 days
        python scripts/load_historical_data.py --symbol AAPL --days-back 2 --timespan minute --multiplier 5

        # Load data for all symbols for specific date range
        python scripts/load_historical_data.py --all-symbols --from-date 2023-01-01 --to-date 2023-12-31

        # Load data for first 10 symbols for testing
        python scripts/load_historical_data.py --all-symbols --days-back 7 --max-symbols 10

        # Incremental loading (default behavior)
        python scripts/load_historical_data.py --symbol AAPL --incremental

        # Force full reload
        python scripts/load_historical_data.py --symbol AAPL --force-full --days-back 30

        # Load data with delisting detection disabled
        python scripts/load_historical_data.py --all-symbols --days-back 7 --no-detect-delisted

        # Load data with delisting detection enabled (default)
        python scripts/load_historical_data.py --all-symbols --days-back 7 --detect-delisted
    """
    # Setup logging
    setup_logging()

    # Convert datetime to date if provided
    from_date_obj = from_date.date() if from_date else None
    to_date_obj = to_date.date() if to_date else None

    async def run_loader():
        loader = HistoricalDataLoader(
            batch_size=batch_size,
            requests_per_minute=requests_per_minute,
            detect_delisted=detect_delisted,
        )

        if health_check:
            healthy = await loader.health_check()
            if healthy:
                logger.info("Health check passed")
                return 0
            else:
                logger.error("Health check failed")
                return 1

        if not symbol and not all_symbols:
            logger.error("Must specify either --symbol or --all-symbols")
            return 1

        if symbol and all_symbols:
            logger.error("Cannot specify both --symbol and --all-symbols")
            return 1

        try:
            if symbol:
                # Load single symbol
                records_count = await loader.load_symbol_data(
                    symbol=symbol,
                    from_date=from_date_obj,
                    to_date=to_date_obj,
                    days_back=days_back,
                    timespan=timespan,
                    multiplier=multiplier,
                    incremental=incremental,
                    force_full=force_full,
                )
                logger.info(f"Loaded {records_count} records for {symbol}")
                return 0

            elif all_symbols:
                # Load all symbols
                stats = await loader.load_all_symbols_data(
                    from_date=from_date_obj,
                    to_date=to_date_obj,
                    days_back=days_back,
                    max_symbols=max_symbols,
                    timespan=timespan,
                    multiplier=multiplier,
                    incremental=incremental,
                    force_full=force_full,
                )

                logger.info("Loading completed:")
                logger.info(f"  Total symbols: {stats['total_symbols']}")
                logger.info(f"  Successful: {stats['successful']}")
                logger.info(f"  Failed: {stats['failed']}")
                logger.info(f"  Total records: {stats['total_records']}")

                if "delisted_symbols" in stats and stats["delisted_symbols"]:
                    logger.info(
                        f"  Delisted symbols detected: {len(stats['delisted_symbols'])}"
                    )
                    for delisted_symbol in stats["delisted_symbols"]:
                        logger.info(f"    - {delisted_symbol}")

                if "delisting_error" in stats:
                    logger.error(
                        f"  Delisting detection error: {stats['delisting_error']}"
                    )

                if stats["errors"]:
                    logger.error("Errors encountered:")
                    for error in stats["errors"]:
                        logger.error(f"  {error}")

                return 0 if stats["failed"] == 0 else 1

        except Exception as e:
            logger.error(f"Loader failed: {e}")
            return 1

    # Run the async function
    return asyncio.run(run_loader())


if __name__ == "__main__":
    exit(main())
