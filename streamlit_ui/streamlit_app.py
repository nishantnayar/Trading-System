"""
Main Streamlit application for Trading System
Handles session state initialization and global configuration
"""

import streamlit as st
import os
from datetime import datetime

# Configure Streamlit page
st.set_page_config(
    page_title="Trading System",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_custom_css():
    """Load custom CSS from file and configuration"""
    css_file = os.path.join(os.path.dirname(__file__), "styles.css")
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

def initialize_session_state():
    """Initialize session state variables"""
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
    
    if 'trading_data' not in st.session_state:
        st.session_state.trading_data = {
            'last_update': datetime.now(),
            'market_status': 'open',
            'positions': [],
            'orders': []
        }

def create_sidebar():
    """Create sidebar with system status and navigation info"""
    st.sidebar.title("📈 Trading System")
    st.sidebar.markdown("---")
    
    # System status
    st.sidebar.subheader("System Status")
    st.sidebar.metric("Status", "🟢 Online")
    st.sidebar.metric("Last Update", st.session_state.trading_data['last_update'].strftime("%H:%M:%S"))
    
    # Portfolio summary
    st.sidebar.subheader("Portfolio Summary")
    st.sidebar.metric("Value", f"${st.session_state.portfolio_value:,.0f}")
    st.sidebar.metric("Return", f"{st.session_state.total_return:.1f}%")
    st.sidebar.metric("Positions", st.session_state.active_positions)
    
    st.sidebar.markdown("---")
    
    # User preferences
    st.sidebar.subheader("Preferences")
    st.session_state.user_preferences['notifications'] = st.sidebar.checkbox(
        "Notifications", 
        value=st.session_state.user_preferences['notifications']
    )
    st.session_state.user_preferences['auto_refresh'] = st.sidebar.checkbox(
        "Auto Refresh", 
        value=st.session_state.user_preferences['auto_refresh']
    )

def main():
    """Main Streamlit application entry point"""
    
    # Initialize session state
    initialize_session_state()
    
    # Load custom CSS
    load_custom_css()
    
    # Create sidebar
    create_sidebar()
    
    # Welcome message
    st.title("🏠 Trading System Dashboard")
    st.write("Welcome to the Trading System. Use the navigation menu to explore different sections.")
    
    # Quick stats
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
    
    # Navigation instructions
    st.info("💡 **Navigation**: Use the pages menu in the sidebar to navigate between different sections of the application.")

if __name__ == "__main__":
    main()