"""
Pair Executor

Wraps AlpacaClient to place and close two-legged pair trades.

Responsibilities:
    - Place LONG_SPREAD / SHORT_SPREAD orders (two market orders simultaneously)
    - Close both legs of an open trade
    - Emergency stop: liquidate both legs with market orders
    - Create PairTrade records on open; update on close
    - Store Alpaca order IDs in PairTrade for reconciliation

Signal → Order mapping:
    LONG_SPREAD:  buy symbol1 (qty1),  sell short symbol2 (qty2)
    SHORT_SPREAD: sell short symbol1 (qty1), buy symbol2 (qty2)
"""

import asyncio
from datetime import datetime, timezone
from typing import Optional

from loguru import logger

from src.services.alpaca.client import AlpacaClient
from src.shared.database.base import db_readonly_session, db_transaction
from src.shared.database.models.strategy_models import (
    PairRegistry,
    PairSignal,
    PairTrade,
)


class PairExecutor:
    """
    Places and closes pair trades via Alpaca.

    Usage:
        executor = PairExecutor(pair, alpaca_client)

        trade = await executor.open_pair_trade(signal, qty1=10, qty2=8)
        await executor.close_pair_trade(trade)
        await executor.emergency_stop()
    """

    def __init__(self, pair: PairRegistry, alpaca: AlpacaClient):
        self.pair = pair
        self.alpaca = alpaca

    # ------------------------------------------------------------------
    # Open a new pair trade
    # ------------------------------------------------------------------

    async def open_pair_trade(
        self,
        signal: PairSignal,
        qty1: int,
        qty2: int,
        current_price1: Optional[float] = None,
        current_price2: Optional[float] = None,
    ) -> Optional[PairTrade]:
        """
        Submit both legs to Alpaca and record a PairTrade in the DB.

        Args:
            signal:         PairSignal that triggered this trade
            qty1:           Shares of symbol1
            qty2:           Shares of symbol2
            current_price1: Last known price for symbol1 (for DB record only)
            current_price2: Last known price for symbol2 (for DB record only)

        Returns:
            PairTrade ORM object (persisted) or None if orders failed.
        """
        sym1 = self.pair.symbol1
        sym2 = self.pair.symbol2
        side = signal.signal_type  # LONG_SPREAD or SHORT_SPREAD

        # Determine buy/sell sides
        if side == "LONG_SPREAD":
            side1, side2 = "buy", "sell"
        elif side == "SHORT_SPREAD":
            side1, side2 = "sell", "buy"
        else:
            logger.warning(f"open_pair_trade called with non-entry signal: {side}")
            return None

        logger.info(
            f"Opening {side}: {side1} {qty1} {sym1} / {side2} {qty2} {sym2}  "
            f"z={signal.z_score:.3f}"
        )

        # Place both orders concurrently
        try:
            order1_task = self.alpaca.place_order(
                symbol=sym1, qty=qty1, side=side1, order_type="market", time_in_force="day"
            )
            order2_task = self.alpaca.place_order(
                symbol=sym2, qty=qty2, side=side2, order_type="market", time_in_force="day"
            )
            order1, order2 = await asyncio.gather(order1_task, order2_task)

        except Exception as e:
            logger.error(f"Failed to place pair orders for {sym1}/{sym2}: {e}")
            return None

        trade = PairTrade(
            pair_id=self.pair.id,
            entry_time=datetime.now(timezone.utc),
            entry_z_score=signal.z_score,
            side=side,
            qty1=qty1,
            qty2=qty2,
            entry_price1=current_price1,
            entry_price2=current_price2,
            order_id1=order1.get("id"),
            order_id2=order2.get("id"),
            status="OPEN",
        )

        with db_transaction() as session:
            session.add(trade)
            session.flush()
            trade_id = trade.id

        # Mark signal as acted on
        self._mark_signal_acted(signal.id)

        logger.info(
            f"PairTrade created: id={trade_id} "
            f"[{sym1} order={order1.get('id')}, "
            f"{sym2} order={order2.get('id')}]"
        )
        return trade

    # ------------------------------------------------------------------
    # Close an existing trade
    # ------------------------------------------------------------------

    async def close_pair_trade(
        self,
        trade: PairTrade,
        exit_z: Optional[float] = None,
        exit_reason: str = "EXIT",
        current_price1: Optional[float] = None,
        current_price2: Optional[float] = None,
    ) -> bool:
        """
        Close both legs of an open trade.

        Args:
            trade:          Open PairTrade to close
            exit_z:         Current z-score at exit
            exit_reason:    "EXIT", "STOP_LOSS", or "EXPIRE"
            current_price1: Fill price for symbol1 (for P&L calc)
            current_price2: Fill price for symbol2 (for P&L calc)

        Returns:
            True if both legs closed successfully.
        """
        sym1 = self.pair.symbol1
        sym2 = self.pair.symbol2

        logger.info(
            f"Closing trade id={trade.id} ({sym1}/{sym2}) "
            f"reason={exit_reason} z={exit_z}"
        )

        try:
            close1 = self.alpaca.close_position(sym1)
            close2 = self.alpaca.close_position(sym2)
            await asyncio.gather(close1, close2)
        except Exception as e:
            logger.error(f"Failed to close positions for {sym1}/{sym2}: {e}")
            return False

        pnl, pnl_pct = _compute_pnl(trade, current_price1, current_price2)

        with db_transaction() as session:
            db_trade = session.query(PairTrade).filter_by(id=trade.id).first()
            if db_trade:
                db_trade.exit_time = datetime.now(timezone.utc)
                db_trade.exit_z_score = exit_z
                db_trade.exit_price1 = current_price1
                db_trade.exit_price2 = current_price2
                db_trade.exit_reason = exit_reason
                db_trade.pnl = pnl
                db_trade.pnl_pct = pnl_pct
                db_trade.status = "STOPPED" if exit_reason == "STOP_LOSS" else "CLOSED"

        logger.info(
            f"Trade id={trade.id} closed: pnl={pnl:.2f} ({pnl_pct:.2f}%)"
        )
        return True

    # ------------------------------------------------------------------
    # Emergency stop
    # ------------------------------------------------------------------

    async def emergency_stop(self) -> None:
        """
        Close all open positions for this pair immediately.

        Calls close_position for both symbols. Ignores errors from
        positions that are already closed (no position to close).
        """
        sym1 = self.pair.symbol1
        sym2 = self.pair.symbol2
        logger.warning(f"EMERGENCY STOP triggered for {sym1}/{sym2}")

        for sym in [sym1, sym2]:
            try:
                await self.alpaca.close_position(sym)
                logger.info(f"Emergency close sent for {sym}")
            except Exception as e:
                logger.warning(f"Emergency close for {sym} raised: {e} (may already be flat)")

        # Mark all OPEN trades for this pair as STOPPED
        with db_transaction() as session:
            open_trades = (
                session.query(PairTrade)
                .filter(
                    PairTrade.pair_id == self.pair.id,
                    PairTrade.status == "OPEN",
                )
                .all()
            )
            now = datetime.now(timezone.utc)
            for t in open_trades:
                t.status = "STOPPED"
                t.exit_time = now
                t.exit_reason = "EMERGENCY_STOP"

        logger.warning(f"Emergency stop complete for {sym1}/{sym2}")

    # ------------------------------------------------------------------

    def _mark_signal_acted(self, signal_id: int) -> None:
        with db_transaction() as session:
            sig = session.query(PairSignal).filter_by(id=signal_id).first()
            if sig:
                sig.acted_on = True


# ---------------------------------------------------------------------------
# P&L helper
# ---------------------------------------------------------------------------

def _compute_pnl(
    trade: PairTrade,
    exit_price1: Optional[float],
    exit_price2: Optional[float],
):
    """
    Compute realized P&L given exit prices.
    Returns (pnl, pnl_pct) or (None, None) if prices unavailable.
    """
    if (
        trade.entry_price1 is None
        or trade.entry_price2 is None
        or exit_price1 is None
        or exit_price2 is None
    ):
        return None, None

    ep1 = float(trade.entry_price1)
    ep2 = float(trade.entry_price2)
    xp1 = float(exit_price1)
    xp2 = float(exit_price2)
    q1 = float(trade.qty1)
    q2 = float(trade.qty2)

    if trade.side == "LONG_SPREAD":
        pnl = q1 * (xp1 - ep1) - q2 * (xp2 - ep2)
    else:  # SHORT_SPREAD
        pnl = -q1 * (xp1 - ep1) + q2 * (xp2 - ep2)

    entry_cost = q1 * ep1 + q2 * ep2
    pnl_pct = (pnl / entry_cost * 100) if entry_cost > 0 else 0.0
    return pnl, pnl_pct
