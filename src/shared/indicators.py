"""
Technical Indicator Calculations (shared by the analytics service and the UI)
RSI, MACD, Moving Averages, Bollinger Bands, etc.

Pure pandas/numpy implementation - no numba or scipy dependency.
All functions accept a list of floats and return a single value (or dict).
"""

from typing import Dict, List, Optional

import numpy as np
import pandas as pd


def calculate_sma(prices: List[float], period: int) -> Optional[float]:
    """
    Calculate Simple Moving Average.

    Args:
        prices: List of prices
        period: Lookback period

    Returns:
        SMA value or None if insufficient data
    """
    if len(prices) < period:
        return None
    s = pd.Series(prices, dtype=float)
    result = s.rolling(window=period).mean().iloc[-1]
    return float(result) if pd.notna(result) else None


def calculate_ema(
    prices: List[float], period: int, alpha: Optional[float] = None
) -> Optional[float]:
    """
    Calculate Exponential Moving Average.

    Args:
        prices: List of prices
        period: Span for EMA (alpha ignored; kept for API compatibility)

    Returns:
        EMA value or None if insufficient data
    """
    if len(prices) < period:
        return None
    s = pd.Series(prices, dtype=float)
    result = s.ewm(span=period, adjust=False).mean().iloc[-1]
    return float(result) if pd.notna(result) else None


def calculate_rsi(prices: List[float], period: int = 14) -> Optional[float]:
    """
    Calculate Relative Strength Index (Wilder's method).

    Args:
        prices: List of closing prices
        period: RSI period (default 14)

    Returns:
        RSI value (0-100) or None if insufficient data
    """
    if len(prices) < period + 1:
        return None
    s = pd.Series(prices, dtype=float)
    delta = s.diff()
    gain = delta.clip(lower=0.0)
    loss = -delta.clip(upper=0.0)
    # Wilder smoothing: alpha = 1/period
    avg_gain = gain.ewm(alpha=1.0 / period, adjust=False).mean()
    avg_loss = loss.ewm(alpha=1.0 / period, adjust=False).mean()
    # Avoid division by zero - no losses means RSI = 100 (50 if also no gains)
    if avg_loss.iloc[-1] == 0:
        return 50.0 if avg_gain.iloc[-1] == 0 else 100.0
    rs = avg_gain.iloc[-1] / avg_loss.iloc[-1]
    return float(100.0 - (100.0 / (1.0 + rs)))


def calculate_macd(
    prices: List[float],
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9,
) -> Optional[Dict[str, float]]:
    """
    Calculate MACD (Moving Average Convergence Divergence).

    Args:
        prices: List of closing prices
        fast_period: Fast EMA period (default 12)
        slow_period: Slow EMA period (default 26)
        signal_period: Signal line EMA period (default 9)

    Returns:
        Dict with 'macd', 'signal', 'histogram' or None if insufficient data
    """
    if len(prices) < slow_period + signal_period:
        return None
    s = pd.Series(prices, dtype=float)
    ema_fast = s.ewm(span=fast_period, adjust=False).mean()
    ema_slow = s.ewm(span=slow_period, adjust=False).mean()
    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal_period, adjust=False).mean()
    histogram = macd_line - signal_line
    macd_val = macd_line.iloc[-1]
    signal_val = signal_line.iloc[-1]
    hist_val = histogram.iloc[-1]
    if pd.isna(macd_val) or pd.isna(signal_val) or pd.isna(hist_val):
        return None
    return {
        "macd": float(macd_val),
        "signal": float(signal_val),
        "histogram": float(hist_val),
    }


def calculate_bollinger_bands(
    prices: List[float],
    period: int = 20,
    std_dev: float = 2.0,
) -> Optional[Dict[str, float]]:
    """
    Calculate Bollinger Bands.

    Args:
        prices: List of closing prices
        period: Rolling window (default 20)
        std_dev: Standard deviation multiplier (default 2.0)

    Returns:
        Dict with 'upper', 'middle', 'lower' or None if insufficient data
    """
    if len(prices) < period:
        return None
    s = pd.Series(prices, dtype=float)
    rolling = s.rolling(window=period)
    middle = rolling.mean().iloc[-1]
    std = rolling.std().iloc[-1]
    if pd.isna(middle) or pd.isna(std):
        return None
    upper = middle + std_dev * std
    lower = middle - std_dev * std
    return {
        "upper": float(upper),
        "middle": float(middle),
        "lower": float(lower),
    }


def calculate_price_change(prices: List[float], periods: int = 1) -> Optional[float]:
    """
    Calculate price change percentage over N periods.

    Args:
        prices: List of prices
        periods: Number of periods to look back (default 1)

    Returns:
        Price change percentage or None if insufficient data
    """
    if len(prices) < periods + 1:
        return None
    current = prices[-1]
    previous = prices[-(periods + 1)]
    if previous == 0:
        return None
    return float(((current - previous) / previous) * 100)


def calculate_volatility(prices: List[float], period: int = 20) -> Optional[float]:
    """
    Calculate annualised price volatility (std of daily returns).

    Args:
        prices: List of closing prices
        period: Lookback period (default 20)

    Returns:
        Annualised volatility in % or None if insufficient data
    """
    if len(prices) < period + 1:
        return None
    s = pd.Series(prices, dtype=float)
    returns = s.pct_change().dropna().iloc[-period:]
    if len(returns) == 0:
        return None
    annualised = float(returns.std() * np.sqrt(252) * 100)
    return annualised


# ---------------------------------------------------------------------------
# Performance statistics (shared by backtest metrics and the Analysis page)
# ---------------------------------------------------------------------------


def sharpe_ratio(
    returns: "np.ndarray | pd.Series | List[float]",
    periods_per_year: float,
    risk_free_rate: float = 0.0,
) -> float:
    """
    Annualized Sharpe ratio of per-period simple returns.

    risk_free_rate is annual; it is spread evenly across periods_per_year.
    Returns 0.0 for fewer than 2 returns or zero volatility.
    """
    r = np.asarray(returns, dtype=float)
    r = r[~np.isnan(r)]
    if len(r) < 2:
        return 0.0
    std = float(np.std(r, ddof=1))
    if std == 0:
        return 0.0
    excess = r - risk_free_rate / periods_per_year
    return float(np.mean(excess) / std * np.sqrt(periods_per_year))


def max_drawdown_pct(values: "np.ndarray | pd.Series | List[float]") -> float:
    """Maximum peak-to-trough drawdown of an equity/price series, as a positive %."""
    v = np.asarray(values, dtype=float)
    if len(v) == 0:
        return 0.0
    running_max = np.maximum.accumulate(v)
    return float(np.max((running_max - v) / running_max * 100))

