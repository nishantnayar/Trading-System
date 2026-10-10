"""
Shared P&L math for every strategy (live executors and the backtest engine).

Convention: pnl is in dollars; pnl_pct is a PERCENTAGE of entry cost
(0.25 means 0.25%, not 25%). pair_trade, basket_trade and backtest results
all store pnl_pct in this unit.
"""

from typing import Iterable, Tuple

# (signed quantity, entry price, exit price); quantity > 0 for long, < 0 for short
Leg = Tuple[float, float, float]


def legs_pnl(legs: Iterable[Leg], commission: float = 0.0) -> Tuple[float, float]:
    """
    Realized P&L for any number of legs.

    Returns (pnl, pnl_pct) where pnl_pct is a percentage of gross entry cost
    (sum of |qty| * entry_price). A flat `commission` is deducted from pnl.
    """
    pnl = 0.0
    cost = 0.0
    for qty, entry, exit_ in legs:
        pnl += qty * (exit_ - entry)
        cost += abs(qty) * entry
    pnl -= commission
    pnl_pct = (pnl / cost * 100) if cost > 0 else 0.0
    return pnl, pnl_pct


def pair_pnl(
    side: str,
    qty1: float,
    qty2: float,
    entry1: float,
    entry2: float,
    exit1: float,
    exit2: float,
    commission: float = 0.0,
) -> Tuple[float, float]:
    """
    Realized P&L for a two-leg spread trade.

    LONG_SPREAD:  long symbol1, short symbol2
    SHORT_SPREAD: short symbol1, long symbol2
    """
    sign = 1.0 if side == "LONG_SPREAD" else -1.0
    return legs_pnl(
        [(sign * qty1, entry1, exit1), (-sign * qty2, entry2, exit2)],
        commission=commission,
    )
