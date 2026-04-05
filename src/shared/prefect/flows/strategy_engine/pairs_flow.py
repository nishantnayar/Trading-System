"""
Intraday Pairs Trading Flow

Scheduled to run hourly during market hours:
    Cron: 0 14-21 * * 1-5  (UTC = 9 AM - 5 PM ET, Mon-Fri)

Each run:
    1. Check market is open (Alpaca clock)
    2. Load active pairs from PairRegistry
    3. For each pair: run one PairsStrategy cycle
    4. Log summary

Deploy alongside existing flows in the Prefect work pool.
"""

import sys
from datetime import datetime
from pathlib import Path
from typing import Awaitable, Optional, cast

# Add project root to path when running directly
if __file__ and Path(__file__).exists():
    project_root = Path(__file__).parent.parent.parent.parent.parent.parent
    if project_root.exists() and str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from loguru import logger
from prefect import flow, task

from src.config.settings import get_settings
from src.services.alpaca.client import AlpacaClient
from src.services.notification.email_notifier import get_notifier
from src.services.strategy_engine.pairs.strategy import PairsStrategy
from src.shared.database.base import db_readonly_session, db_transaction
from src.shared.database.models.market_data import MarketData
from src.shared.database.models.strategy_models import PairRegistry, PairTrade

# ---------------------------------------------------------------------------
# Run name helper
# ---------------------------------------------------------------------------


def _flow_run_name() -> str:
    return f"Pairs Trading Cycle - {datetime.now().strftime('%Y-%m-%d %H:%M')}"


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------


@task(
    name="check-market-open",
    retries=2,
    retry_delay_seconds=15,
    log_prints=True,
)
async def check_market_open_task(alpaca: AlpacaClient) -> bool:
    """Return True if the market is currently open."""
    clock = await alpaca.get_clock()
    is_open = clock.get("is_open", False)
    next_open = clock.get("next_open", "unknown")
    if is_open:
        logger.info("Market is OPEN  -  proceeding with strategy cycle")
    else:
        logger.info(f"Market is CLOSED  -  next open: {next_open}")
    return bool(is_open)


@task(
    name="run-pairs-strategy-cycle",
    retries=1,
    retry_delay_seconds=30,
    log_prints=True,
)
async def run_pairs_strategy_task(alpaca: AlpacaClient) -> dict:
    """Run one full PairsStrategy evaluation cycle across all active pairs."""
    strategy = PairsStrategy(alpaca)
    results = await strategy.run_cycle()

    ok = [r for r in results if r.get("status") == "OK"]
    no_signal = [r for r in results if r.get("status") == "NO_SIGNAL"]
    errors = [r for r in results if r.get("status") == "ERROR"]

    summary = {
        "total_pairs": len(results),
        "with_signal": len(ok),
        "no_signal": len(no_signal),
        "errors": len(errors),
        "details": results,
    }

    logger.info(
        f"Cycle complete: {len(results)} pairs evaluated, "
        f"{len(ok)} with signal, {len(errors)} errors"
    )
    return summary


@task(
    name="refresh-pair-prices",
    retries=2,
    retry_delay_seconds=30,
    log_prints=True,
)
async def refresh_pair_prices_task() -> dict:
    """
    Load today's hourly Yahoo bars into market_data for every active pair symbol.

    Runs before the strategy cycle so _fetch_prices() always sees bars up to
    the current hour.  Uses days_back=2 to ensure the current partial trading
    day is fully covered (yfinance returns all completed 1h candles for today
    when queried intraday).
    """
    with db_readonly_session() as session:
        pairs = (
            session.query(PairRegistry).filter(PairRegistry.is_active.is_(True)).all()
        )
        symbols = sorted({sym for p in pairs for sym in (p.symbol1, p.symbol2)})
        for p in pairs:
            session.expunge(p)

    if not symbols:
        logger.info("refresh-pair-prices: no active pairs, skipping")
        return {"symbols": [], "loaded": 0}

    logger.info("Refreshing hourly bars for %d symbols: %s", len(symbols), symbols)

    from datetime import date, timedelta, timezone

    import yfinance as yf
    from sqlalchemy.dialects.postgresql import insert as pg_insert

    from_date = date.today() - timedelta(days=2)
    to_date = date.today()
    total = 0

    for symbol in symbols:
        try:
            hist = yf.Ticker(symbol).history(
                start=str(from_date),
                end=str(to_date),
                interval="1h",
                auto_adjust=True,
            )
            if hist.empty:
                logger.warning("No Yahoo bars returned for %s", symbol)
                continue

            records = []
            for ts, row in hist.iterrows():
                records.append(
                    {
                        "symbol": symbol,
                        "timestamp": ts.to_pydatetime().astimezone(timezone.utc),
                        "data_source": "yahoo_adjusted_1h",
                        "open": float(row["Open"]),
                        "high": float(row["High"]),
                        "low": float(row["Low"]),
                        "close": float(row["Close"]),
                        "volume": int(row["Volume"]),
                    }
                )

            with db_transaction() as session:
                stmt = pg_insert(MarketData).values(records)
                stmt = stmt.on_conflict_do_update(
                    index_elements=["symbol", "timestamp", "data_source"],
                    set_={
                        "open": stmt.excluded.open,
                        "high": stmt.excluded.high,
                        "low": stmt.excluded.low,
                        "close": stmt.excluded.close,
                        "volume": stmt.excluded.volume,
                    },
                )
                session.execute(stmt)

            total += len(records)
            logger.info("Refreshed %d bars for %s", len(records), symbol)
        except Exception as exc:
            logger.warning("Failed to refresh bars for %s: %s", symbol, exc)

    logger.info("refresh-pair-prices: %d total records for %s", total, symbols)
    return {"symbols": symbols, "loaded": total}


# Degradation thresholds for auto-disabling pairs
_MIN_TRADES_TO_EVALUATE = 5  # skip pairs with fewer closed trades
_EVAL_WINDOW = 10  # look at the most recent N closed trades
_FAIL_WIN_RATE = 0.35  # deactivate if win rate falls below this
# (also requires avg_pnl < 0 to avoid deactivating pairs on a cold streak)


@task(
    name="check-and-disable-failing-pairs",
    retries=1,
    retry_delay_seconds=15,
    log_prints=True,
)
async def check_and_disable_failing_pairs_task() -> dict:
    """
    Evaluate recent trade performance for every active pair.
    Deactivates pairs where the last _EVAL_WINDOW trades show:
      - win rate < _FAIL_WIN_RATE, AND
      - average P&L < 0
    Sends an email alert for each deactivated pair.
    """
    with db_readonly_session() as session:
        pairs = (
            session.query(PairRegistry).filter(PairRegistry.is_active.is_(True)).all()
        )
        for p in pairs:
            session.expunge(p)

    deactivated = []

    for pair in pairs:
        with db_readonly_session() as session:
            recent = (
                session.query(PairTrade)
                .filter(
                    PairTrade.pair_id == pair.id,
                    PairTrade.status.in_(["CLOSED", "STOPPED"]),
                )
                .order_by(PairTrade.exit_time.desc())
                .limit(_EVAL_WINDOW)
                .all()
            )
            for t in recent:
                session.expunge(t)

        if len(recent) < _MIN_TRADES_TO_EVALUATE:
            continue

        wins = sum(1 for t in recent if (t.pnl or 0) > 0)
        win_rate = wins / len(recent)
        avg_pnl = sum(t.pnl or 0 for t in recent) / len(recent)

        if win_rate < _FAIL_WIN_RATE and avg_pnl < 0:
            pair_label = f"{pair.symbol1}/{pair.symbol2}"
            reason = (
                f"Last {len(recent)} trades: "
                f"win_rate={win_rate:.1%} (threshold {_FAIL_WIN_RATE:.0%}), "
                f"avg_pnl=${avg_pnl:+.2f}"
            )
            logger.warning(f"Auto-deactivating {pair_label}: {reason}")

            with db_transaction() as session:
                db_pair = session.get(PairRegistry, pair.id)
                if db_pair:
                    db_pair.is_active = False
                    db_pair.notes = f"Auto-deactivated {datetime.now().strftime('%Y-%m-%d')}: {reason}"

            await get_notifier().send_pair_deactivated(
                pair=pair_label,
                reason=reason,
                win_rate=win_rate,
                avg_pnl=avg_pnl,
                total_trades=len(recent),
            )
            deactivated.append(pair_label)

    if deactivated:
        logger.info(
            f"Deactivated {len(deactivated)} failing pair(s): {', '.join(deactivated)}"
        )
    else:
        logger.info("Performance check: no failing pairs detected")

    return {"deactivated": deactivated, "count": len(deactivated)}


# ---------------------------------------------------------------------------
# Flow
# ---------------------------------------------------------------------------


@flow(
    name="intraday-pairs-trading",
    flow_run_name=_flow_run_name,
    log_prints=True,
    retries=1,
    retry_delay_seconds=60,
    timeout_seconds=600,
)
async def intraday_pairs_flow(skip_market_check: bool = False) -> dict:
    """
    Intraday pairs trading strategy flow.

    Args:
        skip_market_check: Set True to run even when market is closed
                           (useful for testing / manual runs).

    Returns:
        Summary dict with results from all pair cycles.
    """
    logger.info("Starting intraday pairs trading flow")

    settings = get_settings()
    alpaca = AlpacaClient(
        api_key=settings.alpaca_api_key,
        secret_key=settings.alpaca_secret_key,
        is_paper=True,
    )

    if not skip_market_check:
        is_open = await check_market_open_task(alpaca)
        if not is_open:
            return {"status": "MARKET_CLOSED", "pairs_evaluated": 0}

    try:
        await refresh_pair_prices_task()
        summary = await run_pairs_strategy_task(alpaca)
        deactivation = await check_and_disable_failing_pairs_task()
        summary["deactivated_pairs"] = deactivation["deactivated"]
    except Exception as exc:
        err_msg = str(exc)
        logger.error(f"Unhandled flow error: {err_msg}")
        await get_notifier().send_flow_error(error=err_msg)
        raise

    logger.info(
        f"Flow complete: {summary['total_pairs']} pairs, "
        f"{summary['with_signal']} signals, {summary['errors']} errors, "
        f"{len(summary.get('deactivated_pairs', []))} deactivated"
    )
    return {"status": "OK", **summary}


# ---------------------------------------------------------------------------
# Deployment helper (run from CLI)
# ---------------------------------------------------------------------------


async def deploy_pairs_flow() -> None:
    """Register the intraday pairs trading flow as a Prefect deployment."""
    project_root = Path(__file__).parent.parent.parent.parent.parent.parent
    source_path = str(project_root)
    flow_file = "src/shared/prefect/flows/strategy_engine/pairs_flow.py"

    from src.shared.prefect.config import PrefectConfig

    deployment = await cast(
        Awaitable,
        intraday_pairs_flow.from_source(
            source=source_path,
            entrypoint=f"{flow_file}:intraday_pairs_flow",
        ),
    )
    await deployment.deploy(
        name="Intraday Pairs Trading",
        work_pool_name=PrefectConfig.get_work_pool_name(),
        cron="0 14-21 * * 1-5",  # hourly 9 AM-5 PM ET (14-21 UTC), Mon-Fri
        parameters={"skip_market_check": False},
        tags=["strategy-engine", "pairs-trading", "scheduled"],
        description="Hourly intraday pairs trading strategy  -  evaluates z-scores and places paper orders via Alpaca",
        ignore_warnings=True,
    )
    logger.info("Pairs trading flow deployed successfully!")


if __name__ == "__main__":
    """
    Modes:
        Dry-run (one cycle now, market check skipped):
            python src/shared/prefect/flows/strategy_engine/pairs_flow.py

        Register deployment in Prefect (creates scheduled job visible in UI):
            python src/shared/prefect/flows/strategy_engine/pairs_flow.py --deploy
    """
    import asyncio
    import sys as _sys

    if "--deploy" in _sys.argv:
        asyncio.run(deploy_pairs_flow())
    else:
        # Default: run one cycle immediately (skip market check for manual testing)
        asyncio.run(intraday_pairs_flow(skip_market_check=True))
