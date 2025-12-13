"""
Stock Screener Page with Local LLM Integration
Filter stocks by technical and fundamental criteria with AI-powered analysis
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import streamlit as st
from loguru import logger
from st_aggrid import AgGrid, GridOptionsBuilder

# Add parent directory to path
parent_dir = os.path.dirname(os.path.dirname(__file__))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from streamlit_ui.api_client import get_api_client
from streamlit_ui.services.llm_service import LLMService, get_llm_service
from streamlit_ui.utils import (
    format_currency,
    format_number,
    format_percentage,
    get_real_market_data,
    show_error_message,
    show_info_message,
    show_loading_spinner,
)

# Note: Technical indicators are now fetched from database, not calculated on the fly

# Initialize session state
if 'screener_results' not in st.session_state:
    st.session_state.screener_results = []
if 'screener_query' not in st.session_state:
    st.session_state.screener_query = ""


def load_custom_css():
    """Load custom CSS"""
    css_file = os.path.join(os.path.dirname(__file__), "..", "styles.css")
    try:
        with open(css_file, "r") as f:
            css_content = f.read()
        from streamlit_ui.css_config import generate_css_variables, get_theme_css
        css_variables = generate_css_variables()
        theme_css = get_theme_css()
        full_css = css_variables + css_content + theme_css
        st.markdown(f"<style>{full_css}</style>", unsafe_allow_html=True)
    except Exception as e:
        st.warning(f"Error loading CSS: {e}")


def get_indicators_for_symbol_from_db(
    symbol: str,
    ohlc_data: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Get all technical indicators for a symbol from database"""
    from utils import get_latest_technical_indicators
    
    if not ohlc_data:
        return {}
    
    # Get latest indicators from database
    latest_indicators = get_latest_technical_indicators(symbol)
    
    if not latest_indicators:
        # Fallback: return basic info if no database data
        closing_prices = [item['close'] for item in ohlc_data]
        volumes = [item.get('volume', 0) for item in ohlc_data]
        return {
            'symbol': symbol,
            'current_price': closing_prices[-1] if closing_prices else None,
            'current_volume': volumes[-1] if volumes else 0,
        }
    
    # Extract current price and volume from OHLC data
    closing_prices = [item['close'] for item in ohlc_data]
    volumes = [item.get('volume', 0) for item in ohlc_data]
    
    indicators = {
        'symbol': symbol,
        'current_price': closing_prices[-1] if closing_prices else None,
        'sma_20': latest_indicators.get('sma_20'),
        'sma_50': latest_indicators.get('sma_50'),
        'rsi': latest_indicators.get('rsi_14') or latest_indicators.get('rsi'),
        'price_change_1d': latest_indicators.get('price_change_1d'),
        'price_change_5d': latest_indicators.get('price_change_5d'),
        'price_change_30d': latest_indicators.get('price_change_30d'),
        'volatility': latest_indicators.get('volatility_20'),
        'macd': latest_indicators.get('macd_line'),
        'macd_signal': latest_indicators.get('macd_signal'),
        'macd_histogram': latest_indicators.get('macd_histogram'),
        'bb_position': latest_indicators.get('bb_position'),
        'avg_volume': latest_indicators.get('avg_volume_20'),
        'current_volume': volumes[-1] if volumes else latest_indicators.get('current_volume'),
    }
    
    return indicators


def screen_stocks(
    api_client,
    llm_service: Optional[LLMService],
    criteria: Dict[str, Any],
    symbols: List[str],
    use_llm: bool = False
) -> List[Dict[str, Any]]:
    """
    Screen stocks based on criteria
    
    Args:
        api_client: API client instance
        llm_service: LLM service instance
        criteria: Screening criteria dictionary
        symbols: List of symbols to screen
        use_llm: Whether to use LLM for analysis
        
    Returns:
        List of screened stock results
    """
    results = []
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    total_symbols = len(symbols)
    
    for idx, symbol in enumerate(symbols):
        try:
            status_text.text(f"Processing {symbol} ({idx + 1}/{total_symbols})...")
            progress_bar.progress((idx + 1) / total_symbols)
            
            # Get market data
            ohlc_data = get_real_market_data(
                _api_client=api_client,
                symbol=symbol,
                data_source="yahoo"
            )
            
            if not ohlc_data:
                # Log skipped symbols for debugging
                logger.debug(f"Skipping {symbol}: No market data available")
                continue
            
            # Get indicators from database
            indicators = get_indicators_for_symbol_from_db(symbol, ohlc_data)
            
            # Get company info
            company_info = api_client.get_company_info(symbol)
            if "error" not in company_info:
                indicators.update({
                    'name': company_info.get('name', symbol),
                    'sector': company_info.get('sector'),
                    'industry': company_info.get('industry'),
                    'market_cap': company_info.get('marketCap') or company_info.get('market_cap'),
                })
            
            # Apply filters
            # If no criteria specified, show all stocks
            if not criteria or len(criteria) == 0:
                matches = True
            else:
                matches = True
                
                # Sector filter (case-insensitive partial match)
                if criteria.get('sector'):
                    sector_criteria = criteria['sector'].lower()
                    stock_sector = (indicators.get('sector') or '').lower()
                    # Check for exact match or if criteria is contained in sector name
                    if stock_sector and sector_criteria not in stock_sector and stock_sector != sector_criteria:
                        # Also check common variations
                        sector_variations = {
                            'finance': ['financial', 'finance', 'banking', 'bank'],
                            'technology': ['tech', 'technology', 'software'],
                            'healthcare': ['health', 'healthcare', 'medical'],
                        }
                        matched = False
                        for key, variations in sector_variations.items():
                            if sector_criteria in key or key in sector_criteria:
                                if any(var in stock_sector for var in variations):
                                    matched = True
                                    break
                        if not matched:
                            matches = False
            
            # Industry filter
            if matches and criteria.get('industry') and indicators.get('industry'):
                industry_criteria = criteria['industry'].lower()
                stock_industry = indicators.get('industry', '').lower()
                if industry_criteria not in stock_industry and stock_industry != industry_criteria:
                    matches = False
            
            # Price filters
            if matches and indicators.get('current_price'):
                if criteria.get('min_price') and indicators['current_price'] < criteria['min_price']:
                    matches = False
                if criteria.get('max_price') and indicators['current_price'] > criteria['max_price']:
                    matches = False
            
            # Volume filter
            if matches and criteria.get('min_volume'):
                if indicators.get('avg_volume', 0) < criteria['min_volume']:
                    matches = False
            
            # Market cap filter
            if matches and criteria.get('min_market_cap'):
                market_cap_b = indicators.get('market_cap', 0) / 1_000_000_000 if indicators.get('market_cap') else 0
                if market_cap_b < criteria['min_market_cap']:
                    matches = False
            
            # RSI filters (only apply if not looking for "highest" or "lowest")
            if matches and indicators.get('rsi') is not None:
                # Check if query is about "highest" or "lowest" - if so, don't filter, just include
                query_lower = st.session_state.get('screener_query', '').lower()
                is_highest_lowest_query = 'highest' in query_lower or 'lowest' in query_lower or 'top' in query_lower
                
                if not is_highest_lowest_query:
                    if criteria.get('rsi_min') and indicators['rsi'] < criteria['rsi_min']:
                        matches = False
                    if criteria.get('rsi_max') and indicators['rsi'] > criteria['rsi_max']:
                        matches = False
            
            # Price change filters
            if matches:
                if criteria.get('min_price_change_pct'):
                    change = indicators.get('price_change_30d', 0)
                    if change is not None and change < criteria['min_price_change_pct']:
                        matches = False
                if criteria.get('max_price_change_pct'):
                    change = indicators.get('price_change_30d', 0)
                    if change is not None and change > criteria['max_price_change_pct']:
                        matches = False
            
            # Keyword filter - check symbol, name, sector, and industry
            # Ignore sorting-related keywords (highest, lowest, top, etc.)
            if matches and criteria.get('keywords'):
                # Filter out sorting/ranking keywords
                sorting_keywords = ['highest', 'lowest', 'top', 'bottom', 'best', 'worst', 'rsi', 'price', 'volume']
                relevant_keywords = [
                    kw for kw in criteria['keywords'] 
                    if not any(sort_kw in kw.lower() for sort_kw in sorting_keywords)
                ]
                
                # If no relevant keywords after filtering, skip keyword matching
                if not relevant_keywords:
                    # No actual search keywords, just sorting terms - allow all
                    pass
                else:
                    keyword_matched = False
                    search_text = f"{symbol} {indicators.get('name', '')} {indicators.get('sector', '')} {indicators.get('industry', '')}".lower()
                    
                    for kw in relevant_keywords:
                        kw_lower = kw.lower()
                        # Check if keyword matches symbol, name, sector, or industry
                        if kw_lower in search_text:
                            keyword_matched = True
                            break
                        # Also check sector variations
                        sector_variations = {
                            'finance': ['financial', 'finance', 'banking', 'bank', 'financial services'],
                            'technology': ['tech', 'technology', 'software', 'information technology'],
                            'healthcare': ['health', 'healthcare', 'medical', 'pharmaceutical'],
                            'energy': ['energy', 'oil', 'gas', 'petroleum'],
                            'consumer': ['consumer', 'retail', 'consumer goods'],
                        }
                        for key, variations in sector_variations.items():
                            if kw_lower in key or key in kw_lower:
                                stock_sector = (indicators.get('sector') or '').lower()
                                if any(var in stock_sector for var in variations):
                                    keyword_matched = True
                                    break
                        if keyword_matched:
                            break
                    
                    if not keyword_matched:
                        matches = False
            
            if matches:
                results.append(indicators)
                logger.debug(f"Match found: {symbol} - {indicators.get('name', 'N/A')}")
            else:
                logger.debug(f"No match: {symbol} - Criteria: {criteria}")
                
        except Exception as e:
            logger.error(f"Error processing {symbol}: {e}")
            st.warning(f"Error processing {symbol}: {e}")
            continue
    
    progress_bar.empty()
    status_text.empty()
    
    # Sort results if query mentions "highest", "lowest", or "top"
    query_lower = st.session_state.get('screener_query', '').lower()
    if 'highest' in query_lower or 'top' in query_lower:
        # Sort by RSI descending (highest first)
        results.sort(key=lambda x: x.get('rsi', 0) if x.get('rsi') is not None else -1, reverse=True)
        # Limit to top 10 if many results
        if len(results) > 10:
            results = results[:10]
            logger.info(f"Limited results to top 10 for 'highest' query")
    elif 'lowest' in query_lower:
        # Sort by RSI ascending (lowest first)
        results.sort(key=lambda x: x.get('rsi', 100) if x.get('rsi') is not None else 100)
        # Limit to top 10 if many results
        if len(results) > 10:
            results = results[:10]
            logger.info(f"Limited results to top 10 for 'lowest' query")
    
    return results


def screener_page():
    """Main screener page"""
    st.set_page_config(layout="wide", page_title="Stock Screener - AI Powered")
    
    load_custom_css()
    
    st.title("🔍 Stock Screener with AI Analysis")
    st.write("Filter stocks using natural language queries or traditional filters, powered by local LLM")
    
    # Initialize API client
    api_client = get_api_client()
    
    # Check API connection
    with show_loading_spinner("Connecting to API..."):
        health = api_client.health_check()
        if "error" in health:
            st.error("Failed to connect to API. Please check your API connection.")
            return
        # Debug: API connection success message (commented out, uncomment if needed for debugging)
        # st.success("✅ Connected to API")
        pass
    
    # Initialize LLM service
    llm_service = None
    try:
        with show_loading_spinner("Initializing LLM service..."):
            llm_service = get_llm_service(model="phi3")
            st.success("✅ LLM service ready")
    except Exception as e:
        st.warning(f"⚠️ LLM service not available: {e}. You can still use traditional filters.")
    
    # Create tabs
    tab1, tab2 = st.tabs(["🤖 Natural Language Query", "⚙️ Traditional Filters"])
    
    with tab1:
        st.subheader("Ask in Natural Language")
        st.write("Example: 'Find tech stocks with RSI below 30 and high volume'")
        
        query = st.text_input(
            "Enter your screening query:",
            value=st.session_state.screener_query,
            placeholder="e.g., Find undervalued tech stocks with RSI < 30"
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            search_button = st.button("🔍 Search", type="primary", width='stretch')
        
        if search_button and query:
            st.session_state.screener_query = query
            
            if llm_service:
                with show_loading_spinner("Interpreting your query with AI..."):
                    try:
                        criteria = llm_service.interpret_screening_query(query)
                        st.json(criteria)  # Show parsed criteria
                    except Exception as e:
                        st.error(f"Error interpreting query: {e}")
                        criteria = {}
            else:
                st.warning("LLM service not available. Please use Traditional Filters tab.")
                criteria = {}
            
            # Get symbols to screen (always do this, even if criteria is empty)
            with show_loading_spinner("Loading symbols..."):
                try:
                    all_symbols_data = api_client.get_all_symbols()
                    if "error" not in all_symbols_data and all_symbols_data:
                        symbols = [s.get('symbol', '') for s in all_symbols_data if s.get('symbol')]
                        if not symbols:
                            st.warning("No symbols found in database. Using fallback symbols.")
                            symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "NFLX"]
                    else:
                        st.warning("API returned error or empty data. Using fallback symbols.")
                        symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "NFLX"]
                    
                    st.info(f"📊 Screening {len(symbols[:50])} symbols...")
                except Exception as e:
                    st.error(f"Error loading symbols: {e}")
                    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "NFLX"]
            
            if symbols:
                # Screen stocks (even with empty criteria, show all stocks)
                with show_loading_spinner("Screening stocks..."):
                    try:
                        results = screen_stocks(api_client, llm_service, criteria, symbols[:50])  # Limit to 50 for demo
                        st.session_state.screener_results = results
                    except Exception as e:
                        st.error(f"Error during screening: {e}")
                        import traceback
                        st.code(traceback.format_exc())
                        results = []
                
                # Show results
                if results:
                    st.success(f"✅ Found {len(results)} matching stocks")
                else:
                    st.warning("⚠️ No stocks matched your criteria.")
                    st.info("💡 **Troubleshooting tips:**")
                    st.markdown("""
                    - Try using **Traditional Filters** tab for more control
                    - Check if market data is available for symbols
                    - Relax your filter criteria (e.g., remove RSI filters)
                    - Verify API connection is working
                    """)
            else:
                st.error("No symbols available to screen. Please check your API connection.")
    
    with tab2:
        st.subheader("Traditional Filter Options")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write("**Sector & Industry**")
            sectors = api_client.get_sectors() if "error" not in health else []
            selected_sector = st.selectbox("Sector", ["All"] + sectors)
            
            industries = []
            if selected_sector != "All":
                industries = api_client.get_industries(sector=selected_sector) if "error" not in health else []
            else:
                industries = api_client.get_industries() if "error" not in health else []
            
            selected_industry = st.selectbox("Industry", ["All"] + industries)
        
        with col2:
            st.write("**Price & Volume**")
            min_price = st.number_input("Min Price ($)", min_value=0.0, value=0.0, step=1.0)
            max_price = st.number_input("Max Price ($)", min_value=0.0, value=0.0, step=1.0)
            min_volume = st.number_input("Min Avg Volume", min_value=0, value=0, step=10000)
            min_market_cap = st.number_input("Min Market Cap (B)", min_value=0.0, value=0.0, step=0.1)
        
        with col3:
            st.write("**Technical Indicators**")
            rsi_min = st.slider("RSI Min", 0, 100, 0)
            rsi_max = st.slider("RSI Max", 0, 100, 100)
            min_price_change = st.number_input("Min Price Change % (30d)", min_value=-100.0, value=0.0, step=1.0)
            max_price_change = st.number_input("Max Price Change % (30d)", min_value=-100.0, value=100.0, step=1.0)
        
        filter_button = st.button("🔍 Apply Filters", type="primary", width='stretch')
        
        if filter_button:
            # Build criteria
            criteria = {}
            if selected_sector != "All":
                criteria['sector'] = selected_sector
            if selected_industry != "All":
                criteria['industry'] = selected_industry
            if min_price > 0:
                criteria['min_price'] = min_price
            if max_price > 0:
                criteria['max_price'] = max_price
            if min_volume > 0:
                criteria['min_volume'] = min_volume
            if min_market_cap > 0:
                criteria['min_market_cap'] = min_market_cap
            if rsi_min > 0:
                criteria['rsi_min'] = rsi_min
            if rsi_max < 100:
                criteria['rsi_max'] = rsi_max
            if min_price_change != 0:
                criteria['min_price_change_pct'] = min_price_change
            if max_price_change != 100:
                criteria['max_price_change_pct'] = max_price_change
            
            # Get symbols
            with show_loading_spinner("Loading symbols..."):
                if selected_sector != "All" or selected_industry != "All":
                    symbols_data = api_client.get_symbols_by_filter(
                        sector=selected_sector if selected_sector != "All" else None,
                        industry=selected_industry if selected_industry != "All" else None
                    )
                else:
                    symbols_data = api_client.get_all_symbols()
                
                if "error" not in symbols_data:
                    symbols = [s.get('symbol', '') for s in symbols_data if s.get('symbol')]
                else:
                    symbols = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "NVDA", "META", "NFLX"]
            
            if symbols:
                # Screen stocks
                with show_loading_spinner("Screening stocks..."):
                    try:
                        results = screen_stocks(api_client, llm_service, criteria, symbols[:50])
                        st.session_state.screener_results = results
                    except Exception as e:
                        st.error(f"Error during screening: {e}")
                        import traceback
                        st.code(traceback.format_exc())
                        results = []
                
                # Show results
                if results:
                    st.success(f"✅ Found {len(results)} matching stocks")
                else:
                    st.warning("⚠️ No stocks matched your criteria.")
                    st.info("💡 **Troubleshooting tips:**")
                    st.markdown("""
                    - Try relaxing your filter criteria
                    - Check if market data is available
                    - Verify symbols have sufficient historical data
                    - Try screening without filters first
                    """)
            else:
                st.error("No symbols available to screen.")
    
    # Display Results
    if st.session_state.screener_results:
        st.markdown("---")
        st.subheader("📊 Screening Results")
        
        results = st.session_state.screener_results
        
        # LLM Analysis
        if llm_service and st.session_state.screener_query:
            with st.expander("🤖 AI Analysis", expanded=True):
                with show_loading_spinner("Generating AI analysis..."):
                    analysis = llm_service.analyze_screened_results(
                        results, 
                        query=st.session_state.screener_query
                    )
                    st.write(analysis)
        
        # Results Table
        if results:
            # Prepare DataFrame
            df_data = []
            for stock in results:
                df_data.append({
                    'Symbol': stock.get('symbol', 'N/A'),
                    'Name': stock.get('name', 'N/A'),
                    'Sector': stock.get('sector', 'N/A'),
                    'Industry': stock.get('industry', 'N/A'),
                    'Price': f"${stock.get('current_price', 0):.2f}" if stock.get('current_price') else 'N/A',
                    'RSI': f"{stock.get('rsi', 0):.1f}" if stock.get('rsi') is not None else 'N/A',
                    'Price Chg (30d)': format_percentage(stock.get('price_change_30d', 0) / 100) if stock.get('price_change_30d') is not None else 'N/A',
                    'Volatility': f"{stock.get('volatility', 0):.1f}%" if stock.get('volatility') else 'N/A',
                    'Avg Volume': format_number(stock.get('avg_volume', 0)) if stock.get('avg_volume') else 'N/A',
                    'Market Cap': format_currency(stock.get('market_cap', 0)) if stock.get('market_cap') else 'N/A',
                })
            
            df = pd.DataFrame(df_data)
            
            # Configure AgGrid
            gb = GridOptionsBuilder.from_dataframe(df)
            gb.configure_pagination(paginationAutoPageSize=True)
            gb.configure_side_bar()
            gb.configure_default_column(groupable=True, sortable=True, filterable=True)
            grid_options = gb.build()
            
            AgGrid(df, gridOptions=grid_options, theme='streamlit', height=400)
            
            # Export button
            csv = df.to_csv(index=False)
            st.download_button(
                label="📥 Download Results as CSV",
                data=csv,
                file_name=f"stock_screener_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )


def main():
    """Main function"""
    screener_page()


if __name__ == "__main__":
    main()

