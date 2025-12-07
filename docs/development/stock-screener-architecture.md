# Stock Screener Architecture

Technical documentation for the AI-powered Stock Screener implementation.

## Overview

The Stock Screener is a Streamlit-based application that combines traditional filtering with AI-powered natural language query interpretation. It integrates with the Trading System API for market data and uses Ollama (local LLM) for intelligent query processing.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Streamlit UI (Screener.py)                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │ Natural Lang │  │ Traditional │  │   Results   │       │
│  │   Query Tab  │  │ Filters Tab │  │   Display   │       │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘       │
└─────────┼──────────────────┼──────────────────┼─────────────┘
          │                  │                  │
          ▼                  ▼                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    LLM Service Layer                        │
│  ┌──────────────────────────────────────────────────────┐  │
│  │  interpret_screening_query()                        │  │
│  │  analyze_screened_results()                         │  │
│  └──────────────────┬─────────────────────────────────┘  │
└──────────────────────┼────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Ollama (Local LLM)                        │
│                  http://localhost:11434                      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              Technical Indicators Module                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  │
│  │   RSI    │  │   MACD   │  │   SMA    │  │  Volatility│ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    Trading System API                        │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Market Data │  │ Company Info │  │   Symbols    │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└─────────────────────────────────────────────────────────────┘
```

## Components

### 1. Screener Page (`streamlit_ui/pages/Screener.py`)

Main Streamlit page component.

**Key Functions:**

```python
def screener_page()
    """Main screener page entry point"""
    # Initializes API client and LLM service
    # Creates tabbed interface
    # Handles user interactions
    # Displays results

def calculate_indicators_for_symbol(api_client, symbol, ohlc_data)
    """Calculate all technical indicators for a symbol"""
    # Calculates RSI, MACD, SMA, volatility
    # Extracts price and volume metrics
    # Returns dictionary of indicators

def screen_stocks(api_client, llm_service, criteria, symbols)
    """Screen stocks based on criteria"""
    # Iterates through symbols
    # Fetches market data
    # Calculates indicators
    # Applies filters
    # Returns matching stocks
```

**Session State:**
- `screener_results`: List of screened stock results
- `screener_query`: Last natural language query

### 2. LLM Service (`streamlit_ui/services/llm_service.py`)

Service for interacting with Ollama local LLM.

**Class: `LLMService`**

```python
class LLMService:
    def __init__(self, model: str = "phi3", base_url: Optional[str] = None)
        """Initialize LLM service with model and base URL"""
    
    def interpret_screening_query(self, query: str) -> Dict[str, Any]
        """Parse natural language query into structured criteria"""
        # Uses LLM to extract:
        # - sector, industry
        # - price ranges
        # - volume thresholds
        # - RSI ranges
        # - price change filters
        # - keywords
    
    def analyze_screened_results(self, results: List[Dict], query: Optional[str]) -> str
        """Generate AI analysis of screening results"""
        # Analyzes patterns
        # Identifies opportunities/risks
        # Provides insights
    
    def get_model_info(self) -> Dict[str, Any]
        """Get information about available models"""
```

**Query Interpretation Prompt:**
The LLM receives a structured prompt asking it to extract screening criteria from natural language and return JSON with specific fields.

**Analysis Prompt:**
The LLM receives a summary of results and generates 2-3 sentence analysis with insights.

### 3. Technical Indicators (`streamlit_ui/utils/technical_indicators.py`)

Collection of technical indicator calculation functions.

**Functions:**

```python
def calculate_rsi(prices: List[float], period: int = 14) -> Optional[float]
    """Calculate Relative Strength Index (0-100)"""
    # Uses price changes over period
    # Calculates average gains vs losses
    # Returns RSI value

def calculate_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Optional[Dict]
    """Calculate MACD indicator"""
    # Calculates fast and slow EMAs
    # Computes MACD line and signal
    # Returns dictionary with values

def calculate_sma(prices: List[float], period: int) -> Optional[float]
    """Calculate Simple Moving Average"""
    
def calculate_ema(prices: List[float], period: int) -> Optional[float]
    """Calculate Exponential Moving Average"""
    
def calculate_bollinger_bands(prices: List[float], period: int = 20, std_dev: float = 2.0) -> Optional[Dict]
    """Calculate Bollinger Bands"""
    
def calculate_price_change(prices: List[float], periods: int = 1) -> Optional[float]
    """Calculate price change percentage"""
    
def calculate_volatility(prices: List[float], period: int = 20) -> Optional[float]
    """Calculate annualized volatility"""
```

**Implementation Details:**
- Uses pandas-ta library for all technical indicator calculations
- Industry-standard implementations (SMA, EMA, RSI, MACD, Bollinger Bands)
- Handles edge cases (insufficient data, division by zero)
- Returns `None` when data is insufficient
- Proper MACD signal line calculation (not simplified)

### 4. API Client Integration

Uses existing `TradingSystemAPI` client:

```python
from streamlit_ui.api_client import get_api_client

api_client = get_api_client()

# Get symbols
symbols = api_client.get_all_symbols()
symbols = api_client.get_symbols_by_filter(sector="Technology", industry="Software")

# Get market data
ohlc_data = api_client.get_market_data(symbol="AAPL", data_source="yahoo")

# Get company info
company_info = api_client.get_company_info(symbol="AAPL")
```

## Data Flow

### Natural Language Query Flow

```
1. User enters query: "Find tech stocks with RSI < 30"
   │
   ▼
2. LLM Service interprets query
   │
   ▼
3. Returns structured criteria:
   {
     "sector": "Technology",
     "rsi_max": 30
   }
   │
   ▼
4. screen_stocks() function:
   - Loads symbols from API
   - For each symbol:
     a. Fetches market data
     b. Calculates indicators
     c. Applies filters
     d. Adds to results if matches
   │
   ▼
5. Results displayed in table
   │
   ▼
6. LLM generates analysis of results
   │
   ▼
7. Analysis displayed to user
```

### Traditional Filter Flow

```
1. User sets filters in UI
   │
   ▼
2. Criteria dictionary built from inputs
   │
   ▼
3. screen_stocks() function (same as above)
   │
   ▼
4. Results displayed (no LLM analysis)
```

## Filtering Logic

### Criteria Dictionary Structure

```python
{
    "sector": str | None,              # Sector name
    "industry": str | None,             # Industry name
    "min_price": float | None,          # Minimum price
    "max_price": float | None,          # Maximum price
    "min_volume": int | None,           # Minimum average volume
    "min_market_cap": float | None,     # Minimum market cap (billions)
    "rsi_min": float | None,            # Minimum RSI (0-100)
    "rsi_max": float | None,            # Maximum RSI (0-100)
    "min_price_change_pct": float | None,  # Min 30d price change %
    "max_price_change_pct": float | None,  # Max 30d price change %
    "keywords": List[str] | None        # Search keywords
}
```

### Filter Application

Filters are applied sequentially with AND logic:
- All specified criteria must match
- Missing criteria are ignored (no filter applied)
- Numeric comparisons use standard operators (<, >, <=, >=)
- String matching uses case-insensitive contains

## Performance Considerations

### Optimization Strategies

1. **Database-Backed Indicators (Recommended):**
   - Pre-calculated indicators stored in database
   - 10-100x faster than on-the-fly calculation
   - Direct SQL filtering on RSI, MACD, etc.
   - Supports screening thousands of symbols
   - **Implementation**: See "Technical Indicators Storage" section below

2. **Caching:**
   - Company info cached for 30 minutes
   - Sectors/industries cached for 1 hour
   - Indicator values cached in database
   - Reduces API calls and calculations

3. **Batch Processing:**
   - Processes symbols sequentially
   - Shows progress indicator
   - Limits to 50 symbols for demo (can increase with database)

4. **Lazy Loading:**
   - Only loads data when needed
   - Skips symbols that fail early filters
   - Database queries filter before fetching full data

5. **Error Handling:**
   - Continues processing on individual symbol errors
   - Logs errors without stopping entire process
   - Falls back to calculation if database unavailable

### Bottlenecks

1. **API Calls:**
   - Each symbol requires 2-3 API calls (market data + company info)
   - Network latency adds up
   - **Solution**: Caching, parallel processing, database storage

2. **Indicator Calculations:**
   - RSI, MACD require full price history
   - Some calculations are O(n) where n = data points
   - **Solution**: Pre-calculate and store in database (10-100x faster)

3. **LLM Processing:**
   - Query interpretation: ~1-2 seconds
   - Result analysis: ~2-5 seconds
   - **Solution**: Use faster models (phi3), async processing (future)

## Technical Indicators Storage

### Recommended Architecture: Hybrid Approach

Store indicators in database for performance while maintaining calculation fallback.

#### Database Schema

**Latest Values Table** (for fast screening):
```sql
CREATE TABLE data_ingestion.technical_indicators_latest (
    symbol VARCHAR(20) PRIMARY KEY,
    calculated_date DATE NOT NULL,
    
    -- Moving Averages
    sma_20 NUMERIC(15,4),
    sma_50 NUMERIC(15,4),
    ema_12 NUMERIC(15,4),
    ema_26 NUMERIC(15,4),
    
    -- Momentum
    rsi NUMERIC(5,2),  -- 0-100
    rsi_14 NUMERIC(5,2),
    
    -- MACD
    macd_line NUMERIC(15,4),
    macd_signal NUMERIC(15,4),
    macd_histogram NUMERIC(15,4),
    
    -- Bollinger Bands
    bb_upper NUMERIC(15,4),
    bb_middle NUMERIC(15,4),
    bb_lower NUMERIC(15,4),
    bb_position NUMERIC(5,4),
    
    -- Volatility & Price Changes
    volatility_20 NUMERIC(5,2),
    price_change_1d NUMERIC(5,2),
    price_change_30d NUMERIC(5,2),
    
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

**Time-Series Table** (for historical analysis):
```sql
CREATE TABLE data_ingestion.technical_indicators (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    -- Same indicator fields as latest table
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT unique_symbol_date UNIQUE (symbol, date)
);
```

#### Calculation Service

**Service Structure:**
```
src/services/analytics/
├── indicator_calculator.py    # Main calculation service
├── indicator_storage.py        # Database storage operations
└── indicator_models.py        # SQLAlchemy models
```

**Key Functions:**
- `calculate_indicators_for_symbol()`: Calculate all indicators for a symbol
- `batch_calculate_indicators()`: Process multiple symbols
- `update_indicator_tables()`: Store in both latest and time-series tables
- `get_latest_indicators()`: Retrieve current values for screening

#### Data Pipeline

1. **Daily Calculation Job:**
   - Runs after market close
   - Calculates indicators for all active symbols
   - Updates both tables
   - Handles missing data gracefully

2. **On-Demand Calculation:**
   - For new symbols
   - For missing dates
   - Triggered by data ingestion

3. **Incremental Updates:**
   - Only calculate for new market data
   - Skip if already calculated
   - Efficient for daily updates

#### Screener Integration

**Updated Flow:**
```python
def get_indicators_for_symbol(symbol):
    # 1. Try database first (fast)
    indicators = get_latest_indicators_from_db(symbol)
    if indicators:
        return indicators
    
    # 2. Fallback to calculation
    market_data = get_market_data(symbol)
    indicators = calculate_indicators(market_data)
    
    # 3. Store for future use (optional)
    store_indicators_in_db(symbol, indicators)
    
    return indicators
```

**Benefits:**
- Fast screening (database queries)
- Always works (fallback calculation)
- Automatic optimization (stores calculated values)
- No breaking changes (backward compatible)

#### Performance Comparison

| Approach | Symbols/Second | Storage | Scalability |
|----------|---------------|---------|-------------|
| **On-the-fly Calculation** | 0.5-1 | None | Limited (50 symbols) |
| **Database Storage** | 10-50 | ~50-100 bytes/symbol/day | Excellent (1000+ symbols) |

#### Migration Strategy

1. **Phase 1**: Create database tables (no breaking changes)
2. **Phase 2**: Build calculation service
3. **Phase 3**: Populate for existing symbols
4. **Phase 4**: Update screener to use database
5. **Phase 5**: Add scheduled calculation jobs

## Error Handling

### LLM Service Errors

```python
try:
    criteria = llm_service.interpret_screening_query(query)
except Exception as e:
    # Falls back to empty criteria
    # Shows warning to user
    # Allows traditional filters as fallback
```

### API Errors

```python
try:
    ohlc_data = get_real_market_data(api_client, symbol, "yahoo")
except Exception as e:
    # Skips symbol
    # Logs error
    # Continues with next symbol
```

### Data Quality Issues

- Missing data: Returns `None` for indicators
- Insufficient history: Skips indicator calculation
- Invalid values: Uses safe defaults

## Testing

### Unit Tests

Test technical indicators:
```python
def test_calculate_rsi():
    prices = [100, 102, 101, 103, 105, 104, 106]
    rsi = calculate_rsi(prices, period=5)
    assert 0 <= rsi <= 100
```

### Integration Tests

Test screening flow:
```python
def test_screen_stocks():
    criteria = {"sector": "Technology", "rsi_max": 30}
    results = screen_stocks(api_client, llm_service, criteria, ["AAPL", "MSFT"])
    assert isinstance(results, list)
```

### Manual Testing

1. Test natural language queries
2. Test traditional filters
3. Verify indicator calculations
4. Check LLM integration
5. Test error handling

## Configuration

### Environment Variables

```bash
# Ollama Configuration (optional)
OLLAMA_BASE_URL=http://localhost:11434  # Default

# Model Selection
OLLAMA_MODEL=phi3  # Default model
```

### Code Configuration

In `Screener.py`:
```python
# Symbol limit for screening
symbols[:50]  # Limit to 50 symbols

# LLM model selection
llm_service = get_llm_service(model="phi3")
```

## Dependencies

### Required Packages

```python
# Core
streamlit>=1.28.0
pandas>=2.0.0
numpy>=1.24.0

# LLM Integration
ollama>=0.1.0

# UI Components
st-aggrid>=1.2.0  # For interactive tables
plotly>=5.17.0     # For charts (if added)

# API Client
requests>=2.31.0
```

### External Services

- **Ollama**: Must be running locally on port 11434
- **Trading System API**: Must be accessible
- **Database**: Market data must be populated

## Future Enhancements

### Planned Features

1. **Parallel Processing:**
   - Process multiple symbols concurrently
   - Use asyncio for API calls
   - Reduce total screening time

2. **Advanced Filters:**
   - More technical indicators
   - Custom indicator definitions
   - Pattern recognition filters

3. **Saved Screens:**
   - Save filter combinations
   - Schedule automatic screening
   - Alert on matches

4. **Performance Improvements:**
   - Batch API calls
   - Pre-calculate indicators
   - Cache results

5. **Enhanced AI:**
   - Better query understanding
   - Multi-turn conversations
   - Strategy suggestions

## Security Considerations

### Local LLM

- ✅ No data sent to external services
- ✅ All processing happens locally
- ✅ No API keys required for LLM

### API Access

- Uses existing API authentication
- Respects API rate limits
- Handles connection errors gracefully

### Data Privacy

- No user data stored
- Results only in session state
- CSV exports are user-initiated

## Troubleshooting Guide

### Common Issues

1. **LLM Not Responding:**
   - Check Ollama is running: `ollama list`
   - Verify model installed: `ollama pull phi3`
   - Test connection: `python scripts/test_ollama.py`

2. **No Results:**
   - Check filter criteria
   - Verify market data exists
   - Check API connection

3. **Slow Performance:**
   - Reduce symbol count
   - Use traditional filters (faster)
   - Check API response times

4. **Missing Indicators:**
   - Ensure sufficient historical data
   - Check data quality
   - Verify calculation functions

## Code Examples

### Adding a New Filter

```python
# In screen_stocks() function
if criteria.get('new_filter'):
    if stock_value < criteria['new_filter']:
        matches = False
```

### Adding a New Indicator

```python
# In technical_indicators.py
def calculate_new_indicator(prices: List[float]) -> Optional[float]:
    # Implementation
    pass

# In calculate_indicators_for_symbol()
indicators['new_indicator'] = calculate_new_indicator(closing_prices)
```

### Customizing LLM Prompts

```python
# In llm_service.py
prompt = f"""Your custom prompt here...
Query: "{query}"
...
"""
```

---

**Last Updated**: December 2025  
**Version**: 1.0.0  
**Author**: Trading System Development Team

