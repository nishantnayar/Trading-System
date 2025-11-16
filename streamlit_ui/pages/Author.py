"""
Author page for Trading System
System information, team details, and contact information
"""

import os
import sys

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from utils import (
    format_currency,
    format_number,
    format_percentage,
    get_session_state,
    show_info_message,
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

def author_page():
    """Author page with system information"""
    st.title("👨‍💻 Author - About the Trading System")
    
    st.write("Learn about the Trading System, its features, and the development team.")
    
    # Initialize session state if not exists
    if 'portfolio_value' not in st.session_state:
        st.session_state.portfolio_value = 125000
    if 'total_return' not in st.session_state:
        st.session_state.total_return = 15.2
    if 'active_positions' not in st.session_state:
        st.session_state.active_positions = 8
    if 'win_rate' not in st.session_state:
        st.session_state.win_rate = 68
    if 'selected_symbol' not in st.session_state:
        st.session_state.selected_symbol = "AAPL"
    if 'selected_timeframe' not in st.session_state:
        st.session_state.selected_timeframe = "1M"
    if 'user_preferences' not in st.session_state:
        st.session_state.user_preferences = {
            'theme': 'light',
            'notifications': True,
            'auto_refresh': False
        }
    
    # System overview
    st.subheader("System Overview")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Trading System Features:**
        - 📈 Real-time market data
        - 🔍 Technical analysis tools
        - 📊 Portfolio tracking
        - ⚡ Automated trading strategies
        - 🛡️ Risk management
        - 📱 Modern web interface
        """)
    
    with col2:
        st.markdown("""
        **Technology Stack:**
        - Python 3.9+
        - FastAPI backend
        - Streamlit frontend
        - PostgreSQL database
        - Redis caching
        - Docker deployment
        """)
    
    # Architecture diagram
    st.subheader("System Architecture")
    
    # Create a simple architecture diagram
    fig = go.Figure()
    
    # Add boxes for different components
    components = [
        {"name": "Streamlit UI", "x": 1, "y": 3, "color": "lightblue"},
        {"name": "FastAPI Backend", "x": 2, "y": 3, "color": "lightgreen"},
        {"name": "PostgreSQL", "x": 3, "y": 2, "color": "lightcoral"},
        {"name": "Redis Cache", "x": 3, "y": 4, "color": "lightyellow"},
        {"name": "Trading APIs", "x": 2, "y": 1, "color": "lightpink"}
    ]
    
    for comp in components:
        fig.add_trace(go.Scatter(
            x=[comp["x"]],
            y=[comp["y"]],
            mode="markers+text",
            marker=dict(size=100, color=comp["color"]),
            text=[comp["name"]],
            textposition="middle center",
            showlegend=False
        ))
    
    fig.update_layout(
        title="System Architecture",
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        height=400,
        template='plotly_white'
    )
    
    st.plotly_chart(fig, width='stretch', config=PLOTLY_CONFIG)
    
    # Development team
    st.subheader("Development Team")
    
    team_data = {
        "Role": ["Lead Developer", "Data Scientist", "DevOps Engineer", "UI/UX Designer"],
        "Name": ["Alex Johnson", "Sarah Chen", "Mike Rodriguez", "Emma Wilson"],
        "Expertise": ["Python, FastAPI", "ML, Analytics", "Docker, AWS", "Streamlit, Design"],
        "Experience": ["5+ years", "4+ years", "6+ years", "3+ years"]
    }
    
    df_team = pd.DataFrame(team_data)
    st.dataframe(df_team, width='stretch')
    
    # Contact information
    st.subheader("Contact & Support")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Contact Information:**
        - 📧 Email: support@tradingsystem.com
        - 📱 Phone: +1 (555) 123-4567
        - 🌐 Website: www.tradingsystem.com
        - 📍 Office: New York, NY
        """)
    
    with col2:
        st.markdown("""
        **Support Hours:**
        - Monday - Friday: 9:00 AM - 6:00 PM EST
        - Saturday: 10:00 AM - 2:00 PM EST
        - Sunday: Closed
        - Emergency: 24/7 for critical issues
        """)
    
    # Version information
    st.subheader("System Information")
    
    info_data = {
        "Component": ["Trading System", "FastAPI Backend", "Streamlit UI", "Database"],
        "Version": ["v1.0.0", "v0.100.0", "v1.28.0", "PostgreSQL 15"],
        "Last Updated": ["2024-01-15", "2024-01-10", "2024-01-12", "2024-01-08"],
        "Status": ["✅ Active", "✅ Active", "✅ Active", "✅ Active"]
    }
    
    df_info = pd.DataFrame(info_data)
    st.dataframe(df_info, width='stretch')
    
    # Session state information
    st.subheader("Current Session Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Portfolio Status:**")
        st.write(f"- Portfolio Value: ${st.session_state.portfolio_value:,.0f}")
        st.write(f"- Total Return: {st.session_state.total_return:.1f}%")
        st.write(f"- Active Positions: {st.session_state.active_positions}")
        st.write(f"- Win Rate: {st.session_state.win_rate}%")
    
    with col2:
        st.markdown("**User Preferences:**")
        st.write(f"- Notifications: {'✅' if st.session_state.user_preferences['notifications'] else '❌'}")
        st.write(f"- Auto Refresh: {'✅' if st.session_state.user_preferences['auto_refresh'] else '❌'}")
        st.write(f"- Selected Symbol: {st.session_state.selected_symbol}")
        st.write(f"- Selected Timeframe: {st.session_state.selected_timeframe}")

def main():
    """Main function for Author page"""
    load_custom_css()
    author_page()

if __name__ == "__main__":
    main()
