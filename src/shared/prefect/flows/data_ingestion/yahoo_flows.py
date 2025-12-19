"""
Yahoo Finance Data Ingestion Flows

Prefect flows for loading data from Yahoo Finance.
"""

import asyncio
import inspect
import sys
from collections.abc import Coroutine
from datetime import date, timedelta
from pathlib import Path
from typing import Any, List, Optional

# Add project root to path when running directly
# Check if running as script (not imported)
if __file__ and Path(__file__).exists():
    # Go up 6 levels: yahoo_flows.py -> data_ingestion -> flows -> prefect -> shared -> src -> project_root
    project_root = Path(__file__).parent.parent.parent.parent.parent.parent
    if project_root.exists() and str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from pathlib import Path

from loguru import logger
from prefect import flow

from src.services.data_ingestion.symbols import SymbolService
from src.shared.prefect.config import PrefectConfig
from src.shared.prefect.tasks.data_ingestion_tasks import (
    load_yahoo_company_info_task,
    load_yahoo_key_statistics_task,
    load_yahoo_market_data_task,
)


@flow(
    name="Daily Market Data Update",
    flow_run_name=_market_data_run_name,
    log_prints=True,
    retries=1,
    retry_delay_seconds=300,
    timeout_seconds=3600,
)
async def yahoo_market_data_flow(
    days_back: Optional[int] = None,
    symbols: Optional[List[str]] = None,
    interval: str = "1h",
    max_symbols: Optional[int] = None,
) -> dict:
    """
    Daily end-of-day (hourly interval) market data ingestion from Yahoo Finance

    This flow:
    1. Gets active symbols
    2. Loads market data for each symbol
    3. Returns summary statistics

    Args:
        days_back: Number of days to look back (default: 7 for hourly, ensures weekdays included)
        symbols: Optional list of specific symbols (None = all active)
        interval: Data interval (1h, 1d, etc.)
        max_symbols: Maximum number of symbols to process (for testing)

    Returns:
        Dictionary with summary of loaded data
    """
    # Default days_back based on interval to ensure we get trading days
    if days_back is None:
        if interval in ["1h", "30m", "15m", "5m", "1m"]:
            days_back = 7  # For intraday data, look back 7 days to ensure weekdays
        else:
            days_back = 30  # For daily/weekly data, default to 30 days like the script
    
    logger.info(
        f"Starting Yahoo Market Data Flow for {len(symbols) if symbols else 'all active'} symbols (days_back={days_back}, interval={interval})"
    )

    symbol_service = SymbolService()
    symbols_list = symbols or await symbol_service.get_active_symbol_strings()

    if max_symbols:
        symbols_list = symbols_list[:max_symbols]

    successful = []
    failed = []
    no_data = []
    total_records = 0

    for symbol in symbols_list:
        try:
            logger.info(f"Processing {symbol}...")
            result = await load_yahoo_market_data_task(
                symbol=symbol, days_back=days_back, interval=interval
            )
            if result["status"] == "success":
                successful.append(symbol)
                total_records += result["records_count"]
            elif result["status"] == "no_data":
                # No data available (symbol might be delisted, etc.) - not a failure
                no_data.append(symbol)
                logger.info(f"  No data available for {symbol} (likely delisted or no trading data)")
            else:
                failed.append({"symbol": symbol, "error": result.get("error", "Unknown error")})
        except Exception as e:
            logger.error(f"Failed to process {symbol}: {e}")
            failed.append({"symbol": symbol, "error": str(e)})

    # Summary
    result = {
        "total_symbols": len(symbols_list),
        "successful": len(successful),
        "failed": len(failed),
        "no_data": len(no_data),
        "total_records": total_records,
        "successful_symbols": successful,
        "failed_symbols": failed,
        "no_data_symbols": no_data,
    }

    logger.info("=" * 60)
    logger.info("Yahoo Market Data Flow Completed")
    logger.info(f"Successful: {result['successful']}/{result['total_symbols']}")
    logger.info(f"No data: {result['no_data']} (delisted or no trading data)")
    logger.info(f"Failed: {result['failed']}")
    logger.info(f"Total records loaded: {result['total_records']}")
    logger.info("=" * 60)

    return result


@flow(
    name="Weekly Company Information Update",
    flow_run_name=_company_info_run_name,
    log_prints=True,
    retries=1,
    retry_delay_seconds=300,
    timeout_seconds=3600,
)
async def yahoo_company_info_flow(
    symbols: Optional[List[str]] = None, max_symbols: Optional[int] = None
) -> dict:
    """
    Weekly company information update flow from Yahoo Finance

    Args:
        symbols: Optional list of specific symbols (None = all active)
        max_symbols: Maximum number of symbols to process (for testing)

    Returns:
        Dictionary with summary of loaded data
    """
    logger.info(
        f"Starting Yahoo Company Info Flow for {len(symbols) if symbols else 'all active'} symbols"
    )

    symbol_service = SymbolService()
    symbols_list = symbols or await symbol_service.get_active_symbol_strings()

    if max_symbols:
        symbols_list = symbols_list[:max_symbols]

    successful = []
    failed = []
    no_data = []

    for symbol in symbols_list:
        try:
            logger.info(f"Processing {symbol}...")
            result = await load_yahoo_company_info_task(symbol=symbol)
            if result["status"] == "success":
                successful.append(symbol)
            else:
                no_data.append(symbol)
        except Exception as e:
            logger.error(f"Failed to process {symbol}: {e}")
            failed.append({"symbol": symbol, "error": str(e)})

    # Summary
    result = {
        "total_symbols": len(symbols_list),
        "successful": len(successful),
        "failed": len(failed),
        "no_data": len(no_data),
        "successful_symbols": successful,
        "failed_symbols": failed,
        "no_data_symbols": no_data,
    }

    logger.info("=" * 60)
    logger.info("Yahoo Company Info Update Completed")
    logger.info(f"Successful: {result['successful']}/{result['total_symbols']}")
    logger.info(f"Failed: {result['failed']}")
    logger.info(f"No data: {result['no_data']}")
    logger.info("=" * 60)

    return result


@flow(
    name="Weekly Key Statistics Update",
    log_prints=True,
    retries=1,
    retry_delay_seconds=300,
    timeout_seconds=3600,
)
async def yahoo_key_statistics_flow(
    symbols: Optional[List[str]] = None, max_symbols: Optional[int] = None
) -> dict:
    """
    Weekly key statistics update flow from Yahoo Finance

    Args:
        symbols: Optional list of specific symbols (None = all active)
        max_symbols: Maximum number of symbols to process (for testing)

    Returns:
        Dictionary with summary of loaded data
    """
    logger.info(
        f"Starting Yahoo Key Statistics Flow for {len(symbols) if symbols else 'all active'} symbols"
    )

    symbol_service = SymbolService()
    symbols_list = symbols or await symbol_service.get_active_symbol_strings()

    if max_symbols:
        symbols_list = symbols_list[:max_symbols]

    successful = []
    failed = []
    no_data = []

    for symbol in symbols_list:
        try:
            logger.info(f"Processing {symbol}...")

            result = await load_yahoo_key_statistics_task(symbol=symbol)

            if result["status"] == "success":
                successful.append(symbol)
            else:
                no_data.append(symbol)

        except Exception as e:
            logger.error(f"Failed to process {symbol}: {e}")
            failed.append({"symbol": symbol, "error": str(e)})

    # Summary
    result = {
        "total_symbols": len(symbols_list),
        "successful": len(successful),
        "failed": len(failed),
        "no_data": len(no_data),
        "successful_symbols": successful,
        "failed_symbols": failed,
        "no_data_symbols": no_data,
    }

    logger.info("=" * 60)
    logger.info("Yahoo Key Statistics Update Completed")
    logger.info(f"Successful: {result['successful']}/{result['total_symbols']}")
    logger.info(f"Failed: {result['failed']}")
    logger.info(f"No data: {result['no_data']}")
    logger.info("=" * 60)

    return result


@flow(
    name="Weekly Company Data Update",
    flow_run_name=_combined_run_name,
    log_prints=True,
    retries=1,
    retry_delay_seconds=300,
    timeout_seconds=7200,
)
async def yahoo_company_info_then_key_statistics_flow(
    symbols: Optional[List[str]] = None, max_symbols: Optional[int] = None
) -> dict:
    """
    Weekly orchestration flow that runs company info first, then key statistics.

    Args:
        symbols: Optional list of specific symbols (None = all active)
        max_symbols: Maximum number of symbols to process (for testing)

    Returns:
        Dictionary with combined summaries
    """
    logger.info("Starting combined Yahoo Company Info -> Key Statistics flow")

    company_info_result = await yahoo_company_info_flow(
        symbols=symbols, max_symbols=max_symbols
    )
    logger.info(
        f"Company info finished: "
        f"{company_info_result['successful']}/{company_info_result['total_symbols']} successful"
    )

    key_stats_result = await yahoo_key_statistics_flow(
        symbols=symbols, max_symbols=max_symbols
    )
    logger.info(
        f"Key statistics finished: "
        f"{key_stats_result['successful']}/{key_stats_result['total_symbols']} successful"
    )

    combined = {
        "company_info": company_info_result,
        "key_statistics": key_stats_result,
    }

    logger.info("Combined flow completed")
    return combined


async def _resolve_deployment(
    deployment: Any,
) -> Any:
    """
    Resolve a deployment that may be a coroutine.
    
    Args:
        deployment: Either a deployment object or a coroutine that returns one
        
    Returns:
        The resolved deployment object
    """
    if inspect.iscoroutine(deployment):
        return await deployment
    return deployment


def _market_data_run_name() -> str:
    """Generate business-friendly run name for market data flow."""
    from datetime import datetime
    run_date = datetime.now().strftime("%Y-%m-%d")
    return f"Market Data Update - {run_date}"


def _company_info_run_name() -> str:
    """Generate business-friendly run name for company info flow."""
    from datetime import datetime
    run_date = datetime.now().strftime("%Y-%m-%d")
    return f"Company Information Update - {run_date}"


def _key_statistics_run_name() -> str:
    """Generate business-friendly run name for key statistics flow."""
    from datetime import datetime
    run_date = datetime.now().strftime("%Y-%m-%d")
    return f"Key Statistics Update - {run_date}"


def _combined_run_name() -> str:
    """Generate business-friendly run name for combined flow."""
    from datetime import datetime
    run_date = datetime.now().strftime("%Y-%m-%d")
    return f"Company Data Update - {run_date}"


# Deployment configuration using .deploy() API (Prefect 3.x)
async def deploy_all_flows() -> None:
    """Deploy all Yahoo Finance flows."""
    # Get project root for source path
    project_root = Path(__file__).parent.parent.parent.parent.parent.parent
    source_path = str(project_root)
    flow_file = "src/shared/prefect/flows/data_ingestion/yahoo_flows.py"

    # Deploy market data flow (daily end-of-day, still fetching hourly bars)
    # Using from_source with local path for Prefect 3.4
    market_data_deployment = await _resolve_deployment(
        yahoo_market_data_flow.from_source(
            source=source_path,
            entrypoint=f"{flow_file}:yahoo_market_data_flow",
        )
    )
    market_data_deployment.deploy(
        name="Daily Market Data Update",
        work_pool_name=PrefectConfig.get_work_pool_name(),
        cron="15 22 * * 1-5",  # 22:15 UTC Mon–Fri (~after US market close; adjust in UI)
        parameters={
            "days_back": 7,  # Look back 7 days to ensure we get weekday data
            "interval": "1h",
        },
        tags=["data-ingestion", "yahoo", "market-data", "scheduled"],
        description="Daily end-of-day market data ingestion from Yahoo Finance (hourly bars)",
    )

    # Deploy company info flow (weekly)
    company_info_deployment = await _resolve_deployment(
        yahoo_company_info_flow.from_source(
            source=source_path,
            entrypoint=f"{flow_file}:yahoo_company_info_flow",
        )
    )
    company_info_deployment.deploy(
        name="Weekly Company Information Update",
        work_pool_name=PrefectConfig.get_work_pool_name(),
        cron="0 2 * * 0",  # 2 AM Sunday (weekly) - UTC
        tags=["data-ingestion", "yahoo", "company-info", "scheduled"],
        description="Weekly company information update from Yahoo Finance",
    )

    # Deploy key statistics flow (weekly)
    key_stats_deployment = await _resolve_deployment(
        yahoo_key_statistics_flow.from_source(
            source=source_path,
            entrypoint=f"{flow_file}:yahoo_key_statistics_flow",
        )
    )
    key_stats_deployment.deploy(
        name="Weekly Key Statistics Update",
        work_pool_name=PrefectConfig.get_work_pool_name(),
        cron="0 3 * * 0",  # 3 AM Sunday (weekly) - UTC
        tags=["data-ingestion", "yahoo", "key-statistics", "scheduled"],
        description="Weekly key statistics update from Yahoo Finance",
    )

    # Deploy combined company info -> key statistics flow (weekly)
    combined_deployment = await _resolve_deployment(
        yahoo_company_info_then_key_statistics_flow.from_source(
            source=source_path,
            entrypoint=f"{flow_file}:yahoo_company_info_then_key_statistics_flow",
        )
    )
    combined_deployment.deploy(
        name="Weekly Company Data Update",
        work_pool_name=PrefectConfig.get_work_pool_name(),
        cron="0 2 * * 0",  # 2 AM Sunday (weekly) - UTC
        tags=[
            "data-ingestion",
            "yahoo",
            "company-info",
            "key-statistics",
            "scheduled",
        ],
        description="Weekly company information and key statistics update from Yahoo Finance",
    )

    logger.info("All Yahoo Finance flows deployed successfully!")


if __name__ == "__main__":
    asyncio.run(deploy_all_flows())
