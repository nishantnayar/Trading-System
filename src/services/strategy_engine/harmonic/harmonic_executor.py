"""
Harmonic Executor

Places and closes single-leg harmonic pattern trades via Alpaca.

Signal -> Order mapping:
    bullish Gartley D:  buy  (long at point D, exit toward A)
    bearish Gartley D:  sell (short at point D, exit toward A)

Exit triggers (checked by caller each cycle):
    TARGET_1  - price reaches 38.2% retracement of AD
    TARGET_2  - price reaches 61.8% retracement of AD
    STOP_LOSS - price breaches stop level beyond X
    MANUAL    - forced close
"""

import asyncio
from datetime import datetime, timezone
from typing import Optional, Tuple

from loguru import logger

from src.services.alpaca.client import AlpacaClient
from src.services.strategy_engine.harmonic.gartley_detector import GartleyPattern
from src.shared.database.base import db_transaction
from src.shared.database.models.strategy_models import HarmonicTrade

# Fixed position size as fraction of portfolio equity per trade (2% bootstrap).
# Replace with Kelly once trade history is sufficient.
_POSITION_FRACTION = 0.02
_MAX_POSITION_FRACTION = 0.10


def compute_qty(
    portfolio_equity: float,
    entry_price: float,
    fraction: float = _POSITION_FRACTION,
) -> int:
    """
    Return integer share count for a single harmonic leg.

    Caps at _MAX_POSITION_FRACTION of portfolio equity.
    Returns 0 if entry_price is zero or equity is too small for one share.
    """
    if entry_price <= 0 or portfolio_equity <= 0:
        return 0
    target_value = min(
        portfolio_equity * fraction,
        portfolio_equity * _MAX_POSITION_FRACTION,
    )
    qty = int(target_value / entry_price)
    return max(qty, 0)


class HarmonicExecutor:
    """
    Places and closes harmonic pattern trades via Alpaca.

    Usage:
        executor = HarmonicExecutor(alpaca_client)

        trade = await executor.open_trade(pattern, qty=50, current_price=110.5)
        await executor.close_trade(trade, exit_price=125.0, exit_reason="TARGET_1")
        await executor.emergency_stop(trade)
    """

    def __init__(self, alpaca: AlpacaClient) -> None:
        self.alpaca = alpaca

    # ------------------------------------------------------------------
    # Open a new harmonic trade at point D
    # ------------------------------------------------------------------

    async def open_trade(
        self,
        pattern: GartleyPattern,
        qty: int,
        current_price: Optional[float] = None,
        pattern_name: str = "gartley",
    ) -> Optional[HarmonicTrade]:
        """
        Submit a market order at point D and record a HarmonicTrade in the DB.

        Args:
            pattern:       Detected GartleyPattern with XABCD, stop, and targets.
            qty:           Number of shares to trade.
            current_price: Last known fill price (stored in DB; D price used if None).
            pattern_name:  Pattern identifier stored in DB (default 'gartley').

        Returns:
            Persisted HarmonicTrade or None if the order failed.
        """
        if qty <= 0:
            logger.warning(
                "open_trade called with qty={} for {} -- skipping", qty, pattern.symbol if hasattr(pattern, 'symbol') else "unknown"
            )
            return None

        symbol = _symbol_from_pattern(pattern)
        side = "buy" if pattern.direction == "bullish" else "sell"
        entry_price = current_price or pattern.d_price

        logger.info(
            "Opening harmonic {}/{} {} {} shares @ ~{:.4f} | SL={:.4f} T1={:.4f} T2={:.4f}",
            pattern_name,
            pattern.direction,
            side,
            qty,
            entry_price,
            pattern.stop_loss,
            pattern.targets[0],
            pattern.targets[1],
        )

        try:
            order = await self.alpaca.place_order(
                symbol=symbol,
                qty=qty,
                side=side,
                order_type="market",
                time_in_force="day",
            )
        except Exception as exc:
            logger.error("Failed to place harmonic order for {}: {}", symbol, exc)
            return None

        trade = HarmonicTrade(
            symbol=symbol,
            pattern=pattern_name,
            direction=pattern.direction,
            side=side,
            x_price=pattern.X.price,
            a_price=pattern.A.price,
            b_price=pattern.B.price,
            c_price=pattern.C.price,
            d_price=pattern.D.price,
            qty=qty,
            entry_price=entry_price,
            entry_time=datetime.now(timezone.utc),
            order_id=order.get("id"),
            stop_loss=pattern.stop_loss,
            target_1=pattern.targets[0],
            target_2=pattern.targets[1],
            status="OPEN",
        )

        with db_transaction() as session:
            session.add(trade)
            session.flush()
            trade_id = trade.id

        logger.info(
            "HarmonicTrade created: id={} symbol={} order={}",
            trade_id,
            symbol,
            order.get("id"),
        )
        return trade

    # ------------------------------------------------------------------
    # Close an existing harmonic trade
    # ------------------------------------------------------------------

    async def close_trade(
        self,
        trade: HarmonicTrade,
        exit_price: Optional[float] = None,
        exit_reason: str = "MANUAL",
    ) -> bool:
        """
        Close the position and update HarmonicTrade in the DB.

        Args:
            trade:       Open HarmonicTrade to close.
            exit_price:  Fill price at exit (used for P&L).
            exit_reason: 'TARGET_1', 'TARGET_2', 'STOP_LOSS', or 'MANUAL'.

        Returns:
            True if the close order was submitted successfully.
        """
        symbol = trade.symbol
        logger.info(
            "Closing harmonic trade id={} ({}) reason={} price={}",
            trade.id,
            symbol,
            exit_reason,
            exit_price,
        )

        try:
            await self.alpaca.close_position(symbol)
        except Exception as exc:
            logger.error(
                "Failed to close harmonic position for {}: {}", symbol, exc
            )
            return False

        pnl, pnl_pct = _compute_pnl(trade, exit_price)

        with db_transaction() as session:
            db_trade = (
                session.query(HarmonicTrade).filter_by(id=trade.id).first()
            )
            if db_trade:
                db_trade.exit_price = exit_price
                db_trade.exit_time = datetime.now(timezone.utc)
                db_trade.exit_reason = exit_reason
                db_trade.pnl = pnl
                db_trade.pnl_pct = pnl_pct
                db_trade.status = (
                    "STOPPED" if exit_reason == "STOP_LOSS" else "CLOSED"
                )

        logger.info(
            "HarmonicTrade id={} closed: pnl={} ({:.2f}%)",
            trade.id,
            f"{pnl:.2f}" if pnl is not None else "n/a",
            pnl_pct if pnl_pct is not None else 0.0,
        )
        return True

    # ------------------------------------------------------------------
    # Emergency stop
    # ------------------------------------------------------------------

    async def emergency_stop(self, trade: HarmonicTrade) -> None:
        """
        Force-close the position immediately, ignoring errors (may already be flat).
        Marks the trade STOPPED in the DB.
        """
        symbol = trade.symbol
        logger.warning(
            "EMERGENCY STOP triggered for harmonic trade id={} ({})",
            trade.id,
            symbol,
        )
        try:
            await self.alpaca.close_position(symbol)
        except Exception as exc:
            logger.warning(
                "Emergency close for {} raised: {} (may already be flat)",
                symbol,
                exc,
            )

        with db_transaction() as session:
            db_trade = (
                session.query(HarmonicTrade).filter_by(id=trade.id).first()
            )
            if db_trade and db_trade.status == "OPEN":
                db_trade.status = "STOPPED"
                db_trade.exit_time = datetime.now(timezone.utc)
                db_trade.exit_reason = "EMERGENCY_STOP"

        logger.warning(
            "Emergency stop complete for harmonic trade id={}", trade.id
        )

    # ------------------------------------------------------------------
    # Exit signal evaluation (stateless, called each cycle)
    # ------------------------------------------------------------------

    @staticmethod
    def check_exit(
        trade: HarmonicTrade, current_price: float
    ) -> Optional[str]:
        """
        Evaluate whether the current price has hit a target or stop.

        Returns 'TARGET_1', 'TARGET_2', 'STOP_LOSS', or None.
        The caller is responsible for acting on the returned signal.
        """
        t1 = float(trade.target_1)
        t2 = float(trade.target_2)
        sl = float(trade.stop_loss)
        side = trade.side

        if side == "buy":
            if current_price >= t2:
                return "TARGET_2"
            if current_price >= t1:
                return "TARGET_1"
            if current_price <= sl:
                return "STOP_LOSS"
        else:  # sell / short
            if current_price <= t2:
                return "TARGET_2"
            if current_price <= t1:
                return "TARGET_1"
            if current_price >= sl:
                return "STOP_LOSS"

        return None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _symbol_from_pattern(pattern: GartleyPattern) -> str:
    """Extract symbol from pattern; raises if not set."""
    sym: Optional[str] = getattr(pattern, "symbol", None)
    if not sym:
        raise ValueError(
            "GartleyPattern has no 'symbol' attribute. "
            "Set pattern.symbol before passing to HarmonicExecutor."
        )
    return sym


def _compute_pnl(
    trade: HarmonicTrade,
    exit_price: Optional[float],
) -> Tuple[Optional[float], Optional[float]]:
    """Return (pnl, pnl_pct) or (None, None) if prices unavailable."""
    if trade.entry_price is None or exit_price is None:
        return None, None

    ep = float(trade.entry_price)
    xp = float(exit_price)
    qty = float(trade.qty)

    if trade.side == "buy":
        pnl = qty * (xp - ep)
    else:
        pnl = qty * (ep - xp)

    cost = qty * ep
    pnl_pct = (pnl / cost * 100.0) if cost > 0 else 0.0
    return round(pnl, 4), round(pnl_pct, 4)
