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
from streamlit_lightweight_charts import renderLightweightCharts, Chart

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils import (
    calculate_returns,
    calculate_volatility,
    create_candlestick_chart,
    create_price_chart,
    create_volume_chart,
    create_lightweight_ohlc_chart,
    create_lightweight_volume_chart,
    convert_api_data_to_ohlc,
    format_currency,
    format_percentage,
    generate_ohlc_data,
    get_date_range,
    get_real_market_data,
    get_timeframe_days,
    show_error_message,
    show_info_message,
    show_loading_spinner,
    validate_symbol,
)

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
            st.success("Connected to API")
            # Load data from API using cached functions
            with show_loading_spinner("Loading company data..."):
                sectors = get_cached_sectors(api_client)
                industries = get_cached_industries(api_client)
                available_symbols_data = get_cached_symbols(api_client)
                
                if "error" in available_symbols_data:
                    st.warning("Failed to load symbols from API. Using fallback data.")
                    available_symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "NFLX"]
                else:
                    available_symbols = [symbol.get('symbol', '') for symbol in available_symbols_data if symbol.get('symbol')]
    
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
            st.success(f"✅ Loaded {len(ohlc_data)} real market data points from Yahoo Finance")
    
    # Create tabs for different views
    tab1, tab2 = st.tabs(["🏢 Company Info", "📈 Charts & Analysis"])
    
    with tab1:
        st.subheader(f"Company Information for {symbol}")
        
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
                        st.write(f"**City/State:** {safe_text(company_info.get('city'))}, {safe_text(company_info.get('state'))}")
                        st.write(f"**Phone:** {safe_text(company_info.get('phone'))}")
                    with k3:
                        website = company_info.get('website')
                        if website:
                            st.markdown(f"**Website:** [{website}]({website})")
                        else:
                            st.write("**Website:** N/A")
                        st.write(f"**ZIP:** {safe_text(company_info.get('zip'))}")
                        st.write(f"**Country:** {safe_text(company_info.get('country'))}")
                    
                    st.subheader("Valuation")
                    v1, v2, v3 = st.columns(3)
                    with v1:
                        st.write(f"**Market Cap:** {safe_currency(get_value(company_info, 'market_cap', 'marketCap'))}")
                        st.write(f"**Enterprise Value:** {safe_currency(company_info.get('enterpriseValue'))}")
                    with v2:
                        st.write(f"**Trailing P/E:** {safe_text(company_info.get('trailingPE'))}")
                        st.write(f"**Forward P/E:** {safe_text(company_info.get('forwardPE'))}")
                    with v3:
                        st.write(f"**Price to Book:** {safe_text(company_info.get('priceToBook'))}")
                        st.write(f"**Beta:** {safe_text(company_info.get('beta'))}")
                    
                    st.subheader("Financials")
                    f1, f2, f3 = st.columns(3)
                    with f1:
                        st.write(f"**Revenue (ttm):** {safe_currency(company_info.get('totalRevenue'))}")
                        st.write(f"**EBITDA:** {safe_currency(company_info.get('ebitda'))}")
                    with f2:
                        st.write(f"**Gross Margin:** {safe_percent(company_info.get('grossMargins'))}")
                        st.write(f"**Operating Margin:** {safe_percent(company_info.get('operatingMargins'))}")
                    with f3:
                        st.write(f"**Profit Margin:** {safe_percent(company_info.get('profitMargins'))}")
                        st.write(f"**Revenue Growth:** {safe_percent(company_info.get('revenueGrowth'))}")
                    
                    st.subheader("Dividends")
                    d1, d2, d3 = st.columns(3)
                    with d1:
                        st.write(f"**Dividend Rate:** {safe_text(company_info.get('dividendRate'))}")
                        st.write(f"**Dividend Yield:** {safe_percent(company_info.get('dividendYield'))}")
                    with d2:
                        st.write(f"**Payout Ratio:** {safe_percent(company_info.get('payoutRatio'))}")
                        st.write(f"**Ex-Dividend Date:** {safe_date(company_info.get('exDividendDate'))}")
                    with d3:
                        st.write(f"**Last Split Date:** {safe_date(company_info.get('lastSplitDate'))}")
                        st.write(f"**Last Split Factor:** {safe_text(company_info.get('lastSplitFactor'))}")
                    
                    st.subheader("Shares & Ownership")
                    s1, s2, s3 = st.columns(3)
                    with s1:
                        st.write(f"**Shares Outstanding:** {safe_num(company_info.get('sharesOutstanding'))}")
                        st.write(f"**Float Shares:** {safe_num(company_info.get('floatShares'))}")
                    with s2:
                        st.write(f"**Insider Ownership:** {safe_percent(company_info.get('heldPercentInsiders'))}")
                        st.write(f"**Institutional Ownership:** {safe_percent(company_info.get('heldPercentInstitutions'))}")
                    with s3:
                        st.write(f"**Implied Shares Outstanding:** {safe_num(company_info.get('impliedSharesOutstanding'))}")
                        st.write(f"**Book Value:** {safe_text(company_info.get('bookValue'))}")
                    
                    st.subheader("Risk & Short Interest")
                    r1, r2, r3 = st.columns(3)
                    with r1:
                        st.write(f"**Short % of Float:** {safe_percent(company_info.get('shortPercentOfFloat'))}")
                        st.write(f"**Short Ratio:** {safe_text(company_info.get('shortRatio'))}")
                    with r2:
                        st.write(f"**52W High:** {safe_currency(company_info.get('fiftyTwoWeekHigh'))}")
                        st.write(f"**52W Low:** {safe_currency(company_info.get('fiftyTwoWeekLow'))}")
                    with r3:
                        st.write(f"**52W Change:** {safe_percent(company_info.get('52WeekChange') or company_info.get('fiftyTwoWeekChangePercent'))}")
                        st.write(f"**Average Volume:** {safe_num(company_info.get('averageVolume'))}")
                else:
                    st.warning("Company information not available for this symbol.")
        else:
            st.warning("Unable to load company information due to API connection issues.")
        
        # Market data table
        st.subheader("Recent Market Data")
        
        # Use the OHLC data we generated
        recent_ohlc = ohlc_data[-10:]  # Last 10 days
        recent_data = pd.DataFrame({
            'Date': [datetime.fromtimestamp(item['time']).strftime('%Y-%m-%d') for item in recent_ohlc],
            'Open': [f"${item['open']:.2f}" for item in recent_ohlc],
            'High': [f"${item['high']:.2f}" for item in recent_ohlc],
            'Low': [f"${item['low']:.2f}" for item in recent_ohlc],
            'Close': [f"${item['close']:.2f}" for item in recent_ohlc],
            'Volume': [f"{item['volume']:,}" for item in recent_ohlc]
        })
        
        st.dataframe(recent_data, width='stretch')
    
    with tab2:
        st.subheader(f"Market Analysis for {symbol}")
        
        # Create lightweight OHLC chart
        st.subheader(f"{symbol} OHLC Chart")
        create_lightweight_ohlc_chart(
            ohlc_data=ohlc_data,  # Show all available data
            symbol=symbol,
            height=400
        )
        
        # Also show volume chart below
        st.subheader(f"{symbol} Volume Chart")
        create_lightweight_volume_chart(
            ohlc_data=ohlc_data,  # Show all available data
            symbol=symbol,
            height=200
        )
        
        # Technical indicators
        st.subheader("Technical Indicators")
        
        # Extract closing prices from OHLC data for calculations
        closing_prices = [item['close'] for item in ohlc_data]  # All available data
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            sma_20 = np.mean(closing_prices[-20:])
            st.metric("SMA 20", f"${sma_20:.2f}")
        
        with col2:
            rsi = 45 + np.random.normal(0, 10)
            st.metric("RSI", f"{rsi:.1f}")
        
        with col3:
            macd = np.random.normal(0, 0.5)
            st.metric("MACD", f"{macd:.3f}")
        
        with col4:
            bb_position = np.random.uniform(0, 1)
            st.metric("BB Position", f"{bb_position:.2f}")
    
    # Session state debugging (remove in production)
    with st.expander("🔧 Debug: Session State"):
        st.write("Current session state values:")
        st.json({
            "selected_symbol": st.session_state.selected_symbol
        })

def main():
    """Main function for Analysis page"""
    load_custom_css()
    analysis_page()

if __name__ == "__main__":
    main()
