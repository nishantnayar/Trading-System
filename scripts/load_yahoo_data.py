#!/usr/bin/env python3
"""
Yahoo Finance Data Loader Script

Load market data from Yahoo Finance into the database.

Usage:
    python scripts/load_yahoo_data.py --symbol AAPL --days 365
    python scripts/load_yahoo_data.py --all-symbols --days 30
    python scripts/load_yahoo_data.py --symbol AAPL --from-date 2023-01-01 --to-date 2024-12-31
"""

import asyncio
import os
import sys
from datetime import date, datetime, timedelta
from typing import Optional

import click

# Add project root to path
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from loguru import logger

from src.services.yahoo.loader import YahooDataLoader
from src.shared.logging import setup_logging


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
    "--days",
    type=int,
    help="Number of days to look back from today",
)
@click.option(
    "--interval",
    type=click.Choice(["1m", "5m", "15m", "30m", "1h", "1d", "1wk", "1mo"]),
    default="1h",
    help="Data interval (default: 1h for hourly)",
)
@click.option(
    "--batch-size",
    type=int,
    default=100,
    help="Batch size for database inserts (default: 100)",
)
@click.option(
    "--delay",
    type=float,
    default=0.5,
    help="Delay between requests in seconds (default: 0.5)",
)
@click.option(
    "--max-symbols",
    type=int,
    help="Maximum number of symbols to process (for testing)",
)
@click.option(
    "--company-info",
    is_flag=True,
    help="Load company info (fundamentals)",
)
@click.option(
    "--fundamentals",
    is_flag=True,
    help="Load company fundamentals (company info)",
)
@click.option(
    "--key-statistics",
    is_flag=True,
    help="Load key financial statistics (P/E, ROE, margins, etc.)",
)
@click.option(
    "--company-info-only",
    is_flag=True,
    help="Load only company info (no market data)",
)
@click.option(
    "--key-statistics-only",
    is_flag=True,
    help="Load only key statistics (no market data)",
)
@click.option(
    "--institutional-holders",
    is_flag=True,
    help="Load institutional holders data",
)
@click.option(
    "--institutional-holders-only",
    is_flag=True,
    help="Load only institutional holders (no market data)",
)
@click.option(
    "--financial-statements",
    is_flag=True,
    help="Load financial statements (income, balance sheet, cash flow)",
)
@click.option(
    "--financial-statements-only",
    is_flag=True,
    help="Load only financial statements (no market data)",
)
@click.option(
    "--company-officers",
    is_flag=True,
    help="Load company officers and executives",
)
@click.option(
    "--company-officers-only",
    is_flag=True,
    help="Load only company officers (no market data)",
)
@click.option(
    "--dividends",
    is_flag=True,
    help="Load dividend history (not yet implemented)",
)
@click.option(
    "--splits",
    is_flag=True,
    help="Load stock split history (not yet implemented)",
)
@click.option(
    "--health-check",
    is_flag=True,
    help="Run health check and exit",
)
def main(
    symbol: Optional[str],
    all_symbols: bool,
    from_date: Optional[datetime],
    to_date: Optional[datetime],
    days: Optional[int],
    interval: str,
    batch_size: int,
    delay: float,
    max_symbols: Optional[int],
    company_info: bool,
    fundamentals: bool,
    key_statistics: bool,
    company_info_only: bool,
    key_statistics_only: bool,
    institutional_holders: bool,
    institutional_holders_only: bool,
    financial_statements: bool,
    financial_statements_only: bool,
    company_officers: bool,
    company_officers_only: bool,
    dividends: bool,
    splits: bool,
    health_check: bool,
) -> int:
    """
    Load market data from Yahoo Finance

    Examples:
        # Load daily data for AAPL for the last 30 days
        python scripts/load_yahoo_data.py --symbol AAPL --days 30

        # Load hourly data for AAPL for the last 7 days
        python scripts/load_yahoo_data.py --symbol AAPL --days 7 --interval 1h

        # Load key statistics for AAPL
        python scripts/load_yahoo_data.py --symbol AAPL --key-statistics-only

        # Load institutional holders for AAPL
        python scripts/load_yahoo_data.py --symbol AAPL --institutional-holders-only

        # Load key statistics for all symbols
        python scripts/load_yahoo_data.py --all-symbols --key-statistics-only --max-symbols 10

        # Load market data + company info + key statistics + institutional holders
        python scripts/load_yahoo_data.py --symbol AAPL --days 30 --company-info --key-statistics --institutional-holders

        # Load data for all symbols for specific date range
        python scripts/load_yahoo_data.py --all-symbols --from-date 2023-01-01 --to-date 2023-12-31

        # Load company info only (no market data)
        python scripts/load_yahoo_data.py --symbol AAPL --company-info-only
        python scripts/load_yahoo_data.py --all-symbols --company-info-only

        # Load market data + company info
        python scripts/load_yahoo_data.py --symbol AAPL --days 30 --company-info

        # Health check
        python scripts/load_yahoo_data.py --health-check
    """
    # Setup logging
    setup_logging()

    async def run_loader() -> int:
        loader = YahooDataLoader(
            batch_size=batch_size,
            delay_between_requests=delay,
        )

        if health_check:
            healthy = await loader.health_check()
            if healthy:
                logger.info("✅ Health check passed - Yahoo Finance is accessible")
                return 0
            else:
                logger.error("❌ Health check failed - Yahoo Finance not accessible")
                return 1

        if not symbol and not all_symbols:
            logger.error("Must specify either --symbol or --all-symbols")
            return 1

        if symbol and all_symbols:
            logger.error("Cannot specify both --symbol and --all-symbols")
            return 1

        # Convert datetime to date if provided
        from_date_obj = from_date.date() if from_date else None
        to_date_obj = to_date.date() if to_date else None

        # Calculate date range
        if days:
            to_date_obj = to_date_obj or date.today()
            from_date_obj = from_date_obj or (to_date_obj - timedelta(days=days))
        elif not from_date_obj:
            # Default to 30 days if no date range specified
            to_date_obj = to_date_obj or date.today()
            from_date_obj = to_date_obj - timedelta(days=30)

        logger.info(f"Date range: {from_date_obj} to {to_date_obj}")
        logger.info(f"Interval: {interval}")

        try:
            if symbol:
                # Load single symbol
                if company_info_only:
                    # Load only company info
                    success = await loader.load_company_info(symbol)
                    if success:
                        logger.info(f"✅ Successfully loaded company info for {symbol}")
                    else:
                        logger.error(f"❌ Failed to load company info for {symbol}")
                        return 1
                elif key_statistics_only:
                    # Load only key statistics
                    success = await loader.load_key_statistics(symbol)
                    if success:
                        logger.info(
                            f"✅ Successfully loaded key statistics for {symbol}"
                        )
                    else:
                        logger.error(f"❌ Failed to load key statistics for {symbol}")
                        return 1
                elif institutional_holders_only:
                    # Load only institutional holders
                    count = await loader.load_institutional_holders(symbol)
                    if count > 0:
                        logger.info(
                            f"✅ Successfully loaded {count} institutional holders for {symbol}"
                        )
                    else:
                        logger.warning(f"⚠ No institutional holders found for {symbol}")
                        return 1
                elif financial_statements_only:
                    # Load only financial statements
                    statements = await loader.load_financial_statements(symbol)
                    if statements:
                        logger.info(
                            f"✅ Successfully loaded {len(statements)} financial statements for {symbol}"
                        )
                    else:
                        logger.warning(f"⚠ No financial statements found for {symbol}")
                        return 1
                elif company_officers_only:
                    # Load only company officers
                    officers = await loader.load_company_officers(symbol)
                    if officers:
                        logger.info(
                            f"✅ Successfully loaded {len(officers)} company officers for {symbol}"
                        )
                    else:
                        logger.warning(f"⚠ No company officers found for {symbol}")
                        return 1
                elif (
                    company_info
                    or fundamentals
                    or key_statistics
                    or institutional_holders
                    or financial_statements
                    or dividends
                    or splits
                ):
                    # Use load_all_data for comprehensive loading
                    results = await loader.load_all_data(
                        symbol=symbol,
                        start_date=from_date_obj,
                        end_date=to_date_obj,
                        include_fundamentals=company_info or fundamentals,
                        include_key_statistics=key_statistics,
                        include_institutional_holders=institutional_holders,
                        include_financial_statements=financial_statements,
                        include_dividends=dividends,
                        include_splits=splits,
                    )
                    logger.info(f"Loaded data for {symbol}: {results}")
                else:
                    # Load market data only
                    records_count = await loader.load_market_data(
                        symbol=symbol,
                        start_date=from_date_obj,
                        end_date=to_date_obj,
                        interval=interval,
                    )
                    logger.info(f"Loaded {records_count} records for {symbol}")

                return 0

            elif all_symbols:
                if company_info_only:
                    # Load company info for all symbols
                    symbols_list = await loader._get_active_symbols()
                    if max_symbols:
                        symbols_list = symbols_list[:max_symbols]

                    logger.info(f"Loading company info for {len(symbols_list)} symbols")
                    successful = 0
                    failed = 0

                    for i, sym in enumerate(symbols_list, 1):
                        logger.info(f"Processing {i}/{len(symbols_list)}: {sym}")
                        success = await loader.load_company_info(sym)
                        if success:
                            successful += 1
                        else:
                            failed += 1

                        if i < len(symbols_list):
                            await asyncio.sleep(loader.delay_between_requests)

                    logger.info(f"Company info loading completed:")
                    logger.info(f"  Total symbols: {len(symbols_list)}")
                    logger.info(f"  Successful: {successful}")
                    logger.info(f"  Failed: {failed}")

                    return 0 if failed == 0 else 1
                elif key_statistics_only:
                    # Load key statistics for all symbols
                    symbols_list = await loader._get_active_symbols()
                    if max_symbols:
                        symbols_list = symbols_list[:max_symbols]

                    logger.info(
                        f"Loading key statistics for {len(symbols_list)} symbols"
                    )
                    successful = 0
                    failed = 0

                    for i, sym in enumerate(symbols_list, 1):
                        logger.info(f"Processing {i}/{len(symbols_list)}: {sym}")
                        success = await loader.load_key_statistics(sym)
                        if success:
                            successful += 1
                        else:
                            failed += 1

                        if i < len(symbols_list):
                            await asyncio.sleep(loader.delay_between_requests)

                    logger.info(f"Key statistics loading completed:")
                    logger.info(f"  Total symbols: {len(symbols_list)}")
                    logger.info(f"  Successful: {successful}")
                    logger.info(f"  Failed: {failed}")

                    return 0 if failed == 0 else 1
                elif institutional_holders_only:
                    # Load institutional holders for all symbols
                    symbols_list = await loader._get_active_symbols()
                    if max_symbols:
                        symbols_list = symbols_list[:max_symbols]

                    logger.info(
                        f"Loading institutional holders for {len(symbols_list)} symbols"
                    )
                    successful = 0
                    failed = 0
                    total_holders = 0

                    for i, sym in enumerate(symbols_list, 1):
                        logger.info(f"Processing {i}/{len(symbols_list)}: {sym}")
                        count = await loader.load_institutional_holders(sym)
                        if count > 0:
                            successful += 1
                            total_holders += count
                        else:
                            failed += 1

                        if i < len(symbols_list):
                            await asyncio.sleep(loader.delay_between_requests)

                    logger.info(f"Institutional holders loading completed:")
                    logger.info(f"  Total symbols: {len(symbols_list)}")
                    logger.info(f"  Successful: {successful}")
                    logger.info(f"  Failed: {failed}")
                    logger.info(f"  Total holders: {total_holders}")

                    return 0 if failed == 0 else 1
                elif financial_statements_only:
                    # Load financial statements for all symbols
                    symbols_list = await loader._get_active_symbols()
                    if max_symbols:
                        symbols_list = symbols_list[:max_symbols]

                    logger.info(
                        f"Loading financial statements for {len(symbols_list)} symbols"
                    )
                    successful = 0
                    failed = 0
                    total_statements = 0

                    for i, sym in enumerate(symbols_list, 1):
                        logger.info(f"Processing {i}/{len(symbols_list)}: {sym}")
                        statements = await loader.load_financial_statements(sym)
                        if statements:
                            successful += 1
                            total_statements += len(statements)
                        else:
                            failed += 1

                        if i < len(symbols_list):
                            await asyncio.sleep(loader.delay_between_requests)

                    logger.info(f"Financial statements loading completed:")
                    logger.info(f"  Total symbols: {len(symbols_list)}")
                    logger.info(f"  Successful: {successful}")
                    logger.info(f"  Failed: {failed}")
                    logger.info(f"  Total statements: {total_statements}")

                    return 0 if failed == 0 else 1
                elif company_officers_only:
                    # Load company officers for all symbols
                    symbols_list = await loader._get_active_symbols()
                    if max_symbols:
                        symbols_list = symbols_list[:max_symbols]

                    logger.info(
                        f"Loading company officers for {len(symbols_list)} symbols"
                    )
                    successful = 0
                    failed = 0
                    total_officers = 0

                    for i, sym in enumerate(symbols_list, 1):
                        logger.info(f"Processing {i}/{len(symbols_list)}: {sym}")
                        try:
                            officers = await loader.load_company_officers(sym)
                            if officers:
                                successful += 1
                                total_officers += len(officers)
                            else:
                                failed += 1
                        except Exception as e:
                            logger.error(f"Failed to load officers for {sym}: {e}")
                            failed += 1

                        if i < len(symbols_list):
                            await asyncio.sleep(loader.delay_between_requests)

                    logger.info(f"Company officers loading completed:")
                    logger.info(f"  Total symbols: {len(symbols_list)}")
                    logger.info(f"  Successful: {successful}")
                    logger.info(f"  Failed: {failed}")
                    logger.info(f"  Total officers: {total_officers}")

                    return 0 if failed == 0 else 1
                else:
                    # Load all symbols
                    stats = await loader.load_all_symbols_data(
                        start_date=from_date_obj,
                        end_date=to_date_obj,
                        interval=interval,
                        max_symbols=max_symbols,
                        include_fundamentals=company_info or fundamentals,
                        include_key_statistics=key_statistics,
                        include_institutional_holders=institutional_holders,
                        include_financial_statements=financial_statements,
                        include_company_officers=company_officers,
                    )

                logger.info("Loading completed:")
                logger.info(f"  Total symbols: {stats['total_symbols']}")
                logger.info(f"  Successful: {stats['successful']}")
                logger.info(f"  Failed: {stats['failed']}")
                logger.info(f"  Total records: {stats['total_records']}")

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
