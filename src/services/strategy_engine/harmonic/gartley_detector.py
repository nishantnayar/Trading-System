"""
Gartley harmonic pattern detector.

Pattern structure (bullish):
    X -> A  (initial leg, downward)
    A -> B  (retracement upward, 61.8% of XA)
    B -> C  (pullback downward, 38.2-88.6% of AB)
    C -> D  (extension downward, 127.2-161.8% of BC; D at 78.6% retracement of XA)

Bearish is the mirror: X below A, pattern inverted.

Usage:
    detector = GartleyDetector(prices)
    patterns = detector.find_patterns()
    for p in patterns:
        print(p.direction, p.d_price, p.stop_loss, p.targets)
"""

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import pandas as pd
from loguru import logger

# ---------------------------------------------------------------------------
# Fibonacci tolerances
# ---------------------------------------------------------------------------
_FIB_TOL = 0.03  # +/- 3% tolerance on each ratio check

# Gartley Fibonacci ratios
_AB_XA = 0.618
_BC_AB_MIN = 0.382
_BC_AB_MAX = 0.886
_CD_BC_MIN = 1.272
_CD_BC_MAX = 1.618
_XD_XA = 0.786  # defines the Gartley (vs other harmonic patterns)


def _within(value: float, target: float, tol: float = _FIB_TOL) -> bool:
    return abs(value - target) <= tol


def _ratio(leg_a: float, leg_b: float) -> float:
    """Return abs(leg_a) / abs(leg_b), or inf if leg_b is zero."""
    if abs(leg_b) < 1e-10:
        return float("inf")
    return abs(leg_a) / abs(leg_b)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------
@dataclass
class SwingPoint:
    index: int
    price: float
    timestamp: pd.Timestamp


@dataclass
class GartleyPattern:
    direction: str  # 'bullish' or 'bearish'
    X: SwingPoint
    A: SwingPoint
    B: SwingPoint
    C: SwingPoint
    D: SwingPoint
    # Key prices derived from D
    stop_loss: float = 0.0
    targets: List[float] = field(default_factory=list)
    # Set by caller before passing to HarmonicExecutor
    symbol: str = ""

    @property
    def d_price(self) -> float:
        return self.D.price

    @property
    def d_timestamp(self) -> pd.Timestamp:
        return self.D.timestamp

    def to_dict(self) -> dict:
        return {
            "direction": self.direction,
            "X_price": self.X.price,
            "A_price": self.A.price,
            "B_price": self.B.price,
            "C_price": self.C.price,
            "D_price": self.D.price,
            "D_timestamp": self.D.timestamp,
            "stop_loss": self.stop_loss,
            "target_1": self.targets[0] if len(self.targets) > 0 else None,
            "target_2": self.targets[1] if len(self.targets) > 1 else None,
        }


# ---------------------------------------------------------------------------
# Swing point detection
# ---------------------------------------------------------------------------
def find_swing_points(
    prices: pd.Series, order: int = 5
) -> Tuple[List[SwingPoint], List[SwingPoint]]:
    """
    Identify local swing highs and lows using a rolling window of `order` bars
    on each side.

    Returns (swing_highs, swing_lows).
    """
    highs: List[SwingPoint] = []
    lows: List[SwingPoint] = []

    vals = prices.values
    times = prices.index

    for i in range(order, len(vals) - order):
        window = vals[i - order : i + order + 1]
        center = vals[i]
        if center == window.max():
            highs.append(SwingPoint(index=i, price=float(center), timestamp=times[i]))
        if center == window.min():
            lows.append(SwingPoint(index=i, price=float(center), timestamp=times[i]))

    return highs, lows


def _merge_and_sort(
    highs: List[SwingPoint], lows: List[SwingPoint]
) -> List[SwingPoint]:
    """Merge highs and lows sorted by bar index."""
    return sorted(highs + lows, key=lambda s: s.index)


# ---------------------------------------------------------------------------
# Fibonacci validation
# ---------------------------------------------------------------------------
def _validate_gartley(
    X: SwingPoint, A: SwingPoint, B: SwingPoint, C: SwingPoint, D: SwingPoint
) -> bool:
    """Return True if XABCD satisfies Gartley Fibonacci constraints."""
    xa = A.price - X.price
    ab = B.price - A.price
    bc = C.price - B.price
    cd = D.price - C.price
    # XD: D retraces 78.6% of XA measured from A back toward X.
    # ad = A - D (bullish: D is below A, ad is positive fraction of xa)
    ad = A.price - D.price

    # AB should retrace 61.8% of XA (opposite direction)
    if not _within(_ratio(ab, xa), _AB_XA):
        return False

    # BC retraces 38.2-88.6% of AB (opposite direction to AB)
    bc_ab = _ratio(bc, ab)
    if not (_BC_AB_MIN - _FIB_TOL <= bc_ab <= _BC_AB_MAX + _FIB_TOL):
        return False

    # CD extends 127.2-161.8% of BC (opposite direction to BC)
    cd_bc = _ratio(cd, bc)
    if not (_CD_BC_MIN - _FIB_TOL <= cd_bc <= _CD_BC_MAX + _FIB_TOL):
        return False

    # XD/XA = 78.6%: D is 78.6% of XA away from A (toward X)
    if not _within(_ratio(ad, xa), _XD_XA):
        return False

    return True


def _direction_valid(
    X: SwingPoint, A: SwingPoint, B: SwingPoint, C: SwingPoint, D: SwingPoint
) -> Optional[str]:
    """
    Enforce leg directions for bullish / bearish Gartley.
    Returns 'bullish', 'bearish', or None if legs are inconsistent.

    Bullish : X low, A high, B low, C high, D low  -> XA up, AB down, BC up, CD down
    Bearish : X high, A low, B high, C low, D high -> XA down, AB up, BC down, CD up
    """
    xa_up = A.price > X.price
    ab_down = B.price < A.price
    bc_up = C.price > B.price
    cd_down = D.price < C.price

    if xa_up and ab_down and bc_up and cd_down:
        return "bullish"

    xa_down = A.price < X.price
    ab_up = B.price > A.price
    bc_down = C.price < B.price
    cd_up = D.price > C.price

    if xa_down and ab_up and bc_down and cd_up:
        return "bearish"

    return None


# ---------------------------------------------------------------------------
# Target and stop-loss calculation
# ---------------------------------------------------------------------------
def _compute_levels(
    pattern: str, X: SwingPoint, A: SwingPoint, D: SwingPoint
) -> Tuple[float, List[float]]:
    """
    Return (stop_loss, [target_1, target_2]).

    Stop-loss: beyond X (bullish: below X; bearish: above X).
    Targets: A retracement (38.2% and 61.8% of AD leg).
    """
    ad = abs(A.price - D.price)
    if pattern == "bullish":
        # 5% buffer below D toward X
        stop_loss = D.price - 0.05 * abs(X.price - D.price)
        stop_loss = min(stop_loss, X.price * 0.995)
        target_1 = D.price + 0.382 * ad
        target_2 = D.price + 0.618 * ad
    else:
        stop_loss = D.price + 0.05 * abs(X.price - D.price)
        stop_loss = max(stop_loss, X.price * 1.005)
        target_1 = D.price - 0.382 * ad
        target_2 = D.price - 0.618 * ad

    return round(stop_loss, 4), [round(target_1, 4), round(target_2, 4)]


# ---------------------------------------------------------------------------
# Main detector
# ---------------------------------------------------------------------------
class GartleyDetector:
    """
    Scan a price series for completed Gartley harmonic patterns.

    Parameters
    ----------
    prices : pd.Series
        Close prices with a DatetimeIndex (UTC-aware preferred).
        At least 20 bars recommended; 100+ for reliable swing detection.
    swing_order : int
        Number of bars on each side required to confirm a swing high/low.
        Lower = more sensitive; higher = fewer but cleaner swings.
    max_patterns : int
        Stop after finding this many patterns (most-recent first).
    """

    def __init__(
        self,
        prices: pd.Series,
        swing_order: int = 5,
        max_patterns: int = 10,
    ) -> None:
        if len(prices) < 2 * swing_order + 1:
            raise ValueError(
                f"Need at least {2 * swing_order + 1} bars; got {len(prices)}"
            )
        self.prices = prices
        self.swing_order = swing_order
        self.max_patterns = max_patterns

    def find_patterns(self) -> List[GartleyPattern]:
        """
        Return a list of GartleyPattern objects found in the price series,
        ordered most-recent D point first.
        """
        highs, lows = find_swing_points(self.prices, order=self.swing_order)
        swings = _merge_and_sort(highs, lows)

        if len(swings) < 5:
            logger.debug(
                "Not enough swing points ({}) to search for Gartley patterns",
                len(swings),
            )
            return []

        patterns: List[GartleyPattern] = []

        # Slide a window of 5 consecutive swing points
        for i in range(len(swings) - 4):
            X, A, B, C, D = swings[i : i + 5]

            direction = _direction_valid(X, A, B, C, D)
            if direction is None:
                continue

            if not _validate_gartley(X, A, B, C, D):
                continue

            stop_loss, targets = _compute_levels(direction, X, A, D)

            pattern = GartleyPattern(
                direction=direction,
                X=X,
                A=A,
                B=B,
                C=C,
                D=D,
                stop_loss=stop_loss,
                targets=targets,
            )
            patterns.append(pattern)
            logger.info(
                "Gartley {} found: D={:.4f} at {} | SL={:.4f} | T1={:.4f} | T2={:.4f}",
                direction,
                D.price,
                D.timestamp,
                stop_loss,
                targets[0],
                targets[1],
            )

            if len(patterns) >= self.max_patterns:
                break

        # Return most-recent D first
        patterns.sort(key=lambda p: p.D.index, reverse=True)
        return patterns


# ---------------------------------------------------------------------------
# Convenience scanner for a symbol universe
# ---------------------------------------------------------------------------
def scan_universe(
    symbol_prices: dict,
    swing_order: int = 5,
) -> dict:
    """
    Run GartleyDetector across a dict of {symbol: pd.Series} and return
    {symbol: List[GartleyPattern]} for symbols that have at least one pattern.

    Parameters
    ----------
    symbol_prices : dict
        Keys are ticker strings; values are close-price Series.
    swing_order : int
        Passed through to GartleyDetector.
    """
    results: dict = {}
    for symbol, prices in symbol_prices.items():
        try:
            detector = GartleyDetector(prices, swing_order=swing_order)
            found = detector.find_patterns()
            if found:
                results[symbol] = found
                logger.info("{}: {} Gartley pattern(s) detected", symbol, len(found))
        except Exception as exc:
            logger.warning("GartleyDetector failed for {}: {}", symbol, exc)
    return results
