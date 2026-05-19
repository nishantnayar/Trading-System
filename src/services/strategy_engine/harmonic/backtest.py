"""
Harmonic pattern walk-forward backtester.

For each bar in [start_date, end_date]:
  - Slide a window of `lookback_bars` EOD bars ending at that bar
  - Run GartleyDetector on the window
  - For any newly detected pattern (D point is the most recent bar):
      - Simulate entry at close of D bar
      - Walk forward bar-by-bar, checking check_exit() at each bar's close
      - Record exit bar, exit price, exit reason, hold bars, P&L

No live orders are placed -- this is purely in-process simulation.

Usage:
    from src.services.strategy_engine.harmonic.backtest import HarmonicBacktester
    results = HarmonicBacktester().run(prices, symbol="AAPL")
    summary = HarmonicBacktester.summary(results)
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from src.services.strategy_engine.harmonic.gartley_detector import GartleyDetector

# Maximum bars to hold a trade before forcing an exit at market
_MAX_HOLD_BARS = 60


@dataclass
class BacktestTrade:
    symbol: str
    direction: str
    side: str
    entry_bar: int
    entry_date: pd.Timestamp
    entry_price: float
    stop_loss: float
    target_1: float
    target_2: float
    quality_score: float
    qty: int = 1
    exit_bar: Optional[int] = None
    exit_date: Optional[pd.Timestamp] = None
    exit_price: Optional[float] = None
    exit_reason: Optional[str] = None
    hold_bars: Optional[int] = None
    pnl: Optional[float] = None
    pnl_pct: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            "symbol": self.symbol,
            "direction": self.direction,
            "side": self.side,
            "entry_date": self.entry_date,
            "entry_price": self.entry_price,
            "stop_loss": self.stop_loss,
            "target_1": self.target_1,
            "target_2": self.target_2,
            "quality_score": self.quality_score,
            "exit_date": self.exit_date,
            "exit_price": self.exit_price,
            "exit_reason": self.exit_reason,
            "hold_bars": self.hold_bars,
            "pnl": self.pnl,
            "pnl_pct": self.pnl_pct,
        }


@dataclass
class BacktestSummary:
    symbol: str
    total_trades: int
    win_rate: float
    avg_pnl: float
    total_pnl: float
    profit_factor: float
    max_drawdown: float
    sharpe: float
    avg_hold_bars: float
    target1_rate: float
    target2_rate: float
    stop_rate: float
    trades: List[BacktestTrade] = field(default_factory=list)


class HarmonicBacktester:
    """
    Walk-forward backtester for Gartley patterns on a single symbol.

    Parameters
    ----------
    lookback_bars : int
        Bars of history fed to GartleyDetector at each step (default 252).
    swing_order : int
        Swing point detection sensitivity (default 5).
    long_only : bool
        Skip bearish patterns if True (default True, mirrors live flow).
    """

    def __init__(
        self,
        lookback_bars: int = 252,
        swing_order: int = 5,
        long_only: bool = True,
    ) -> None:
        self.lookback_bars = lookback_bars
        self.swing_order = swing_order
        self.long_only = long_only

    def run(
        self,
        prices: pd.Series,
        symbol: str = "",
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[BacktestTrade]:
        """
        Run the walk-forward simulation.

        Parameters
        ----------
        prices : pd.Series
            Full EOD close series with DatetimeIndex.
        symbol : str
            Ticker label stored on each BacktestTrade.
        start_date / end_date : date
            Slice the simulation window (defaults to full series).

        Returns
        -------
        List[BacktestTrade] with all simulated trades (closed + expired).
        """
        prices = prices.sort_index()

        # Collapse intraday bars to one close per calendar date (last bar of each day).
        # The DB stores yahoo_adjusted as hourly bars (~7/day); the detector needs
        # daily bars to find meaningful multi-week swing patterns.
        norm = prices.index.normalize()
        prices = prices.groupby(norm).last()
        idx = pd.DatetimeIndex(prices.index)
        if idx.tz is None:
            idx = idx.tz_localize("UTC")
        else:
            idx = idx.tz_convert("UTC")
        prices.index = idx

        if start_date is not None:
            prices = prices[prices.index >= pd.Timestamp(start_date, tz="UTC")]
        if end_date is not None:
            prices = prices[prices.index <= pd.Timestamp(end_date, tz="UTC")]

        if len(prices) < self.lookback_bars + 1:
            return []

        vals = prices.to_numpy(dtype=float)
        times = prices.index

        trades: List[BacktestTrade] = []
        # Track the last D-bar index where we opened so we don't double-enter
        open_d_indices: set = set()

        for i in range(self.lookback_bars, len(vals)):
            window_prices = prices.iloc[i - self.lookback_bars : i]

            try:
                detector = GartleyDetector(window_prices, swing_order=self.swing_order)
                patterns = detector.find_patterns()
            except ValueError:
                continue

            if not patterns:
                continue

            # Only trade the most-recent pattern if D is new (not seen before)
            best = patterns[0]
            if self.long_only and best.direction != "bullish":
                continue

            # best.D.index is positional within the window slice.
            # Translate to absolute position in vals/times.
            window_start = i - self.lookback_bars
            d_global = window_start + best.D.index

            # D must be recent: within the last swing_order*2 bars of the window.
            # swing detection needs swing_order bars after D, so D can't be the very last bar
            min_d = i - self.swing_order * 2 - 1
            if d_global < min_d:
                continue
            if d_global in open_d_indices:
                continue

            open_d_indices.add(d_global)
            entry_price = float(vals[d_global])  # close of D bar
            side = "buy" if best.direction == "bullish" else "sell"

            trade = BacktestTrade(
                symbol=symbol,
                direction=best.direction,
                side=side,
                entry_bar=d_global,
                entry_date=times[d_global],
                entry_price=entry_price,
                stop_loss=best.stop_loss,
                target_1=best.targets[0],
                target_2=best.targets[1],
                quality_score=best.quality_score,
            )

            # Walk forward from bar after D to find exit
            _simulate_exit(trade, vals, times, d_global + 1)
            trades.append(trade)

        return trades

    @staticmethod
    def summary(trades: List[BacktestTrade], symbol: str = "") -> BacktestSummary:
        """Compute aggregate performance metrics from a list of BacktestTrade."""
        closed = [t for t in trades if t.pnl is not None]
        if not closed:
            return BacktestSummary(
                symbol=symbol,
                total_trades=0,
                win_rate=0.0,
                avg_pnl=0.0,
                total_pnl=0.0,
                profit_factor=0.0,
                max_drawdown=0.0,
                sharpe=0.0,
                avg_hold_bars=0.0,
                target1_rate=0.0,
                target2_rate=0.0,
                stop_rate=0.0,
                trades=trades,
            )

        pnls: List[float] = [t.pnl for t in closed if t.pnl is not None]
        wins = [p for p in pnls if p > 0]
        losses = [p for p in pnls if p <= 0]

        win_rate = len(wins) / len(closed)
        avg_pnl = float(np.mean(pnls)) if pnls else 0.0
        total_pnl = float(np.sum(pnls)) if pnls else 0.0
        gross_profit = float(sum(wins)) if wins else 0.0
        gross_loss = float(abs(sum(losses))) if losses else 0.0
        if gross_loss > 0:
            profit_factor = gross_profit / gross_loss
        elif gross_profit > 0:
            profit_factor = float("inf")
        else:
            profit_factor = 0.0

        # Equity curve drawdown (cumulative pnl, normalized)
        cum: np.ndarray = np.cumsum(pnls)
        peak = np.maximum.accumulate(cum)
        dd = (cum - peak) / (peak + 1e-9)
        max_drawdown = float(abs(dd.min())) if len(dd) > 0 else 0.0

        # Sharpe (annualised from per-trade pnl_pct)
        pnl_pcts: List[float] = [t.pnl_pct for t in closed if t.pnl_pct is not None]
        if len(pnl_pcts) > 1:
            sharpe = float(np.mean(pnl_pcts) / (np.std(pnl_pcts) + 1e-9) * np.sqrt(252))
        else:
            sharpe = 0.0

        hold_bars = [t.hold_bars for t in closed if t.hold_bars]
        avg_hold = float(np.mean(hold_bars)) if hold_bars else 0.0

        reasons = [t.exit_reason for t in closed]
        n = len(closed)
        t1_rate = reasons.count("TARGET_1") / n
        t2_rate = reasons.count("TARGET_2") / n
        stop_rate = reasons.count("STOP_LOSS") / n

        return BacktestSummary(
            symbol=symbol,
            total_trades=n,
            win_rate=round(win_rate, 4),
            avg_pnl=round(avg_pnl, 4),
            total_pnl=round(total_pnl, 4),
            profit_factor=round(profit_factor, 4),
            max_drawdown=round(max_drawdown, 4),
            sharpe=round(sharpe, 4),
            avg_hold_bars=round(avg_hold, 1),
            target1_rate=round(t1_rate, 4),
            target2_rate=round(t2_rate, 4),
            stop_rate=round(stop_rate, 4),
            trades=trades,
        )


def run_universe_backtest(
    symbol_prices: Dict[str, pd.Series],
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    lookback_bars: int = 252,
    swing_order: int = 5,
    long_only: bool = True,
) -> Dict[str, BacktestSummary]:
    """
    Run walk-forward backtest across a universe of symbols.

    Returns {symbol: BacktestSummary}.
    """
    backtester = HarmonicBacktester(
        lookback_bars=lookback_bars,
        swing_order=swing_order,
        long_only=long_only,
    )
    results: Dict[str, BacktestSummary] = {}
    for symbol, prices in symbol_prices.items():
        trades = backtester.run(
            prices, symbol=symbol, start_date=start_date, end_date=end_date
        )
        results[symbol] = HarmonicBacktester.summary(trades, symbol=symbol)
    return results


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _simulate_exit(
    trade: BacktestTrade,
    vals: "np.ndarray",
    times: pd.DatetimeIndex,
    entry_i: int,
) -> None:
    """
    Walk forward from entry_i, checking each bar's close against SL/T1/T2.
    Mutates trade in place with exit fields and P&L.
    """
    max_i = min(entry_i + _MAX_HOLD_BARS, len(vals))

    for j in range(entry_i, max_i):
        price = float(vals[j])
        signal = _check_exit(trade, price)
        if signal is not None:
            _fill_exit(trade, j, times[j], price, signal)
            return

    # Time-expired: exit at last bar close
    last_i = max_i - 1
    _fill_exit(trade, last_i, times[last_i], float(vals[last_i]), "EXPIRED")


def _check_exit(trade: BacktestTrade, price: float) -> Optional[str]:
    """Mirror of HarmonicExecutor.check_exit but uses BacktestTrade."""
    t1, t2, sl = trade.target_1, trade.target_2, trade.stop_loss
    if trade.side == "buy":
        if price >= t2:
            return "TARGET_2"
        if price >= t1:
            return "TARGET_1"
        if price <= sl:
            return "STOP_LOSS"
    else:
        if price <= t2:
            return "TARGET_2"
        if price <= t1:
            return "TARGET_1"
        if price >= sl:
            return "STOP_LOSS"
    return None


def _fill_exit(
    trade: BacktestTrade,
    bar_i: int,
    bar_time: pd.Timestamp,
    price: float,
    reason: str,
) -> None:
    trade.exit_bar = bar_i
    trade.exit_date = bar_time
    trade.exit_price = price
    trade.exit_reason = reason
    trade.hold_bars = bar_i - trade.entry_bar

    ep = trade.entry_price
    qty = float(trade.qty)
    if trade.side == "buy":
        pnl = qty * (price - ep)
    else:
        pnl = qty * (ep - price)

    trade.pnl = round(pnl, 4)
    trade.pnl_pct = round(pnl / (qty * ep) * 100.0, 4) if ep > 0 else 0.0
