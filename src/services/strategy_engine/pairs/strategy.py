"""
Pairs Strategy Orchestrator

Main entry point called by the Prefect intraday flow.

Each call to PairsStrategy.run_cycle() performs one full evaluation loop:
    1. Load active pairs from PairRegistry
    2. For each pair:
        a. Fetch latest N hourly bars from data_ingestion.market_data
        b. SpreadCalculator.calculate() → spread, z_score
        c. Store spread/z-score to PairSpread table
        d. SignalGenerator.generate() → signal or None
        e. If entry signal: KellySizer.calculate_size() → qty1, qty2
        f. PairExecutor.open_pair_trade() or close_pair_trade() / emergency_stop()
    3. Update PairPerformance table

The strategy reads prices from the DB (not Yahoo API) for low latency.
"""

import asyncio
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import pandas as pd
from loguru import logger

from src.services.alpaca.client import AlpacaClient
from src.services.strategy_engine.pairs.pair_executor import PairExecutor
from src.services.strategy_engine.pairs.position_sizer import KellySizer
from src.services.strategy_engine.pairs.signal_generator import SignalGenerator
from src.services.strategy_engine.pairs.spread_calculator import SpreadCalculator
from src.shared.database.base import db_readonly_session, db_transaction
from src.shared.database.models.strategy_models import (
    PairPerformance,
    PairRegistry,
    PairSpread,
    PairTrade,
)


class PairsStrategy:
    """
    Orchestrates the full pairs trading evaluation cycle.

    Usage:
        strategy = PairsStrategy(alpaca_client)
        results = await strategy.run_cycle()
    """

    # How many hourly bars to fetch for spread calculation
    # Needs to be at least z_score_window; we use 3× for buffer
    PRICE_LOOKBACK_BARS = 500

    def __init__(self, alpaca: AlpacaClient):
        self.alpaca = alpaca

    # ------------------------------------------------------------------
    # Main cycle
    # ------------------------------------------------------------------

    async def run_cycle(self) -> List[Dict]:
        """
        Run one full evaluation cycle across all active pairs.

        Returns:
            List of per-pair result dicts with signal, action taken, etc.
        """
        pairs = self._load_active_pairs()
        if not pairs:
            logger.warning("No active pairs found in PairRegistry")
            return []

        account = await self.alpaca.get_account()
        portfolio_equity = float(account.get("equity", 0))

        results = []
        for pair in pairs:
            try:
                result = await self._run_pair_cycle(pair, portfolio_equity)
                results.append(result)
            except Exception as e:
                logger.error(f"Error in pair cycle {pair.symbol1}/{pair.symbol2}: {e}")
                results.append({
                    "pair": f"{pair.symbol1}/{pair.symbol2}",
                    "status": "ERROR",
                    "error": str(e),
                })

        return results

    # ------------------------------------------------------------------
    # Single pair cycle
    # ------------------------------------------------------------------

    async def _run_pair_cycle(
        self, pair: PairRegistry, portfolio_equity: float
    ) -> Dict:
        sym1, sym2 = pair.symbol1, pair.symbol2
        logger.info(f"Evaluating pair: {sym1}/{sym2}")

        # 1. Fetch prices (live intraday from Alpaca — includes today's bars)
        prices1, prices2 = await self._fetch_prices(pair)
        if prices1.empty or prices2.empty:
            logger.warning(f"No price data for {sym1}/{sym2} — skipping")
            return {"pair": f"{sym1}/{sym2}", "status": "NO_DATA"}

        # 2. Calculate spread + z-score
        calc = SpreadCalculator(
            hedge_ratio=float(pair.hedge_ratio),
            z_score_window=int(pair.z_score_window),
        )
        spread_series, z_series, current_z = calc.calculate(prices1, prices2)

        if current_z is None:
            logger.warning(f"Insufficient data for z-score: {sym1}/{sym2}")
            return {"pair": f"{sym1}/{sym2}", "status": "INSUFFICIENT_DATA"}

        p1, p2 = calc.current_prices(prices1, prices2)

        # 3. Persist spread/z-score
        self._store_spread(pair, spread_series, z_series, prices1, prices2)

        # 4. Generate signal
        sig_gen = SignalGenerator(pair)
        signal = sig_gen.generate(current_z, persist=True)

        if signal is None:
            return {
                "pair": f"{sym1}/{sym2}",
                "status": "NO_SIGNAL",
                "z_score": round(current_z, 4),
            }

        logger.info(f"Signal [{signal.signal_type}] for {sym1}/{sym2} z={current_z:.3f}")

        # 5. Execute
        executor = PairExecutor(pair, self.alpaca)
        action = "NONE"

        if signal.signal_type in ("LONG_SPREAD", "SHORT_SPREAD"):
            if p1 is None or p2 is None:
                return {"pair": f"{sym1}/{sym2}", "status": "NO_PRICE"}
            sizer = KellySizer(pair)
            qty1, qty2 = sizer.calculate_size(portfolio_equity, p1, p2)
            trade = await executor.open_pair_trade(
                signal=signal, qty1=qty1, qty2=qty2,
                current_price1=p1, current_price2=p2,
            )
            action = f"OPEN ({signal.signal_type})" if trade else "OPEN_FAILED"

        elif signal.signal_type in ("EXIT", "STOP_LOSS", "EXPIRE"):
            open_trade = self._get_open_trade(pair)
            if open_trade:
                success = await executor.close_pair_trade(
                    trade=open_trade,
                    exit_z=current_z,
                    exit_reason=signal.signal_type,
                    current_price1=p1,
                    current_price2=p2,
                )
                action = f"CLOSE ({signal.signal_type})" if success else "CLOSE_FAILED"

        # 6. Update performance metrics
        self._update_performance(pair)

        return {
            "pair": f"{sym1}/{sym2}",
            "status": "OK",
            "z_score": round(current_z, 4),
            "signal": signal.signal_type,
            "action": action,
        }

    # ------------------------------------------------------------------
    # Data helpers
    # ------------------------------------------------------------------

    def _load_active_pairs(self) -> List[PairRegistry]:
        with db_readonly_session() as session:
            pairs = (
                session.query(PairRegistry)
                .filter(PairRegistry.is_active.is_(True))
                .all()
            )
            for p in pairs:
                session.expunge(p)
            return pairs

    async def _fetch_prices(self, pair: PairRegistry) -> Tuple[pd.Series, pd.Series]:
        """
        Fetch the last PRICE_LOOKBACK_BARS hourly closes from Alpaca.

        Using Alpaca instead of the DB because the DB is populated end-of-day
        by the Yahoo flow — it has no data for today during market hours.
        Alpaca returns live intraday bars including the current incomplete bar.
        """
        sym1, sym2 = pair.symbol1, pair.symbol2
        p1 = await self.alpaca.get_bars(sym1, limit=self.PRICE_LOOKBACK_BARS)
        p2 = await self.alpaca.get_bars(sym2, limit=self.PRICE_LOOKBACK_BARS)
        return p1, p2

    def _get_open_trade(self, pair: PairRegistry) -> Optional[PairTrade]:
        with db_readonly_session() as session:
            trade = (
                session.query(PairTrade)
                .filter(
                    PairTrade.pair_id == pair.id,
                    PairTrade.status == "OPEN",
                )
                .order_by(PairTrade.entry_time.desc())
                .first()
            )
            if trade:
                session.expunge(trade)
            return trade

    def _store_spread(
        self,
        pair: PairRegistry,
        spread_series: pd.Series,
        z_series: pd.Series,
        prices1: pd.Series,
        prices2: pd.Series,
    ) -> None:
        """Persist the latest spread/z-score bar to PairSpread."""
        if spread_series.empty:
            return

        last_ts = spread_series.index[-1]
        spread_val = float(spread_series.iloc[-1])
        z_val = float(z_series.iloc[-1]) if not z_series.empty else None
        p1_val = float(prices1.iloc[-1]) if not prices1.empty else None
        p2_val = float(prices2.iloc[-1]) if not prices2.empty else None

        row = PairSpread(
            pair_id=pair.id,
            timestamp=last_ts.to_pydatetime(),
            price1=p1_val,
            price2=p2_val,
            spread=spread_val,
            z_score=z_val,
            hedge_ratio=float(pair.hedge_ratio),
        )
        with db_transaction() as session:
            session.add(row)

    def _update_performance(self, pair: PairRegistry) -> None:
        """Recompute and upsert today's PairPerformance row."""
        today = datetime.now(timezone.utc).date()

        with db_readonly_session() as session:
            trades = (
                session.query(PairTrade)
                .filter(
                    PairTrade.pair_id == pair.id,
                    PairTrade.status.in_(["CLOSED", "STOPPED"]),
                )
                .all()
            )
            for t in trades:
                session.expunge(t)

        if not trades:
            return

        total = len(trades)
        wins = [t for t in trades if (t.pnl or 0) > 0]
        win_rate = len(wins) / total if total > 0 else 0.0
        avg_pnl = sum(t.pnl or 0 for t in trades) / total
        total_pnl = sum(t.pnl or 0 for t in trades)
        hold_times = [t for t in trades if t.entry_time and t.exit_time]
        avg_hold = (
            sum(
                (t.exit_time - t.entry_time).total_seconds() / 3600  # type: ignore[operator,misc]
                for t in hold_times
            )
            / len(hold_times)
            if hold_times else 0.0
        )

        with db_transaction() as session:
            perf = (
                session.query(PairPerformance)
                .filter(PairPerformance.pair_id == pair.id, PairPerformance.date == today)
                .first()
            )
            if perf is None:
                perf = PairPerformance(pair_id=pair.id, date=today)
                session.add(perf)

            perf.total_trades = total
            perf.winning_trades = len(wins)
            perf.win_rate = win_rate
            perf.avg_pnl = avg_pnl
            perf.total_pnl = total_pnl
            perf.avg_hold_hours = avg_hold
