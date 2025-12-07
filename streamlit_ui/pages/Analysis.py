"""
Analysis page for Trading System
Market data analysis, technical indicators, and trading opportunities
"""

import os
import sys
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from streamlit_lightweight_charts import Chart, renderLightweightCharts

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

# Import from utils package (which re-exports from utils.py)
from utils import (
    calculate_max_drawdown,
    calculate_returns,
    calculate_sharpe_ratio,
    calculate_volatility,
    convert_api_data_to_ohlc,
    create_candlestick_chart,
    create_candlestick_chart_with_overlays,
    create_lightweight_macd_chart,
    create_lightweight_ohlc_chart,
    create_lightweight_rsi_chart,
    create_lightweight_volume_chart,
    create_macd_chart,
    create_price_chart,
    create_rsi_chart,
    create_volume_chart,
    filter_ohlc_data_by_timeframe,
    format_currency,
    format_percentage,
    generate_ohlc_data,
    get_date_range,
    get_latest_technical_indicators,
    get_real_market_data,
    get_technical_indicators_from_db,
    get_timeframe_days,
    ohlc_data_to_dataframe,
    show_error_message,
    show_info_message,
    show_loading_spinner,
    validate_symbol,
)

# Note: Technical indicators are now fetched from database, not calculated on the fly
# The calculation functions are kept for fallback scenarios only

# Centralized Plotly configuration to avoid deprecation warnings
PLOTLY_CONFIG = {
    'displayModeBar': True,
    'displaylogo': False,
    'modeBarButtonsToRemove': ['pan2d', 'lasso2d', 'select2d', 'autoScale2d', 'resetScale2d'],
    'toImageButtonOptions': {
        'format': 'png',
        'filename': 'plot',
        'height': 500,
        'width': 700,
        'scale': 1
    }
}

# Chart height constant - all secondary charts (Volume, RSI, MACD) use the same height
CHART_HEIGHT_SECONDARY = 200

from api_client import get_api_client


@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_cached_sectors(_api_client):
    """Get cached sectors data"""
    return _api_client.get_sectors()


@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_cached_industries(_api_client, sector=None):
    """Get cached industries data"""
    return _api_client.get_industries(sector=sector)


@st.cache_data(ttl=3600)  # Cache for 1 hour
def get_cached_symbols(_api_client, sector=None, industry=None):
    """Get cached symbols data"""
    return _api_client.get_symbols_by_filter(sector=sector, industry=industry)


def load_custom_css():
    """Load custom CSS from file and configuration"""
    css_file = os.path.join(os.path.dirname(__file__), "..", "styles.css")
    try:
        with open(css_file, "r") as f:
            css_content = f.read()

        # Add CSS variables from configuration
        from css_config import generate_css_variables, get_theme_css
        css_variables = generate_css_variables()
        theme_css = get_theme_css()

        # Combine all CSS
        full_css = css_variables + css_content + theme_css
        st.markdown(f"<style>{full_css}</style>", unsafe_allow_html=True)

    except FileNotFoundError:
        st.warning("Custom CSS file not found. Using default styling.")
    except Exception as e:
        st.error(f"Error loading custom CSS: {e}")


def analysis_page():
    """Analysis page with market data and charts"""
    # Set page layout to wide for better use of screen space
    st.set_page_config(layout="wide", page_title="Analysis - Market Data & Charts")

    st.title("📊 Analysis - Market Data & Charts")

    st.write("Analyze market trends, technical indicators, and trading opportunities.")

    # Initialize session state if not exists
    if 'selected_symbol' not in st.session_state:
        st.session_state.selected_symbol = "AAPL"

    # Symbol selection with industry/sector filtering
    st.subheader("Symbol Analysis")
    # st.info("💡 **Linked Dropdowns**: Select a sector first, then choose from industries within that sector. Symbols will be filtered based on your selections.")

    # Initialize API client
    api_client = get_api_client()

    # Check API connection
    with show_loading_spinner("Connecting to API..."):
        health = api_client.health_check()
        if "error" in health:
            st.error("Failed to connect to API. Using fallback data.")
            # Fallback to hardcoded symbols
            available_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "NFLX"]
            industries = ["Technology", "Healthcare", "Finance"]
            sectors = ["Software", "Hardware", "Biotechnology"]
        else:
            # Debug: API connection success message (commented out, uncomment if needed for debugging)
            # st.success("Connected to API")
            pass
            # Load data from API using cached functions
            with show_loading_spinner("Loading company data..."):
                sectors = get_cached_sectors(api_client)
                industries = get_cached_industries(api_client)
                available_symbols_data = get_cached_symbols(api_client)

                if "error" in available_symbols_data:
                    st.warning("Failed to load symbols from API. Using fallback data.")
                    available_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "NFLX"]
                else:
                    available_symbols = [symbol.get('symbol', '') for symbol in available_symbols_data if
                                         symbol.get('symbol')]

    # Sector, Industry, and Symbol Selection (All in one line)
    col1, col2, col3 = st.columns(3)

    with col1:
        # Sector selection (FIRST)
        selected_sector = st.selectbox(
            "Select Sector",
            ["All Sectors"] + sectors,
            index=0,
            key="sector_selector"
        )

    with col2:
        # Industry selection (SECOND - filtered by sector)
        if selected_sector == "All Sectors":
            # Show all industries
            available_industries = industries
        else:
            # Filter industries by selected sector using cached function
            with show_loading_spinner("Loading industries for selected sector..."):
                if "error" not in health:
                    available_industries = get_cached_industries(api_client, sector=selected_sector)
                    if "error" in available_industries:
                        available_industries = industries  # Fallback
                else:
                    available_industries = industries  # Fallback

        selected_industry = st.selectbox(
            "Select Industry",
            ["All Industries"] + available_industries,
            index=0,
            key="industry_selector"
        )

    with col3:
        # Filter symbols based on sector and industry using cached functions
        with show_loading_spinner("Filtering symbols..."):
            if "error" not in health:
                # Use cached API filtering with sector-first approach
                if selected_sector == "All Sectors" and selected_industry == "All Industries":
                    # Show all symbols
                    filtered_data = get_cached_symbols(api_client)
                    filtered_symbols = [symbol.get('symbol', '') for symbol in filtered_data if symbol.get('symbol')]
                elif selected_sector != "All Sectors" and selected_industry == "All Industries":
                    # Filter by sector only
                    filtered_data = get_cached_symbols(api_client, sector=selected_sector)
                    filtered_symbols = [symbol.get('symbol', '') for symbol in filtered_data if symbol.get('symbol')]
                elif selected_sector == "All Sectors" and selected_industry != "All Industries":
                    # Filter by industry only (across all sectors)
                    filtered_data = get_cached_symbols(api_client, industry=selected_industry)
                    filtered_symbols = [symbol.get('symbol', '') for symbol in filtered_data if symbol.get('symbol')]
                else:
                    # Filter by both sector and industry
                    filtered_data = get_cached_symbols(api_client, sector=selected_sector, industry=selected_industry)
                    filtered_symbols = [symbol.get('symbol', '') for symbol in filtered_data if symbol.get('symbol')]
            else:
                # Use fallback data
                filtered_symbols = available_symbols

        # Ensure we have symbols to display
        if not filtered_symbols:
            st.warning("No symbols found for the selected criteria. Showing all available symbols.")
            filtered_symbols = available_symbols

        # Get current symbol from session state or default
        current_symbol = st.session_state.get('selected_symbol', 'AAPL')

        # Ensure current symbol is in the filtered list
        if current_symbol not in filtered_symbols:
            current_symbol = filtered_symbols[0] if filtered_symbols else "AAPL"
            st.session_state.selected_symbol = current_symbol

        # Create symbol selection with display names
        symbol_options = []
        symbol_values = []

        for symbol in filtered_symbols:
            # Get company info for display
            if "error" not in health:
                company_info = api_client.get_company_info(symbol)
                if "error" not in company_info and company_info:
                    company_name = company_info.get('name', symbol)
                    display_name = f"{symbol} - {company_name}"
                else:
                    display_name = symbol
            else:
                display_name = symbol

            symbol_options.append(display_name)
            symbol_values.append(symbol)

        # Symbol selectbox
        selected_display = st.selectbox(
            "Select Symbol",
            symbol_options,
            index=symbol_values.index(current_symbol) if current_symbol in symbol_values else 0
        )

        # Get the actual symbol value
        symbol = symbol_values[symbol_options.index(selected_display)]
        st.session_state.selected_symbol = symbol

    # Generate market data (needed for both tabs)
    data_source = "yahoo"

    # Try to get real market data from API
    with show_loading_spinner("Loading real market data from Yahoo Finance..."):
        ohlc_data = get_real_market_data(
            _api_client=api_client,
            symbol=symbol,
            data_source=data_source
        )

        # If no real data available, fall back to simulated data
        if not ohlc_data:
            st.warning("⚠️ No real market data available. Using simulated data.")
            base_price = 150 if symbol == "AAPL" else 200
            ohlc_data = generate_ohlc_data(
                symbol=symbol,
                days=365,
                base_price=base_price,
                volatility=2.0
            )
        else:
            # Debug: Market data loaded message (commented out, uncomment if needed for debugging)
            # st.success(f"✅ Loaded {len(ohlc_data)} real market data points from Yahoo Finance")
            pass

    # Create tabs for different views
    tab1, tab2 = st.tabs(["🏢 Company Info", "📈 Charts & Analysis"])

    with tab1:
        # Get detailed company info
        if "error" not in health:
            with show_loading_spinner("Loading detailed company information..."):
                company_info = api_client.get_company_info(symbol)
                if "error" not in company_info and company_info:
                    # Helper functions for safe formatting
                    def get_value(info: dict, *keys):
                        """Helper to read multiple possible key names"""
                        for k in keys:
                            v = info.get(k)
                            if v is not None and v != "":
                                return v
                        return None

                    def safe_text(value):
                        """Return value or N/A if empty"""
                        return value if (value is not None and value != "") else "N/A"

                    def safe_num(value):
                        """Format number with commas"""
                        return f"{int(value):,}" if isinstance(value, (int, float)) else safe_text(value)

                    def safe_currency(value):
                        """Format currency with B/M/K suffixes"""
                        if isinstance(value, (int, float)) and value is not None:
                            return format_currency(value)
                        return safe_text(value)

                    def safe_percent(value):
                        """Format percentage"""
                        return format_percentage(value) if isinstance(value, (int, float)) else safe_text(value)

                    def safe_date(ts):
                        """Format timestamp to date string"""
                        try:
                            if isinstance(ts, (int, float)) and ts > 0:
                                # Company info timestamps are often in seconds
                                return datetime.utcfromtimestamp(ts).strftime('%Y-%m-%d')
                            return safe_text(ts)
                        except Exception:
                            return "N/A"

                    # Company overview
                    st.subheader("Company Overview")
                    col1, col2 = st.columns(2)

                    with col1:
                        st.write(f"**Company Name:** {company_info.get('name', 'N/A')}")
                        st.write(f"**Symbol:** {symbol}")
                        st.write(f"**Industry:** {company_info.get('industry', 'N/A')}")
                        st.write(f"**Sector:** {company_info.get('sector', 'N/A')}")

                    with col2:
                        st.write(f"**Country:** {company_info.get('country', 'N/A')}")
                        st.write(f"**Website:** {company_info.get('website', 'N/A')}")
                        st.write(f"**Employees:** {get_value(company_info, 'employees', 'fullTimeEmployees') or 'N/A'}")
                        market_cap_value = get_value(company_info, 'market_cap', 'marketCap')
                        st.write(f"**Market Cap:** {safe_currency(market_cap_value)}")

                    # Company description
                    if company_info.get('longBusinessSummary') or company_info.get('description'):
                        st.subheader("Business Summary")
                        st.write(company_info.get('longBusinessSummary') or company_info.get('description'))

                    # Additional company attributes with safe formatting
                    st.subheader("Key Facts")
                    k1, k2, k3 = st.columns(3)
                    with k1:
                        st.write(f"**Exchange:** {safe_text(company_info.get('exchange'))}")
                        st.write(f"**Currency:** {safe_text(company_info.get('currency'))}")
                        st.write(f"**IPO Date:** {safe_date(company_info.get('ipoDate'))}")
                    with k2:
                        st.write(f"**Address:** {safe_text(get_value(company_info, 'address', 'address1'))}")
                        st.write(
                            f"**City/State:** {safe_text(company_info.get('city'))}, {safe_text(company_info.get('state'))}")
                        st.write(f"**Phone:** {safe_text(company_info.get('phone'))}")
                    with k3:
                        website = company_info.get('website')
                        if website:
                            st.markdown(f"**Website:** [{website}]({website})")
                        else:
                            st.write("**Website:** N/A")
                        st.write(f"**ZIP:** {safe_text(company_info.get('zip'))}")
                        st.write(f"**Country:** {safe_text(company_info.get('country'))}")

                else:
                    st.warning("Company information not available for this symbol.")
        else:
            st.warning("Unable to load company information due to API connection issues.")

    with tab2:
        st.subheader(f"Market Analysis for {symbol}")

        # Combined Timeframe Selection and Chart Settings
        st.subheader("Chart Configuration")
        
        # Timeframe selection and chart settings in columns
        config_col1, config_col2, config_col3, config_col4, config_col5 = st.columns(5)
        
        with config_col1:
            timeframe_options = ["1D", "1W", "1M", "3M", "6M", "1Y", "ALL"]
            timeframe_labels = {
                "1D": "1 Day",
                "1W": "1 Week",
                "1M": "1 Month",
                "3M": "3 Months",
                "6M": "6 Months",
                "1Y": "1 Year",
                "ALL": "All Available Data"
            }
            
            # Get default timeframe from session state or use "1M"
            default_timeframe = st.session_state.get('selected_timeframe', '1M')
            default_index = timeframe_options.index(default_timeframe) if default_timeframe in timeframe_options else 2
            
            selected_timeframe = st.selectbox(
                "Timeframe",
                options=timeframe_options,
                format_func=lambda x: timeframe_labels[x],
                index=default_index,
                key="timeframe_selector"
            )
            st.session_state.selected_timeframe = selected_timeframe
        
        with config_col2:
            show_sma = st.checkbox("Show SMA", value=False, key="show_sma")
            if show_sma:
                sma_period = st.number_input("SMA Period", min_value=5, max_value=200, value=20, step=5, key="sma_period")
            else:
                sma_period = 20
        
        with config_col3:
            show_ema = st.checkbox("Show EMA", value=False, key="show_ema")
            if show_ema:
                ema_period = st.number_input("EMA Period", min_value=5, max_value=200, value=50, step=5, key="ema_period")
            else:
                ema_period = 50
        
        with config_col4:
            show_bollinger = st.checkbox("Show Bollinger Bands", value=False, key="show_bollinger")
            if show_bollinger:
                bb_period = st.number_input("BB Period", min_value=5, max_value=200, value=20, step=5, key="bb_period")
                bb_std = st.number_input("BB Std Dev", min_value=1.0, max_value=3.0, value=2.0, step=0.1, key="bb_std")
            else:
                bb_period = 20
                bb_std = 2.0
        
        with config_col5:
            chart_height = st.number_input("Chart Height", min_value=300, max_value=800, value=500, step=50, key="chart_height")
        
        # Filter data by timeframe
        if ohlc_data:
            filtered_ohlc_data = filter_ohlc_data_by_timeframe(ohlc_data, selected_timeframe)
            
            if filtered_ohlc_data:
                # Debug: Data points info (commented out, uncomment if needed for debugging)
                # data_info = f"Showing {len(filtered_ohlc_data)} data points"
                # if selected_timeframe != "ALL":
                #     days = get_timeframe_days(selected_timeframe)
                #     data_info += f" for the last {days} days"
                # st.info(f"📊 {data_info}")
                pass
            else:
                # Only show warning if there's actually no data for the timeframe
                st.warning(f"⚠️ No data available for the selected timeframe ({timeframe_labels[selected_timeframe]}). Showing all available data.")
                filtered_ohlc_data = ohlc_data
        else:
            filtered_ohlc_data = ohlc_data

        # Create enhanced OHLC chart with overlays (using filtered data)
        st.subheader("Price Chart")
        fig = create_candlestick_chart_with_overlays(
            ohlc_data=filtered_ohlc_data,
            symbol=symbol,
            show_sma=show_sma,
            sma_period=sma_period,
            show_ema=show_ema,
            ema_period=ema_period,
            show_bollinger=show_bollinger,
            bb_period=bb_period,
            bb_std=bb_std,
            height=chart_height
        )
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

        # Also show volume chart below (using filtered data)
        st.subheader("Volume Chart")
        create_lightweight_volume_chart(
            ohlc_data=filtered_ohlc_data,
            symbol=symbol,
            height=CHART_HEIGHT_SECONDARY
        )

        # RSI Chart (full width, same height as Volume)
        st.subheader("RSI Chart")
        create_lightweight_rsi_chart(
            ohlc_data=filtered_ohlc_data,
            symbol=symbol,
            period=14,
            height=CHART_HEIGHT_SECONDARY
        )
        
        # MACD Chart (full width, same height as Volume)
        st.subheader("MACD Chart")
        create_lightweight_macd_chart(
            ohlc_data=filtered_ohlc_data,
            symbol=symbol,
            fast_period=12,
            slow_period=26,
            signal_period=9,
            height=CHART_HEIGHT_SECONDARY
        )

        # Analysis Metrics Section
        with st.expander("📊 Performance Metrics", expanded=True):
            st.subheader("Performance Analysis")
            
            # Get date range from filtered data
            if filtered_ohlc_data:
                timestamps = [item['time'] for item in filtered_ohlc_data]
                start_timestamp = min(timestamps)
                end_timestamp = max(timestamps)
                
                start_date = datetime.fromtimestamp(start_timestamp)
                end_date = datetime.fromtimestamp(end_timestamp)
                
                # Fetch technical indicators from database for the date range
                indicators = get_technical_indicators_from_db(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date
                )
                
                if indicators:
                    # Get latest values for metrics
                    latest_indicator = indicators[-1] if indicators else None
                    
                    # Calculate total return from price data (if needed, or use price_change_30d from DB)
                    df = ohlc_data_to_dataframe(filtered_ohlc_data)
                    if len(df) > 1:
                        total_return = ((df['close'].iloc[-1] / df['close'].iloc[0]) - 1) * 100
                    else:
                        total_return = 0
                    
                    # Get volatility from database (volatility_20 is annualized percentage)
                    annual_volatility = latest_indicator.get('volatility_20', 0) if latest_indicator else 0
                    
                    # For Sharpe ratio and max drawdown, we'd need to calculate from returns
                    # But for now, we can show N/A or calculate from price data if needed
                    # Note: These metrics might not be in the database, so we calculate them
                    if len(df) > 1:
                        returns = calculate_returns(df['close'])
                        sharpe_ratio = calculate_sharpe_ratio(returns, risk_free_rate=0.02) if len(returns) > 0 else 0.0
                        max_dd = calculate_max_drawdown(df['close']) * 100
                    else:
                        sharpe_ratio = 0.0
                        max_dd = 0.0
                else:
                    # Fallback to calculation if no database data
                    df = ohlc_data_to_dataframe(filtered_ohlc_data)
                    if len(df) > 1:
                        returns = calculate_returns(df['close'])
                        total_return = ((df['close'].iloc[-1] / df['close'].iloc[0]) - 1) * 100
                        volatility_pct = calculate_volatility(returns, window=min(30, len(returns)))
                        annual_volatility = volatility_pct.iloc[-1] if len(volatility_pct) > 0 and not pd.isna(volatility_pct.iloc[-1]) else returns.std() * np.sqrt(252) * 100
                        sharpe_ratio = calculate_sharpe_ratio(returns, risk_free_rate=0.02) if len(returns) > 0 else 0.0
                        max_dd = calculate_max_drawdown(df['close']) * 100
                    else:
                        total_return = 0
                        annual_volatility = 0
                        sharpe_ratio = 0.0
                        max_dd = 0.0
            else:
                # No filtered data
                total_return = 0
                annual_volatility = 0
                sharpe_ratio = 0.0
                max_dd = 0.0
            
            # Display metrics in columns
            if filtered_ohlc_data and len(filtered_ohlc_data) > 1:
                metrics_col1, metrics_col2, metrics_col3, metrics_col4 = st.columns(4)
                
                with metrics_col1:
                    st.metric(
                        "Total Return",
                        format_percentage(total_return / 100),
                        help="Total return over the selected timeframe"
                    )
                
                with metrics_col2:
                    st.metric(
                        "Annual Volatility",
                        f"{annual_volatility:.2f}%",
                        help="Annualized volatility (30-day rolling)"
                    )
                
                with metrics_col3:
                    st.metric(
                        "Sharpe Ratio",
                        f"{sharpe_ratio:.2f}",
                        help="Risk-adjusted return (higher is better)"
                    )
                
                with metrics_col4:
                    st.metric(
                        "Max Drawdown",
                        f"{max_dd:.2f}%",
                        help="Maximum peak-to-trough decline"
                    )
            else:
                st.warning("Insufficient data to calculate performance metrics. Need at least 2 data points.")

        # Technical indicators (using database data)
        with st.expander("📈 Technical Indicator Values", expanded=False):
            st.subheader("Current Indicator Values")

            # Fetch latest technical indicators from database
            latest_indicators = get_latest_technical_indicators(symbol)
            
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                if latest_indicators and latest_indicators.get('sma_20') is not None:
                    sma_20 = latest_indicators['sma_20']
                    st.metric("SMA 20", f"${sma_20:.2f}")
                else:
                    st.metric("SMA 20", "N/A", help="No data in database. Please ensure indicators are calculated.")

            with col2:
                if latest_indicators:
                    rsi = latest_indicators.get('rsi_14') or latest_indicators.get('rsi')
                    if rsi is not None:
                        # Color code RSI: overbought (>70), oversold (<30)
                        if rsi > 70:
                            status = "Overbought"
                            delta_color = "inverse"  # Red for overbought
                        elif rsi < 30:
                            status = "Oversold"
                            delta_color = "off"  # Green for oversold
                        else:
                            status = "Neutral"
                            delta_color = "normal"
                        st.metric("RSI (14)", f"{rsi:.1f}", delta=status, delta_color=delta_color)
                    else:
                        st.metric("RSI (14)", "N/A", help="No RSI data in database")
                else:
                    st.metric("RSI (14)", "N/A", help="No data in database")

            with col3:
                if latest_indicators:
                    macd_line = latest_indicators.get('macd_line')
                    macd_signal = latest_indicators.get('macd_signal')
                    macd_histogram = latest_indicators.get('macd_histogram')
                    if macd_line is not None and macd_signal is not None and macd_histogram is not None:
                        delta_color = "off" if macd_histogram > 0 else "inverse"
                        st.metric("MACD", f"{macd_line:.3f}", 
                                 delta=f"Signal: {macd_signal:.3f} | Hist: {macd_histogram:.3f}",
                                 delta_color=delta_color)
                    else:
                        st.metric("MACD", "N/A", help="No MACD data in database")
                else:
                    st.metric("MACD", "N/A", help="No data in database")

            with col4:
                if latest_indicators:
                    bb_position = latest_indicators.get('bb_position')
                    bb_upper = latest_indicators.get('bb_upper')
                    bb_lower = latest_indicators.get('bb_lower')
                    if bb_position is not None and bb_upper is not None and bb_lower is not None:
                        bb_position_pct = bb_position * 100
                        delta_color = "normal"
                        if bb_position > 0.8:
                            delta_color = "inverse"  # Red for overbought
                        elif bb_position < 0.2:
                            delta_color = "off"  # Green for oversold
                        st.metric("BB Position", f"{bb_position_pct:.1f}%",
                                 delta=f"Upper: ${bb_upper:.2f} | Lower: ${bb_lower:.2f}",
                                 delta_color=delta_color)
                    else:
                        st.metric("BB Position", "N/A", help="No Bollinger Bands data in database")
                else:
                    st.metric("BB Position", "N/A", help="No data in database")

    # Debug: Session state debugging (commented out, uncomment if needed for debugging)
    # with st.expander("🔧 Debug: Session State"):
    #     st.write("Current session state values:")
    #     st.json({
    #         "selected_symbol": st.session_state.selected_symbol
    #     })


def main():
    """Main function for Analysis page"""
    load_custom_css()
    analysis_page()


if __name__ == "__main__":
    main()
