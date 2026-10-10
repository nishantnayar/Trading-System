"""
Basket Discovery Script

Finds statistically validated N-stock baskets for intraday pairs trading
using Johansen cointegration (multi-asset generalization of Engle-Granger).

The Johansen test finds a cointegrating vector [w1, w2, ..., wN] such that
    spread = w1*log(P1) + w2*log(P2) + ... + wN*log(PN)
is stationary and mean-reverting.  The eigenvector with the smallest eigenvalue
gives the fastest mean reversion - directly minimizing half-life.

Usage:
    python scripts/discover_baskets.py --sector "Regional Banks"
    python scripts/discover_baskets.py --sector Technology --min-basket-size 3 --top 5
    python scripts/discover_baskets.py --sector "Regional Banks" --max-pvalue 0.05
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

from src.services.strategy_engine.discovery.baskets import run_discovery  # noqa: E402


@click.command()
@click.option(
    "--sector",
    default=None,
    type=str,
    help="Filter to a specific sector (e.g. 'Regional Banks')",
)
@click.option(
    "--min-basket-size",
    default=3,
    type=int,
    show_default=True,
    help="Minimum number of stocks in basket",
)
@click.option(
    "--max-basket-size",
    default=3,
    type=int,
    show_default=True,
    help="Maximum number of stocks in basket",
)
@click.option(
    "--max-symbols",
    default=25,
    type=int,
    show_default=True,
    help="Max symbols to test after correlation pre-filter (keeps most correlated)",
)
@click.option(
    "--min-corr-prefilter",
    default=0.3,
    type=float,
    show_default=True,
    help="Min average absolute pairwise correlation to survive pre-filter",
)
@click.option(
    "--max-pvalue",
    default=0.05,
    type=float,
    show_default=True,
    help="Maximum Johansen trace statistic p-value",
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
    "--top",
    "top_n",
    default=3,
    type=int,
    show_default=True,
    help="Number of top baskets to display and save",
)
@click.option(
    "--days-back",
    default=252,
    type=int,
    show_default=True,
    help="Days of hourly history to pull",
)
@click.option(
    "--data-source",
    default="yahoo_adjusted",
    show_default=True,
    help="Data source in market_data table",
)
def main(
    sector: Optional[str],
    min_basket_size: int,
    max_basket_size: int,
    max_pvalue: float,
    min_half_life: float,
    max_half_life: float,
    top_n: int,
    days_back: int,
    data_source: str,
    max_symbols: int,
    min_corr_prefilter: float,
) -> None:
    """
    Discover statistically validated N-stock baskets via Johansen cointegration.

    The Johansen test extends Engle-Granger to N assets and directly finds the
    cointegrating vector with the fastest mean reversion (shortest half-life).

    Examples:

        # Regional Banks sector, default settings (top 3 baskets)
        python scripts/discover_baskets.py --sector "Regional Banks"

        # Technology sector, 3-4 stock baskets only
        python scripts/discover_baskets.py --sector Technology --max-basket-size 4

        # Relaxed p-value filter
        python scripts/discover_baskets.py --sector "Regional Banks" --max-pvalue 0.10
    """
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>",
        level="INFO",
    )

    asyncio.run(
        run_discovery(
            sector_filter=sector,
            min_basket_size=min_basket_size,
            max_basket_size=max_basket_size,
            max_pvalue=max_pvalue,
            min_half_life=min_half_life,
            max_half_life=max_half_life,
            top_n=top_n,
            days_back=days_back,
            data_source=data_source,
            max_symbols=max_symbols,
            min_corr_prefilter=min_corr_prefilter,
        )
    )


if __name__ == "__main__":
    main()
