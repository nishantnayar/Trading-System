"""
Common utilities for the Trading System Streamlit UI
"""

import os
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# ============================================================================
# FORMATTING UTILITIES
# ============================================================================

def format_currency(value: float, currency: str = "$", decimals: int = 2) -> str:
    """
    Format a number as currency
    
    Args:
        value: The numeric value to format
        currency: Currency symbol (default: "$")
        decimals: Number of decimal places (default: 2)
    
    Returns:
        Formatted currency string
    """
    if value is None or np.isnan(value):
        return f"{currency}0.00"
    
    if abs(value) >= 1_000_000_000:
        return f"{currency}{value/1_000_000_000:.{decimals}f}B"
    elif abs(value) >= 1_000_000:
        return f"{currency}{value/1_000_000:.{decimals}f}M"
    elif abs(value) >= 1_000:
        return f"{currency}{value/1_000:.{decimals}f}K"
    else:
        return f"{currency}{value:,.{decimals}f}"


def format_percentage(value: float, decimals: int = 2, show_sign: bool = True) -> str:
    """
    Format a number as percentage
    
    Args:
        value: The numeric value to format (as decimal, not percentage)
        decimals: Number of decimal places (default: 2)
        show_sign: Whether to show + sign for positive values
    
    Returns:
        Formatted percentage string
    """
    if value is None or np.isnan(value):
        return "0.00%"
    
    percentage = value * 100
    if show_sign and percentage > 0:
        return f"+{percentage:.{decimals}f}%"
    else:
        return f"{percentage:.{decimals}f}%"


def format_number(value: float, decimals: int = 2) -> str:
    """
    Format a number with appropriate scaling
    
    Args:
        value: The numeric value to format
        decimals: Number of decimal places
    
    Returns:
        Formatted number string
    """
    if value is None or np.isnan(value):
        return "0"
    
    if abs(value) >= 1_000_000_000:
        return f"{value/1_000_000_000:.{decimals}f}B"
    elif abs(value) >= 1_000_000:
        return f"{value/1_000_000:.{decimals}f}M"
    elif abs(value) >= 1_000:
        return f"{value/1_000:.{decimals}f}K"
    else:
        return f"{value:,.{decimals}f}"


def format_date(date: Union[str, datetime], format_str: str = "%Y-%m-%d") -> str:
    """
    Format a date string or datetime object
    
    Args:
        date: Date string or datetime object
        format_str: Output format string
    
    Returns:
        Formatted date string
    """
    if isinstance(date, str):
        try:
            date = datetime.fromisoformat(date.replace("Z", "+00:00"))
        except ValueError:
            return date
    
    return date.strftime(format_str)


# ============================================================================
# DATA PROCESSING UTILITIES
# ============================================================================

def get_timeframe_days(timeframe: str) -> int:
    """
    Convert timeframe string to days
    
    Args:
        timeframe: Timeframe string (1D, 1W, 1M, 3M, 6M, 1Y)
    
    Returns:
        Number of days
    """
    timeframe_map = {
        "1D": 1,
        "1W": 7,
        "1M": 30,
        "3M": 90,
        "6M": 180,
        "1Y": 365
    }
    return timeframe_map.get(timeframe, 30)


def get_date_range(timeframe: str, end_date: Optional[datetime] = None) -> Tuple[str, str]:
    """
    Get start and end dates for a timeframe
    
    Args:
        timeframe: Timeframe string
        end_date: End date (defaults to now)
    
    Returns:
        Tuple of (start_date, end_date) as ISO strings
    """
    if end_date is None:
        end_date = datetime.now()
    
    days = get_timeframe_days(timeframe)
    start_date = end_date - timedelta(days=days)
    
    return start_date.isoformat(), end_date.isoformat()


def calculate_returns(prices: pd.Series) -> pd.Series:
    """
    Calculate returns from price series
    
    Args:
        prices: Series of prices
    
    Returns:
        Series of returns
    """
    return prices.pct_change().dropna()


def calculate_volatility(returns: pd.Series, window: int = 30) -> pd.Series:
    """
    Calculate rolling volatility
    
    Args:
        returns: Series of returns
        window: Rolling window size
    
    Returns:
        Series of rolling volatility
    """
    return returns.rolling(window=window).std() * np.sqrt(252)


def calculate_sharpe_ratio(returns: pd.Series, risk_free_rate: float = 0.02) -> float:
    """
    Calculate Sharpe ratio
    
    Args:
        returns: Series of returns
        risk_free_rate: Risk-free rate (annual)
    
    Returns:
        Sharpe ratio
    """
    if len(returns) == 0:
        return 0.0
    
    excess_returns = returns - (risk_free_rate / 252)
    return excess_returns.mean() / returns.std() * np.sqrt(252)


def calculate_max_drawdown(prices: pd.Series) -> float:
    """
    Calculate maximum drawdown
    
    Args:
        prices: Series of prices
    
    Returns:
        Maximum drawdown as percentage
    """
    if len(prices) == 0:
        return 0.0
    
    peak = prices.expanding().max()
    drawdown = (prices - peak) / peak
    return drawdown.min()




# ============================================================================
# CHART UTILITIES
# ============================================================================

def create_price_chart(
    dates: pd.Series,
    prices: pd.Series,
    title: str = "Price Chart",
    symbol: str = "",
    color: str = "#2E8B57"
) -> go.Figure:
    """
    Create a price line chart
    
    Args:
        dates: Series of dates
        prices: Series of prices
        title: Chart title
        symbol: Symbol name
        color: Line color
    
    Returns:
        Plotly figure
    """
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=dates,
        y=prices,
        mode='lines',
        name=f'{symbol} Price' if symbol else 'Price',
        line=dict(color=color, width=2),
        hovertemplate='<b>%{fullData.name}</b><br>' +
                     'Date: %{x}<br>' +
                     'Price: $%{y:.2f}<br>' +
                     '<extra></extra>'
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Price ($)",
        height=400,
        hovermode='x unified',
        showlegend=True
    )
    
    return fig


def create_candlestick_chart(
    dates: pd.Series,
    open_prices: pd.Series,
    high_prices: pd.Series,
    low_prices: pd.Series,
    close_prices: pd.Series,
    title: str = "Candlestick Chart",
    symbol: str = ""
) -> go.Figure:
    """
    Create a candlestick chart
    
    Args:
        dates: Series of dates
        open_prices: Series of open prices
        high_prices: Series of high prices
        low_prices: Series of low prices
        close_prices: Series of close prices
        title: Chart title
        symbol: Symbol name
    
    Returns:
        Plotly figure
    """
    fig = go.Figure(data=go.Candlestick(
        x=dates,
        open=open_prices,
        high=high_prices,
        low=low_prices,
        close=close_prices,
        name=f'{symbol} OHLC' if symbol else 'OHLC'
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Price ($)",
        height=400,
        hovermode='x unified'
    )
    
    return fig


def create_volume_chart(
    dates: pd.Series,
    volumes: pd.Series,
    title: str = "Volume Chart",
    color: str = "lightblue"
) -> go.Figure:
    """
    Create a volume bar chart
    
    Args:
        dates: Series of dates
        volumes: Series of volumes
        title: Chart title
        color: Bar color
    
    Returns:
        Plotly figure
    """
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=dates,
        y=volumes,
        name='Volume',
        marker_color=color,
        hovertemplate='<b>Volume</b><br>' +
                     'Date: %{x}<br>' +
                     'Volume: %{y:,.0f}<br>' +
                     '<extra></extra>'
    ))
    
    fig.update_layout(
        title=title,
        xaxis_title="Date",
        yaxis_title="Volume",
        height=300,
        hovermode='x unified'
    )
    
    return fig


def create_pie_chart(
    labels: List[str],
    values: List[float],
    title: str = "Pie Chart",
    colors: Optional[List[str]] = None
) -> go.Figure:
    """
    Create a pie chart
    
    Args:
        labels: List of labels
        values: List of values
        title: Chart title
        colors: Optional list of colors
    
    Returns:
        Plotly figure
    """
    fig = go.Figure(data=[go.Pie(
        labels=labels,
        values=values,
        hovertemplate='<b>%{label}</b><br>' +
                     'Value: %{value:,.0f}<br>' +
                     'Percentage: %{percent}<br>' +
                     '<extra></extra>'
    )])
    
    if colors:
        fig.update_traces(marker=dict(colors=colors))
    
    fig.update_layout(
        title=title,
        height=400,
        showlegend=True
    )
    
    return fig


# ============================================================================
# SESSION STATE UTILITIES
# ============================================================================

def initialize_session_state() -> None:
    """
    Initialize default session state values
    """
    defaults = {
        'portfolio_value': 125000,
        'total_return': 15.2,
        'active_positions': 8,
        'win_rate': 68,
        'selected_symbol': "AAPL",
        'selected_timeframe': "1M",
        'user_preferences': {
            'theme': 'light',
            'notifications': True,
            'auto_refresh': False
        },
        'trading_data': {
            'last_update': datetime.now(),
            'market_status': 'open',
            'positions': [],
            'orders': []
        }
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def update_session_state(key: str, value: Any) -> None:
    """
    Update a session state variable
    
    Args:
        key: Session state key
        value: New value
    """
    st.session_state[key] = value


def get_session_state(key: str, default: Any = None) -> Any:
    """
    Get a session state variable with default
    
    Args:
        key: Session state key
        default: Default value if key doesn't exist
    
    Returns:
        Session state value or default
    """
    return st.session_state.get(key, default)


def reset_session_state() -> None:
    """
    Reset all session state to defaults
    """
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    initialize_session_state()


# ============================================================================
# UI UTILITIES
# ============================================================================

def load_custom_css() -> None:
    """
    Load custom CSS from file
    """
    css_file = os.path.join(os.path.dirname(__file__), "styles.css")
    try:
        with open(css_file, "r") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("Custom CSS file not found. Using default styling.")
    except Exception as e:
        st.error(f"Error loading custom CSS: {e}")


def create_metric_card(title: str, value: str, delta: str = None, delta_color: str = "normal") -> None:
    """
    Create a styled metric card
    
    Args:
        title: Metric title
        value: Metric value
        delta: Delta value (optional)
        delta_color: Delta color (normal, inverse, off)
    """
    st.markdown('<div class="metric-container">', unsafe_allow_html=True)
    st.metric(title, value, delta)
    st.markdown('</div>', unsafe_allow_html=True)


def create_info_card(title: str, content: str) -> None:
    """
    Create an info card
    
    Args:
        title: Card title
        content: Card content
    """
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.markdown(f"**{title}**")
    st.write(content)
    st.markdown('</div>', unsafe_allow_html=True)


def create_expandable_section(title: str, content: str, expanded: bool = False) -> None:
    """
    Create an expandable section
    
    Args:
        title: Section title
        content: Section content
        expanded: Whether to expand by default
    """
    with st.expander(title, expanded=expanded):
        st.write(content)


# ============================================================================
# DATA VALIDATION UTILITIES
# ============================================================================

def validate_symbol(symbol: str) -> bool:
    """
    Validate stock symbol format
    
    Args:
        symbol: Stock symbol to validate
    
    Returns:
        True if valid, False otherwise
    """
    if not symbol or not isinstance(symbol, str):
        return False
    
    # Basic validation: 1-5 characters, alphanumeric
    return len(symbol) <= 5 and symbol.isalnum()


def validate_date_range(start_date: str, end_date: str) -> bool:
    """
    Validate date range
    
    Args:
        start_date: Start date string
        end_date: End date string
    
    Returns:
        True if valid, False otherwise
    """
    try:
        start = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
        end = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
        return start < end
    except (ValueError, TypeError):
        return False


def validate_numeric_input(value: Any, min_val: float = None, max_val: float = None) -> bool:
    """
    Validate numeric input
    
    Args:
        value: Value to validate
        min_val: Minimum value (optional)
        max_val: Maximum value (optional)
    
    Returns:
        True if valid, False otherwise
    """
    try:
        num_val = float(value)
        if min_val is not None and num_val < min_val:
            return False
        if max_val is not None and num_val > max_val:
            return False
        return True
    except (ValueError, TypeError):
        return False


# ============================================================================
# ERROR HANDLING UTILITIES
# ============================================================================

def handle_api_error(error: Exception, context: str = "") -> None:
    """
    Handle API errors with user-friendly messages
    
    Args:
        error: Exception object
        context: Additional context for the error
    """
    error_msg = str(error)
    
    if "ConnectionError" in error_msg:
        st.error("❌ Cannot connect to API server. Please ensure the API is running on port 8001.")
    elif "TimeoutError" in error_msg:
        st.error("⏰ Request timed out. Please try again.")
    elif "HTTPError" in error_msg:
        st.error(f"🌐 API Error: {error_msg}")
    else:
        st.error(f"❌ Unexpected error: {error_msg}")
    
    if context:
        st.info(f"Context: {context}")


def show_loading_spinner(message: str = "Loading..."):
    """
    Context manager for showing loading spinner
    
    Args:
        message: Loading message
    """
    return st.spinner(message)


def show_success_message(message: str) -> None:
    """
    Show success message
    
    Args:
        message: Success message
    """
    st.success(f"✅ {message}")


def show_warning_message(message: str) -> None:
    """
    Show warning message
    
    Args:
        message: Warning message
    """
    st.warning(f"⚠️ {message}")


def show_error_message(message: str) -> None:
    """
    Show error message
    
    Args:
        message: Error message
    """
    st.error(f"❌ {message}")


def show_info_message(message: str) -> None:
    """
    Show info message
    
    Args:
        message: Info message
    """
    st.info(f"ℹ️ {message}")


# ============================================================================
# LIGHTWEIGHT CHARTS UTILITIES
# ============================================================================


def generate_ohlc_data(
    symbol: str, 
    days: int = 365, 
    base_price: float = 150.0,
    volatility: float = 2.0
) -> List[Dict[str, Any]]:
    """
    Generates realistic OHLC data for lightweight charts.
    
    Args:
        symbol: Stock symbol
        days: Number of days of data to generate
        base_price: Starting price
        volatility: Daily price volatility
        
    Returns:
        List of OHLC data dictionaries
    """
    from datetime import datetime, timedelta
    import numpy as np
    
    # Generate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    
    ohlc_data = []
    current_price = base_price
    
    for i, date in enumerate(dates):
        # Generate daily price movement
        daily_change = np.random.normal(0, volatility)
        open_price = current_price
        close_price = open_price + daily_change
        
        # Generate high and low prices
        high_price = max(open_price, close_price) + abs(np.random.normal(0, volatility * 0.5))
        low_price = min(open_price, close_price) - abs(np.random.normal(0, volatility * 0.5))
        
        # Generate volume (higher volume on larger price movements)
        volume_multiplier = 1 + abs(daily_change) / volatility
        volume = int(np.random.randint(1000000, 5000000) * volume_multiplier)
        
        ohlc_data.append({
            'time': int(date.timestamp()),
            'open': round(open_price, 2),
            'high': round(high_price, 2),
            'low': round(low_price, 2),
            'close': round(close_price, 2),
            'volume': volume
        })
        
        current_price = close_price
    
    return ohlc_data


def create_lightweight_ohlc_chart(
    ohlc_data: List[Dict[str, Any]], 
    symbol: str,
    height: int = 400
) -> None:
    """
    Creates a lightweight OHLC candlestick chart.
    
    Args:
        ohlc_data: List of OHLC data dictionaries
        symbol: Stock symbol for display
        height: Chart height in pixels
    """
    from streamlit_lightweight_charts import renderLightweightCharts, Chart
    
    # Prepare data for lightweight chart
    chart_data = {
        'chart': {
            'height': height
        },
        'series': [{
            'type': 'Candlestick',
            'data': ohlc_data,
            'options': {
                'upColor': '#26a69a',
                'downColor': '#ef5350',
                'borderVisible': False,
                'wickUpColor': '#26a69a',
                'wickDownColor': '#ef5350',
            }
        }]
    }
    
    # Render the lightweight chart
    renderLightweightCharts(
        [chart_data],
        key=f"ohlc_chart_{symbol}"
    )


def create_lightweight_volume_chart(
    ohlc_data: List[Dict[str, Any]], 
    symbol: str,
    height: int = 200
) -> None:
    """
    Creates a lightweight volume chart.
    
    Args:
        ohlc_data: List of OHLC data dictionaries
        symbol: Stock symbol for display
        height: Chart height in pixels
    """
    from streamlit_lightweight_charts import renderLightweightCharts, Chart
    
    # Prepare volume data
    volume_data = {
        'chart': {
            'height': height
        },
        'series': [{
            'type': 'Histogram',
            'data': [{'time': item['time'], 'value': item['volume']} for item in ohlc_data],
            'options': {
                'color': '#26a69a',
                'priceFormat': {
                    'type': 'volume',
                },
                'priceScaleId': '',
            }
        }]
    }
    
    # Render the lightweight chart
    renderLightweightCharts(
        [volume_data],
        key=f"volume_chart_{symbol}"
    )

                
def convert_api_data_to_ohlc(api_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Convert API market data to OHLC format for lightweight charts.
    
    Args:
        api_data: List of market data from API
        
    Returns:
        List of OHLC data dictionaries
    """
    ohlc_data = []
    
    for item in api_data:
        # Convert timestamp to Unix timestamp
        if isinstance(item['timestamp'], str):
            from datetime import datetime
            dt = datetime.fromisoformat(item['timestamp'].replace('Z', '+00:00'))
            timestamp = int(dt.timestamp())
        else:
            timestamp = int(item['timestamp'].timestamp())
        
        ohlc_data.append({
            'time': timestamp,
            'open': float(item['open']) if item['open'] else 0.0,
            'high': float(item['high']) if item['high'] else 0.0,
            'low': float(item['low']) if item['low'] else 0.0,
            'close': float(item['close']) if item['close'] else 0.0,
            'volume': int(item['volume']) if item['volume'] else 0
        })
    
    return ohlc_data


def get_real_market_data(
    _api_client,
    symbol: str,
    data_source: str = "yahoo"
) -> List[Dict[str, Any]]:
    """
    Fetch real market data from API and convert to OHLC format.
    
    Args:
        api_client: API client instance
        symbol: Stock symbol
        days: Number of days to fetch
        data_source: Data source (yahoo, polygon, alpaca)
        
    Returns:
        List of OHLC data dictionaries
    """
    try:
        # Fetch data from API (no date filtering to get all available data)
        api_data = _api_client.get_market_data(
            symbol=symbol,
            data_source=data_source
        )
        
        if "error" in api_data:
            return []
        
        # Convert to OHLC format
        ohlc_data = convert_api_data_to_ohlc(api_data)
        
        # Sort by time (oldest first)
        ohlc_data.sort(key=lambda x: x['time'])
        
        return ohlc_data
        
    except Exception as e:
        print(f"Error fetching real market data: {e}")
        return []
