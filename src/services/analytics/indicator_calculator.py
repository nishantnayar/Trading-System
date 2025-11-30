"""
Technical Indicator Calculation Service

Calculates technical indicators from market data and stores them in the database.
Uses only Yahoo Finance data (data_source = 'yahoo') for calculations.
"""

import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np
import pandas as pd
from loguru import logger
from sqlalchemy import and_, desc, select

from src.shared.database.base import db_transaction
from src.shared.database.models.market_data import (  # noqa: F401 (used in type hints)
    MarketData,
)

# Import calculation functions from streamlit_ui
# Note: In production, these should be moved to a shared location

# Add streamlit_ui to path to import calculation functions
streamlit_path = Path(__file__).parent.parent.parent.parent / "streamlit_ui"
sys.path.insert(0, str(streamlit_path))

from utils.technical_indicators import (
    calculate_bollinger_bands,
    calculate_ema,
    calculate_macd,
    calculate_price_change,
    calculate_rsi,
    calculate_sma,
    calculate_volatility,
)


class IndicatorCalculationService:
    """
    Service for calculating and storing technical indicators
    
    Calculates indicators from Yahoo Finance market data and stores
    results in both latest and time-series tables.
    """

    def __init__(self, data_source: str = "yahoo"):
        """
        Initialize the indicator calculation service
        
        Args:
            data_source: Data source to use for calculations (default: 'yahoo')
        """
        self.data_source = data_source

    async def get_market_data(
        self,
        symbol: str,
        end_date: Optional[date] = None,
        days_back: int = 300,
    ) -> List[Dict]:
        """
        Fetch market data for a symbol (Yahoo Finance only)
        
        Args:
            symbol: Stock symbol
            end_date: End date for data (default: today)
            days_back: Number of days to fetch (default: 300 for sufficient history)
            
        Returns:
            List of dictionaries with market data, sorted by timestamp (oldest first)
        """
        if end_date is None:
            end_date = date.today()
        
        start_date = end_date - timedelta(days=days_back)
        
        with db_transaction() as session:
            stmt = (
                select(MarketData)
                .where(
                    and_(
                        MarketData.symbol == symbol.upper(),
                        MarketData.data_source == self.data_source,
                        MarketData.timestamp >= datetime.combine(start_date, datetime.min.time()),
                        MarketData.timestamp <= datetime.combine(end_date, datetime.max.time()),
                    )
                )
                .order_by(MarketData.timestamp.asc())
            )
            result = session.execute(stmt)
            market_data_records = list(result.scalars().all())
            
            if not market_data_records:
                logger.warning(
                    f"No {self.data_source} market data found for {symbol} "
                    f"between {start_date} and {end_date}"
                )
                return []
            
            # Extract data while still in session context
            market_data = []
            for record in market_data_records:
                market_data.append({
                    'symbol': record.symbol,
                    'timestamp': record.timestamp,
                    'open': record.open,
                    'high': record.high,
                    'low': record.low,
                    'close': record.close,
                    'volume': record.volume,
                })
            
            return market_data

    def calculate_all_indicators(
        self,
        market_data: List[Dict],
        calculation_date: Optional[date] = None,
    ) -> Optional[Dict]:
        """
        Calculate all technical indicators from market data
        
        Args:
            market_data: List of market data dictionaries (must be sorted by timestamp)
            calculation_date: Date for which to calculate indicators (default: latest date)
            
        Returns:
            Dictionary with all indicator values, or None if insufficient data
        """
        if not market_data:
            logger.warning("No market data provided for indicator calculation")
            return None
        
        # Extract closing prices and volumes
        closing_prices = [float(md['close']) for md in market_data if md.get('close') is not None]
        volumes = [int(md['volume']) for md in market_data if md.get('volume') is not None]
        
        if not closing_prices:
            logger.warning("No closing prices found in market data")
            return None
        
        # Determine calculation date
        if calculation_date is None:
            calculation_date = market_data[-1]['timestamp'].date()
        
        # Get current price and volume
        current_price = closing_prices[-1] if closing_prices else None
        current_volume = volumes[-1] if volumes else None
        
        # Calculate Moving Averages
        sma_20 = calculate_sma(closing_prices, 20)
        sma_50 = calculate_sma(closing_prices, 50)
        sma_200 = calculate_sma(closing_prices, 200)
        ema_12 = calculate_ema(closing_prices, 12)
        ema_26 = calculate_ema(closing_prices, 26)
        ema_50 = calculate_ema(closing_prices, 50)
        
        # Calculate Momentum Indicators
        rsi = calculate_rsi(closing_prices, 14)
        rsi_14 = rsi  # Explicit 14-period RSI
        
        # Calculate MACD
        macd_result = calculate_macd(closing_prices, fast_period=12, slow_period=26, signal_period=9)
        macd_line = macd_result["macd"] if macd_result else None
        macd_signal = macd_result["signal"] if macd_result else None
        macd_histogram = macd_result["histogram"] if macd_result else None
        
        # Calculate Bollinger Bands
        bb_result = calculate_bollinger_bands(closing_prices, period=20, std_dev=2.0)
        bb_upper = bb_result["upper"] if bb_result else None
        bb_middle = bb_result["middle"] if bb_result else None
        bb_lower = bb_result["lower"] if bb_result else None
        
        # Calculate BB position (0 = lower band, 1 = upper band)
        bb_position = None
        bb_width = None
        if bb_result and current_price:
            if (bb_upper - bb_lower) > 0:
                bb_position = (current_price - bb_lower) / (bb_upper - bb_lower)
            else:
                bb_position = 0.5
            
            # Calculate band width as percentage
            if bb_middle and bb_middle > 0:
                bb_width = ((bb_upper - bb_lower) / bb_middle) * 100
        
        # Calculate Volatility & Price Changes
        volatility_20 = calculate_volatility(closing_prices, 20)
        price_change_1d = calculate_price_change(closing_prices, 1)
        price_change_5d = calculate_price_change(closing_prices, 5)
        price_change_30d = calculate_price_change(closing_prices, 30)
        
        # Calculate Volume Indicators
        avg_volume_20 = None
        if len(volumes) >= 20:
            avg_volume_20 = int(np.mean(volumes[-20:]))
        elif volumes:
            avg_volume_20 = int(np.mean(volumes))
        
        # Helper function to convert numpy types to Python native types
        def to_python_type(value):
            """Convert numpy types to Python native types for database storage"""
            if value is None:
                return None
            # Handle numpy scalar types
            if isinstance(value, np.generic):
                if isinstance(value, np.floating):
                    return float(value)
                elif isinstance(value, np.integer):
                    return int(value)
                elif isinstance(value, np.bool_):
                    return bool(value)
                else:
                    # Fallback: convert to Python type
                    return value.item() if hasattr(value, 'item') else float(value)
            # Handle numpy arrays
            if isinstance(value, np.ndarray):
                return value.tolist()
            # Already a Python native type
            return value
        
        # Build indicators dictionary (convert numpy types to Python native types)
        indicators = {
            "symbol": market_data[0]['symbol'],
            "calculated_date": calculation_date,
            # Moving Averages
            "sma_20": to_python_type(sma_20),
            "sma_50": to_python_type(sma_50),
            "sma_200": to_python_type(sma_200),
            "ema_12": to_python_type(ema_12),
            "ema_26": to_python_type(ema_26),
            "ema_50": to_python_type(ema_50),
            # Momentum
            "rsi": to_python_type(rsi),
            "rsi_14": to_python_type(rsi_14),
            # MACD
            "macd_line": to_python_type(macd_line),
            "macd_signal": to_python_type(macd_signal),
            "macd_histogram": to_python_type(macd_histogram),
            # Bollinger Bands
            "bb_upper": to_python_type(bb_upper),
            "bb_middle": to_python_type(bb_middle),
            "bb_lower": to_python_type(bb_lower),
            "bb_position": to_python_type(bb_position),
            "bb_width": to_python_type(bb_width),
            # Volatility & Price Changes
            "volatility_20": to_python_type(volatility_20),
            "price_change_1d": to_python_type(price_change_1d),
            "price_change_5d": to_python_type(price_change_5d),
            "price_change_30d": to_python_type(price_change_30d),
            # Volume
            "avg_volume_20": to_python_type(avg_volume_20),
            "current_volume": to_python_type(current_volume),
        }
        
        return indicators

    async def calculate_indicators_for_symbol(
        self,
        symbol: str,
        calculation_date: Optional[date] = None,
        days_back: int = 300,
    ) -> Optional[Dict]:
        """
        Calculate indicators for a symbol on a specific date
        
        Args:
            symbol: Stock symbol
            calculation_date: Date for which to calculate (default: today)
            days_back: Number of days of history to fetch (default: 300)
            
        Returns:
            Dictionary with indicator values, or None if calculation fails
        """
        if calculation_date is None:
            calculation_date = date.today()
        
        symbol = symbol.upper()
        logger.info(f"Calculating indicators for {symbol} on {calculation_date}")
        
        try:
            # Fetch market data (Yahoo only)
            market_data = await self.get_market_data(
                symbol=symbol,
                end_date=calculation_date,
                days_back=days_back,
            )
            
            if not market_data:
                logger.warning(f"No market data available for {symbol}")
                return None
            
            # Calculate indicators
            indicators = self.calculate_all_indicators(
                market_data=market_data,
                calculation_date=calculation_date,
            )
            
            if indicators:
                logger.info(
                    f"Successfully calculated indicators for {symbol}: "
                    f"RSI={indicators.get('rsi')}, SMA_20={indicators.get('sma_20')}"
                )
            
            return indicators
            
        except Exception as e:
            logger.error(f"Error calculating indicators for {symbol}: {e}", exc_info=True)
            return None

    async def batch_calculate_indicators(
        self,
        symbols: List[str],
        calculation_date: Optional[date] = None,
        days_back: int = 300,
    ) -> Dict[str, Optional[Dict]]:
        """
        Calculate indicators for multiple symbols
        
        Args:
            symbols: List of stock symbols
            calculation_date: Date for which to calculate (default: today)
            days_back: Number of days of history to fetch (default: 300)
            
        Returns:
            Dictionary mapping symbol to indicator values (None if calculation failed)
        """
        if calculation_date is None:
            calculation_date = date.today()
        
        results = {}
        
        logger.info(f"Batch calculating indicators for {len(symbols)} symbols on {calculation_date}")
        
        for symbol in symbols:
            indicators = await self.calculate_indicators_for_symbol(
                symbol=symbol,
                calculation_date=calculation_date,
                days_back=days_back,
            )
            results[symbol.upper()] = indicators
        
        successful = sum(1 for v in results.values() if v is not None)
        logger.info(
            f"Batch calculation complete: {successful}/{len(symbols)} symbols successful"
        )
        
        return results

