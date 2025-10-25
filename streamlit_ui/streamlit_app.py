"""
Basic Streamlit UI for Trading System
A simple hello world interface
"""

import streamlit as st

# Configure Streamlit page
st.set_page_config(
    page_title="Trading System",
    page_icon="📈",
    layout="wide"
)

def main():
    """Main Streamlit application"""
    
    st.title("📈 Trading System")
    st.write("Hello World! Welcome to the Trading System.")
    
    st.subheader("Basic Dashboard")
    st.write("This is a simple Streamlit interface for your trading system.")
    
    # Simple metrics
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Portfolio Value", "$100,000", "$1,000")
    
    with col2:
        st.metric("Total Return", "12.5%", "2.1%")
    
    with col3:
        st.metric("Active Positions", "5", "1")
    
    # Simple chart placeholder
    st.subheader("Portfolio Performance")
    st.line_chart([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])

if __name__ == "__main__":
    main()