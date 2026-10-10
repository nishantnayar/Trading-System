"""
Pair Discovery Script

Finds statistically validated pairs for intraday pairs trading from actual DB data.
Runs Engle-Granger cointegration tests on 252 days of hourly close prices,
computes OLS hedge ratios and mean-reversion half-lives, and outputs a ranked
table of the best candidates.

Usage:
    python scripts/discover_pairs.py
    python scripts/discover_pairs.py --min-correlation 0.75 --max-pvalue 0.05
    python scripts/discover_pairs.py --sector Technology
    python scripts/discover_pairs.py --top 10
"""

import asyncio
import sys
from pathlib import Path
from typing import Optional

import click
from loguru import logger

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.services.strategy_engine.discovery.pairs import run_discovery  # noqa: E402


@click.command()
@click.option(
    "--min-correlation",
    default=0.70,
    type=float,
    show_default=True,
    help="Minimum Pearson correlation on log returns",
)
@click.option(
    "--max-pvalue",
    default=0.05,
    type=float,
    show_default=True,
    help="Maximum Engle-Granger cointegration p-value",
)
@click.option(
    "--min-half-life",
    default=5.0,
    type=float,
    show_default=True,
    help="Minimum mean-reversion half-life in hours",
)
@click.option(
    "--max-half-life",
    default=72.0,
    type=float,
    show_default=True,
    help="Maximum mean-reversion half-life in hours",
)
@click.option(
    "--sector",
    default=None,
    type=str,
    help="Filter to a specific sector (e.g. Technology)",
)
@click.option(
    "--top",
    "top_n",
    default=5,
    type=int,
    show_default=True,
    help="Number of top pairs to display",
)
@click.option(
    "--days-back",
    default=252,
    type=int,
    show_default=True,
    help="Days of hourly history to pull (default: 252 = 1 trading year)",
)
@click.option(
    "--data-source",
    default="yahoo_adjusted",
    show_default=True,
    help="Data source in market_data table",
)
def main(
    min_correlation: float,
    max_pvalue: float,
    min_half_life: float,
    max_half_life: float,
    sector: Optional[str],
    top_n: int,
    days_back: int,
    data_source: str,
) -> None:
    """
    Discover statistically validated pairs for intraday pairs trading.

    Pulls hourly close prices from the DB, filters by correlation and
    Engle-Granger cointegration, computes OLS hedge ratios and mean-reversion
    half-lives, and prints a ranked table of the best candidates.

    After reviewing the results, update config/pairs.yaml with the pair(s) you
    want to trade.

    Examples:

        # Run with defaults (top 5 pairs, 252 days)
        python scripts/discover_pairs.py

        # Technology sector only, stricter correlation
        python scripts/discover_pairs.py --sector Technology --min-correlation 0.80

        # Show top 10 pairs
        python scripts/discover_pairs.py --top 10
    """
    # Configure logging
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO",
    )

    asyncio.run(
        run_discovery(
            min_correlation=min_correlation,
            max_pvalue=max_pvalue,
            min_half_life=min_half_life,
            max_half_life=max_half_life,
            sector_filter=sector,
            top_n=top_n,
            days_back=days_back,
            data_source=data_source,
        )
    )


if __name__ == "__main__":
    main()
