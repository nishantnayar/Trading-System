"""
Analysis page for Trading System
Market data analysis, technical indicators, and trading opportunities
"""

import os
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

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
    st.title("📊 Analysis - Market Data & Charts")
    
    st.write("Analyze market trends, technical indicators, and trading opportunities.")
    
    # Symbol selection with session state
    st.subheader("Symbol Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Update session state when symbol changes
        symbol = st.selectbox(
            "Select Symbol",
            ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "NFLX"],
            index=["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "NFLX"].index(st.session_state.selected_symbol)
        )
        st.session_state.selected_symbol = symbol
    
    with col2:
        # Update session state when timeframe changes
        timeframe = st.selectbox(
            "Timeframe",
            ["1D", "1W", "1M", "3M", "6M", "1Y"],
            index=["1D", "1W", "1M", "3M", "6M", "1Y"].index(st.session_state.selected_timeframe)
        )
        st.session_state.selected_timeframe = timeframe
    
    # Generate sample market data
    st.subheader(f"Market Analysis for {symbol}")
    
    # Sample price data
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
    base_price = 150 if symbol == "AAPL" else 200
    prices = base_price + np.cumsum(np.random.normal(0, 2, len(dates)))
    volumes = np.random.randint(1000000, 5000000, len(dates))
    
    # Price chart
    fig_price = go.Figure()
    fig_price.add_trace(go.Scatter(
        x=dates,
        y=prices,
        mode='lines',
        name=f'{symbol} Price',
        line=dict(color='#2E8B57', width=2)
    ))
    
    fig_price.update_layout(
        title=f"{symbol} Price Chart",
        xaxis_title="Date",
        yaxis_title="Price ($)",
        height=400
    )
    
    st.plotly_chart(fig_price, use_container_width=True)
    
    # Technical indicators
    st.subheader("Technical Indicators")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        sma_20 = np.mean(prices[-20:])
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
    
    # Volume chart
    st.subheader("Volume Analysis")
    
    fig_volume = go.Figure()
    fig_volume.add_trace(go.Bar(
        x=dates[-30:],  # Last 30 days
        y=volumes[-30:],
        name='Volume',
        marker_color='lightblue'
    ))
    
    fig_volume.update_layout(
        title=f"{symbol} Volume Chart (Last 30 Days)",
        xaxis_title="Date",
        yaxis_title="Volume",
        height=300
    )
    
    st.plotly_chart(fig_volume, use_container_width=True)
    
    # Market data table
    st.subheader("Recent Market Data")
    
    recent_data = pd.DataFrame({
        'Date': dates[-10:],
        'Open': prices[-10:] + np.random.normal(0, 1, 10),
        'High': prices[-10:] + np.random.uniform(0, 3, 10),
        'Low': prices[-10:] - np.random.uniform(0, 3, 10),
        'Close': prices[-10:],
        'Volume': volumes[-10:]
    })
    
    st.dataframe(recent_data, use_container_width=True)
    
    # Session state debugging (remove in production)
    with st.expander("🔧 Debug: Session State"):
        st.write("Current session state values:")
        st.json({
            "selected_symbol": st.session_state.selected_symbol,
            "selected_timeframe": st.session_state.selected_timeframe,
            "portfolio_value": st.session_state.portfolio_value,
            "user_preferences": st.session_state.user_preferences
        })

def main():
    """Main function for Analysis page"""
    load_custom_css()
    analysis_page()

if __name__ == "__main__":
    main()
