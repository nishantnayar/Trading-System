"""
Settings page for Trading System
User preferences, system configuration, and session state management
"""

import os
from datetime import datetime

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

def settings_page():
    """Settings page with user preferences and system configuration"""
    st.title("⚙️ Settings - System Configuration")
    
    st.write("Configure your trading system preferences and manage session state.")
    
    # User Preferences
    st.subheader("User Preferences")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Notification Settings**")
        st.session_state.user_preferences['notifications'] = st.checkbox(
            "Enable Notifications",
            value=st.session_state.user_preferences['notifications']
        )
        
        st.session_state.user_preferences['auto_refresh'] = st.checkbox(
            "Auto Refresh Data",
            value=st.session_state.user_preferences['auto_refresh']
        )
        
        refresh_interval = st.selectbox(
            "Refresh Interval",
            ["1 minute", "5 minutes", "15 minutes", "30 minutes", "1 hour"],
            index=1
        )
    
    with col2:
        st.markdown("**Display Settings**")
        theme = st.selectbox(
            "Theme",
            ["Light", "Dark", "Auto"],
            index=0
        )
        
        chart_style = st.selectbox(
            "Chart Style",
            ["Default", "Minimal", "Professional", "Colorful"],
            index=0
        )
        
        data_format = st.selectbox(
            "Data Format",
            ["US Format", "European Format", "Scientific"],
            index=0
        )
    
    # Portfolio Settings
    st.subheader("Portfolio Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Portfolio Configuration**")
        
        # Portfolio value update
        new_portfolio_value = st.number_input(
            "Portfolio Value ($)",
            min_value=0,
            value=st.session_state.portfolio_value,
            step=1000,
            help="Set your current portfolio value"
        )
        
        if st.button("Update Portfolio Value"):
            st.session_state.portfolio_value = new_portfolio_value
            st.success("Portfolio value updated!")
            st.rerun()
    
    with col2:
        st.markdown("**Performance Metrics**")
        
        # Return percentage update
        new_return = st.number_input(
            "Total Return (%)",
            min_value=-100.0,
            max_value=1000.0,
            value=st.session_state.total_return,
            step=0.1,
            help="Set your total return percentage"
        )
        
        if st.button("Update Return"):
            st.session_state.total_return = new_return
            st.success("Return percentage updated!")
            st.rerun()
    
    # Trading Settings
    st.subheader("Trading Settings")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Default Trading Parameters**")
        
        # Update selected symbol
        new_symbol = st.selectbox(
            "Default Symbol",
            ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "NFLX"],
            index=["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "NFLX"].index(st.session_state.selected_symbol)
        )
        
        if new_symbol != st.session_state.selected_symbol:
            st.session_state.selected_symbol = new_symbol
            st.success(f"Default symbol updated to {new_symbol}")
        
        # Update selected timeframe
        new_timeframe = st.selectbox(
            "Default Timeframe",
            ["1D", "1W", "1M", "3M", "6M", "1Y"],
            index=["1D", "1W", "1M", "3M", "6M", "1Y"].index(st.session_state.selected_timeframe)
        )
        
        if new_timeframe != st.session_state.selected_timeframe:
            st.session_state.selected_timeframe = new_timeframe
            st.success(f"Default timeframe updated to {new_timeframe}")
    
    with col2:
        st.markdown("**Risk Management**")
        
        max_position_size = st.slider(
            "Max Position Size (%)",
            min_value=1,
            max_value=50,
            value=10,
            help="Maximum percentage of portfolio for a single position"
        )
        
        stop_loss = st.slider(
            "Default Stop Loss (%)",
            min_value=1,
            max_value=20,
            value=5,
            help="Default stop loss percentage"
        )
        
        take_profit = st.slider(
            "Default Take Profit (%)",
            min_value=5,
            max_value=100,
            value=15,
            help="Default take profit percentage"
        )
    
    # Session State Management
    st.subheader("Session State Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Current Session State**")
        
        # Display current session state
        st.json({
            "portfolio_value": st.session_state.portfolio_value,
            "total_return": st.session_state.total_return,
            "active_positions": st.session_state.active_positions,
            "win_rate": st.session_state.win_rate,
            "selected_symbol": st.session_state.selected_symbol,
            "selected_timeframe": st.session_state.selected_timeframe,
            "user_preferences": st.session_state.user_preferences
        })
    
    with col2:
        st.markdown("**Session Actions**")
        
        if st.button("Reset to Defaults", type="secondary"):
            # Reset session state to defaults
            st.session_state.portfolio_value = 125000
            st.session_state.total_return = 15.2
            st.session_state.active_positions = 8
            st.session_state.win_rate = 68
            st.session_state.selected_symbol = "AAPL"
            st.session_state.selected_timeframe = "1M"
            st.session_state.user_preferences = {
                'theme': 'light',
                'notifications': True,
                'auto_refresh': False
            }
            st.success("Session state reset to defaults!")
            st.rerun()
        
        if st.button("Clear Session State", type="secondary"):
            # Clear all session state
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.success("Session state cleared!")
            st.rerun()
        
        if st.button("Export Session State"):
            # Export session state as JSON
            import json
            session_data = dict(st.session_state)
            st.download_button(
                label="Download Session Data",
                data=json.dumps(session_data, indent=2, default=str),
                file_name=f"session_state_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    
    # System Information
    st.subheader("System Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Application Details**")
        st.write(f"- **App Version**: 1.0.0")
        st.write(f"- **Python Version**: 3.9+")
        st.write(f"- **Streamlit Version**: 1.28.0")
        st.write(f"- **Last Updated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    with col2:
        st.markdown("**Session Details**")
        st.write(f"- **Session Start**: {st.session_state.trading_data['last_update'].strftime('%Y-%m-%d %H:%M:%S')}")
        st.write(f"- **Market Status**: {st.session_state.trading_data['market_status']}")
        st.write(f"- **User Preferences**: {len(st.session_state.user_preferences)} configured")
        st.write(f"- **Active Data**: {len(st.session_state.trading_data)} items")

def main():
    """Main function for Settings page"""
    load_custom_css()
    settings_page()

if __name__ == "__main__":
    main()
