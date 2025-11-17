"""
Technical Indicator Calculations
RSI, MACD, Moving Averages, etc.
"""

from typing import Dict, List, Optional

import numpy as np
import pandas as pd


def calculate_sma(prices: List[float], period: int) -> Optional[float]:
    """
    Calculate Simple Moving Average
    
    Args:
        prices: List of prices
        period: Period for SMA
        
    Returns:
        SMA value or None if insufficient data
    """
    if len(prices) < period:
        return None
    return np.mean(prices[-period:])


def calculate_ema(prices: List[float], period: int, alpha: Optional[float] = None) -> Optional[float]:
    """
    Calculate Exponential Moving Average
    
    Args:
        prices: List of prices
        period: Period for EMA
        alpha: Smoothing factor (if None, calculated from period)
        
    Returns:
        EMA value or None if insufficient data
    """
    if len(prices) < period:
        return None
    
    if alpha is None:
        alpha = 2.0 / (period + 1)
    
    # Convert to pandas Series for easier calculation
    series = pd.Series(prices)
    ema = series.ewm(span=period, adjust=False).mean()
    return float(ema.iloc[-1])


def calculate_rsi(prices: List[float], period: int = 14) -> Optional[float]:
    """
    Calculate Relative Strength Index (RSI)
    
    Args:
        prices: List of closing prices
        period: RSI period (default: 14)
        
    Returns:
        RSI value (0-100) or None if insufficient data
    """
    if len(prices) < period + 1:
        return None
    
    # Calculate price changes
    deltas = np.diff(prices)
    
    # Separate gains and losses
    gains = np.where(deltas > 0, deltas, 0)
    losses = np.where(deltas < 0, -deltas, 0)
    
    # Calculate average gain and loss
    avg_gain = np.mean(gains[-period:])
    avg_loss = np.mean(losses[-period:])
    
    if avg_loss == 0:
        return 100.0
    
    # Calculate RS and RSI
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    
    return float(rsi)


def calculate_macd(
    prices: List[float], 
    fast_period: int = 12, 
    slow_period: int = 26, 
    signal_period: int = 9
) -> Optional[Dict[str, float]]:
    """
    Calculate MACD (Moving Average Convergence Divergence)
    
    Args:
        prices: List of closing prices
        fast_period: Fast EMA period (default: 12)
        slow_period: Slow EMA period (default: 26)
        signal_period: Signal line EMA period (default: 9)
        
    Returns:
        Dictionary with 'macd', 'signal', and 'histogram' values
    """
    if len(prices) < slow_period + signal_period:
        return None
    
    # Calculate EMAs
    fast_ema = calculate_ema(prices, fast_period)
    slow_ema = calculate_ema(prices, slow_period)
    
    if fast_ema is None or slow_ema is None:
        return None
    
    macd_line = fast_ema - slow_ema
    
    # For signal line, we need MACD values over time
    # Simplified: use current MACD as approximation
    # In production, you'd maintain a history of MACD values
    signal_line = macd_line  # Simplified
    
    histogram = macd_line - signal_line
    
    return {
        'macd': macd_line,
        'signal': signal_line,
        'histogram': histogram
    }


def calculate_bollinger_bands(
    prices: List[float], 
    period: int = 20, 
    std_dev: float = 2.0
) -> Optional[Dict[str, float]]:
    """
    Calculate Bollinger Bands
    
    Args:
        prices: List of closing prices
        period: Period for moving average (default: 20)
        std_dev: Standard deviation multiplier (default: 2.0)
        
    Returns:
        Dictionary with 'upper', 'middle', and 'lower' band values
    """
    if len(prices) < period:
        return None
    
    recent_prices = prices[-period:]
    middle = np.mean(recent_prices)
    std = np.std(recent_prices)
    
    return {
        'upper': float(middle + (std_dev * std)),
        'middle': float(middle),
        'lower': float(middle - (std_dev * std))
    }


def calculate_price_change(prices: List[float], periods: int = 1) -> Optional[float]:
    """
    Calculate price change percentage
    
    Args:
        prices: List of prices
        periods: Number of periods to look back (default: 1)
        
    Returns:
        Price change percentage or None if insufficient data
    """
    if len(prices) < periods + 1:
        return None
    
    current = prices[-1]
    previous = prices[-(periods + 1)]
    
    if previous == 0:
        return None
    
    change_pct = ((current - previous) / previous) * 100
    return float(change_pct)


def calculate_volatility(prices: List[float], period: int = 20) -> Optional[float]:
    """
    Calculate price volatility (standard deviation of returns)
    
    Args:
        prices: List of closing prices
        period: Period for calculation (default: 20)
        
    Returns:
        Volatility (annualized) or None if insufficient data
    """
    if len(prices) < period + 1:
        return None
    
    # Calculate returns
    returns = []
    for i in range(len(prices) - period, len(prices)):
        if i > 0 and prices[i-1] != 0:
            ret = (prices[i] - prices[i-1]) / prices[i-1]
            returns.append(ret)
    
    if not returns:
        return None
    
    # Calculate standard deviation and annualize (assuming daily data)
    std_dev = np.std(returns)
    annualized_vol = std_dev * np.sqrt(252) * 100  # Convert to percentage
    
    return float(annualized_vol)

