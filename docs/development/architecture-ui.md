# Trading System UI Architecture

> **Status**: ✅ Fully Implemented (v1.0.0)

## Design Philosophy

### Core Principles
1. **Interactive Dashboard**: Streamlit-based multipage interface with session state management
2. **Analysis-Focused**: Emphasis on monitoring, analysis, and configuration rather than trading execution
3. **Real-time Updates**: Streamlit's reactive framework provides live updates
4. **Trading Interface**: ✅ Account management, position tracking, and order management (paper trading)
5. **Simple & Maintainable**: Streamlit + Plotly + Custom CSS for professional, responsive interface

### Technology Stack
- **Backend**: FastAPI (Python web framework)
- **Frontend**: Streamlit (multipage application framework)
- **Charts**: Plotly for interactive financial visualizations
- **Styling**: Custom CSS for professional appearance
- **Database**: PostgreSQL (structured logs, trading data, system state)
- **AI Integration**: Ollama LLM for natural language stock screening

## UI Components

The Streamlit UI provides a multipage interface with the following pages:

### 1. Portfolio Page ✅ Implemented
- Real-time portfolio tracking and performance metrics
- Portfolio value, daily change, and performance indicators
- Interactive charts showing portfolio performance over time
- Asset allocation visualization
- Recent trades and transactions
- Risk metrics and exposure

### 2. Analysis Page ✅ Implemented
- Symbol selection with session state persistence
- Interactive Plotly charts with candlesticks and volume
- Technical indicators display (SMA, EMA, RSI, MACD, Bollinger Bands)
- Volume analysis visualization
- Timeframe selection (1D, 1W, 1M, 3M, 6M, 1Y)

### 3. Stock Screener Page ✅ Implemented
- AI-powered natural language queries (with Ollama integration)
- Traditional filters (sector, price, volume, RSI, market cap)
- Technical indicators filtering
- Interactive results table with sorting and filtering
- CSV export functionality
- AI analysis of screening results

### 4. Author Page ✅ Implemented
- System information and team details
- Technology stack overview
- Architecture information
- Session state debugging information

### 5. Settings Page ✅ Implemented
- User preferences and interface settings
- Portfolio configuration options
- Session state management (reset, clear, export)
- System configuration display

## Backend API Architecture

The FastAPI backend provides REST API endpoints that power the Streamlit frontend:

### Market Data Endpoints ✅ Implemented
```python
# src/web/api/market_data.py
@router.get("/api/market-data/stats")
async def get_market_data_stats():
    """Get market data statistics"""
    
@router.get("/api/market-data/symbols")
async def get_symbols():
    """Get available symbols"""
    
@router.get("/api/market-data/data/{symbol}")
async def get_market_data(symbol: str, start_date: str = None, end_date: str = None):
    """Get historical market data"""
```

### Trading Endpoints ✅ Implemented
```python
# src/web/api/alpaca.py
@router.get("/api/alpaca/account")
async def get_account():
    """Get Alpaca account information"""
    
@router.get("/api/alpaca/positions")
async def get_positions():
    """Get all positions"""
    
@router.get("/api/alpaca/orders")
async def get_orders():
    """Get orders"""
```

### Analytics Endpoints ✅ Implemented
```python
# src/web/api/analytics.py
@router.get("/api/analytics/indicators/{symbol}")
async def get_technical_indicators(symbol: str):
    """Get technical indicators for a symbol"""
```

See [API Reference Documentation](../api/) for complete endpoint documentation.

---

**See Also**:
- [Stock Screener Architecture](stock-screener-architecture.md) - Detailed screener implementation
- [Architecture Overview](architecture-overview.md) - System overview
- [Services Architecture](architecture-services.md) - Backend services

