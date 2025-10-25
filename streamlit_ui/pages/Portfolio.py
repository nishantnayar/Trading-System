"""
Portfolio page for Trading System
Portfolio tracking, performance metrics, and position management
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import os

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

def portfolio_page():
    """Portfolio page with dashboard overview"""
    st.title("📈 Portfolio - Trading Dashboard")
    
    st.write("Monitor your portfolio performance and market activity.")
    
    # Key metrics with session state
    st.subheader("Portfolio Overview")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("Portfolio Value", f"${st.session_state.portfolio_value:,.0f}", "$5,000")
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("Total Return", f"{st.session_state.total_return:.1f}%", "2.1%")
        st.markdown('</div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("Active Positions", st.session_state.active_positions, "2")
        st.markdown('</div>', unsafe_allow_html=True)
    with col4:
        st.markdown('<div class="metric-container">', unsafe_allow_html=True)
        st.metric("Win Rate", f"{st.session_state.win_rate}%", "5%")
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Performance chart
    st.subheader("Portfolio Performance")
    
    # Generate sample data
    dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='D')
    portfolio_values = 100000 + np.cumsum(np.random.normal(100, 50, len(dates)))
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=dates,
        y=portfolio_values,
        mode='lines',
        name='Portfolio Value',
        line=dict(color='#1f77b4', width=2)
    ))
    
    fig.update_layout(
        title="Portfolio Value Over Time",
        xaxis_title="Date",
        yaxis_title="Value ($)",
        height=400
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Portfolio allocation
    st.subheader("Portfolio Allocation")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Pie chart for allocation
        allocation_data = {
            'Sector': ['Technology', 'Healthcare', 'Finance', 'Energy', 'Consumer', 'Other'],
            'Percentage': [35, 20, 15, 12, 10, 8],
            'Value': [43750, 25000, 18750, 15000, 12500, 10000]
        }
        
        fig_pie = go.Figure(data=[go.Pie(
            labels=allocation_data['Sector'],
            values=allocation_data['Percentage'],
            hole=0.3
        )])
        
        fig_pie.update_layout(
            title="Portfolio Allocation by Sector",
            height=400
        )
        
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        # Top holdings table
        st.markdown("**Top Holdings**")
        
        holdings_data = {
            'Symbol': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA'],
            'Shares': [100, 50, 25, 30, 20],
            'Price': [150.25, 300.50, 2800.00, 3200.00, 250.75],
            'Value': [15025, 15025, 70000, 96000, 5015],
            'Weight': [12.0, 12.0, 56.0, 76.8, 4.0]
        }
        
        df_holdings = pd.DataFrame(holdings_data)
        df_holdings['Weight'] = df_holdings['Weight'].astype(str) + '%'
        st.dataframe(df_holdings, use_container_width=True)
    
    # Recent activity
    st.subheader("Recent Activity")
    st.markdown('<div class="card">', unsafe_allow_html=True)
    
    activity_data = {
        "Time": ["10:30 AM", "09:45 AM", "09:15 AM", "Yesterday"],
        "Action": ["Bought AAPL", "Sold MSFT", "Bought GOOGL", "Portfolio Update"],
        "Amount": ["$5,000", "$3,200", "$4,500", f"${st.session_state.portfolio_value:,.0f}"],
        "Status": ["✅ Completed", "✅ Completed", "✅ Completed", "✅ Completed"]
    }
    
    df_activity = pd.DataFrame(activity_data)
    st.dataframe(df_activity, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    # Risk metrics
    st.subheader("Risk Metrics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Sharpe Ratio", "1.25", "0.15")
    with col2:
        st.metric("Max Drawdown", "-8.5%", "-1.2%")
    with col3:
        st.metric("Volatility", "12.3%", "0.8%")
    
    # Session state controls
    st.subheader("Portfolio Controls")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Update Portfolio Value**")
        new_value = st.number_input(
            "New Portfolio Value",
            min_value=0,
            value=st.session_state.portfolio_value,
            step=1000
        )
        if st.button("Update Value"):
            st.session_state.portfolio_value = new_value
            st.success(f"Portfolio value updated to ${new_value:,.0f}")
            st.rerun()
    
    with col2:
        st.markdown("**Update Return Percentage**")
        new_return = st.number_input(
            "New Return Percentage",
            min_value=-100.0,
            max_value=1000.0,
            value=st.session_state.total_return,
            step=0.1
        )
        if st.button("Update Return"):
            st.session_state.total_return = new_return
            st.success(f"Return percentage updated to {new_return:.1f}%")
            st.rerun()

def main():
    """Main function for Portfolio page"""
    load_custom_css()
    portfolio_page()

if __name__ == "__main__":
    main()
