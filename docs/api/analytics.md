# Analytics API

This guide covers the analytics API endpoints for market data analysis, performance tracking, and reporting.

## Overview

The analytics service provides REST API endpoints for:
- Market data statistics and analysis
- Symbol information and data availability
- Performance metrics and reporting
- Data quality monitoring
- Interactive charting data

## Base URL

```
http://localhost:8001/api/market-data
```

## Endpoints

### Market Data Statistics

#### Get Market Data Statistics
```http
GET /api/market-data/stats
```

**Response:**
```json
{
  "total_symbols": 150,
  "total_records": 125000,
  "last_update": "2023-12-01T16:00:00Z",
  "data_sources": [
    {
      "source": "polygon",
      "symbols_count": 150,
      "records_count": 125000,
      "last_update": "2023-12-01T16:00:00Z"
    }
  ],
  "date_range": {
    "earliest": "2022-01-01T00:00:00Z",
    "latest": "2023-12-01T16:00:00Z"
  }
}
```

### Symbol Management

#### Get Available Symbols
```http
GET /api/market-data/symbols
```

**Response:**
```json
[
  {
    "symbol": "AAPL",
    "name": "Apple Inc.",
    "exchange": "NASDAQ",
    "sector": "Technology",
    "market_cap": 3000000000000,
    "status": "active",
    "data_count": 500,
    "last_update": "2023-12-01T16:00:00Z"
  },
  {
    "symbol": "MSFT",
    "name": "Microsoft Corporation",
    "exchange": "NASDAQ",
    "sector": "Technology",
    "market_cap": 2800000000000,
    "status": "active",
    "data_count": 500,
    "last_update": "2023-12-01T16:00:00Z"
  }
]
```

### Market Data Access

#### Get Market Data for Symbol
```http
GET /api/market-data/data/{symbol}
```

**Parameters:**
- `symbol` (path): The trading symbol (e.g., AAPL, MSFT)
- `start_date` (query, optional): Start date in YYYY-MM-DD format
- `end_date` (query, optional): End date in YYYY-MM-DD format
- `limit` (query, optional): Maximum number of records to return (default: 1000)

**Response:**
```json
[
  {
    "symbol": "AAPL",
    "timestamp": "2023-12-01T16:00:00Z",
    "open": 150.00,
    "high": 152.50,
    "low": 149.75,
    "close": 151.25,
    "volume": 45000000,
    "source": "polygon",
    "created_at": "2023-12-01T16:05:00Z"
  }
]
```

#### Get Latest Market Data
```http
GET /api/market-data/data/{symbol}/latest
```

**Parameters:**
- `symbol` (path): The trading symbol

**Response:**
```json
{
  "symbol": "AAPL",
  "timestamp": "2023-12-01T16:00:00Z",
  "open": 150.00,
  "high": 152.50,
  "low": 149.75,
  "close": 151.25,
  "volume": 45000000,
  "source": "polygon",
  "created_at": "2023-12-01T16:05:00Z"
}
```

#### Get Data Count for Symbol
```http
GET /api/market-data/data/{symbol}/count
```

**Parameters:**
- `symbol` (path): The trading symbol

**Response:**
```json
{
  "symbol": "AAPL",
  "count": 500,
  "date_range": {
    "earliest": "2022-01-01T00:00:00Z",
    "latest": "2023-12-01T16:00:00Z"
  }
}
```

#### Get OHLC Summary
```http
GET /api/market-data/data/{symbol}/ohlc
```

**Parameters:**
- `symbol` (path): The trading symbol
- `period` (query, optional): Time period (`1D`, `1W`, `1M`, `3M`, `6M`, `1Y`)

**Response:**
```json
{
  "symbol": "AAPL",
  "period": "1M",
  "summary": {
    "open": 150.00,
    "high": 158.75,
    "low": 148.50,
    "close": 155.25,
    "volume": 1250000000,
    "change": 5.25,
    "change_percent": 3.5
  },
  "daily_data": [
    {
      "date": "2023-12-01",
      "open": 150.00,
      "high": 152.50,
      "low": 149.75,
      "close": 151.25,
      "volume": 45000000
    }
  ]
}
```

## Data Models

### MarketDataResponse
```json
{
  "symbol": "string",
  "timestamp": "datetime",
  "open": "number",
  "high": "number",
  "low": "number",
  "close": "number",
  "volume": "integer",
  "source": "string",
  "created_at": "datetime"
}
```

### MarketDataStats
```json
{
  "total_symbols": "integer",
  "total_records": "integer",
  "last_update": "datetime",
  "data_sources": [
    {
      "source": "string",
      "symbols_count": "integer",
      "records_count": "integer",
      "last_update": "datetime"
    }
  ],
  "date_range": {
    "earliest": "datetime",
    "latest": "datetime"
  }
}
```

### SymbolInfo
```json
{
  "symbol": "string",
  "name": "string",
  "exchange": "string",
  "sector": "string",
  "market_cap": "integer",
  "status": "string",
  "data_count": "integer",
  "last_update": "datetime"
}
```

## Error Handling

### Error Response Format
```json
{
  "error": "string",
  "message": "string",
  "code": "integer",
  "details": "object"
}
```

### Common Error Codes
- `400` - Bad Request (invalid parameters)
- `404` - Not Found (symbol not found or no data available)
- `422` - Unprocessable Entity (invalid date format)
- `500` - Internal Server Error (server-side error)

## Data Quality and Validation

### Data Validation Rules
- Timestamps must be in UTC timezone
- OHLC values must be positive numbers
- Volume must be non-negative integers
- High must be >= Low
- High must be >= Open and Close
- Low must be <= Open and Close

### Data Quality Monitoring
The system continuously monitors data quality:
- Missing data detection
- Anomaly detection (unusual price movements)
- Data freshness monitoring
- Source validation

## Performance Considerations

### Caching Strategy
- Frequently accessed data is cached in Redis
- Cache TTL: 5 minutes for recent data
- Cache invalidation on new data updates

### Query Optimization
- Database indexes on symbol and timestamp
- Pagination for large datasets
- Efficient date range queries

## Examples

### Get Market Statistics
```bash
curl http://localhost:8001/api/market-data/stats
```

### Get Available Symbols
```bash
curl http://localhost:8001/api/market-data/symbols
```

### Get Historical Data for AAPL
```bash
curl "http://localhost:8001/api/market-data/data/AAPL?start_date=2023-11-01&end_date=2023-12-01&limit=100"
```

### Get Latest Data for MSFT
```bash
curl http://localhost:8001/api/market-data/data/MSFT/latest
```

### Get Data Count for GOOGL
```bash
curl http://localhost:8001/api/market-data/data/GOOGL/count
```

### Get Monthly OHLC Summary
```bash
curl "http://localhost:8001/api/market-data/data/AAPL/ohlc?period=1M"
```

## Integration with Streamlit UI

The analytics API is designed to work seamlessly with the Streamlit multipage interface:

### Chart Data
```python
import streamlit as st
import plotly.graph_objects as go
import requests

# Fetch data for Plotly charts
@st.cache_data
def get_market_data(symbol, limit=100):
    response = requests.get(f'http://localhost:8001/api/market-data/data/{symbol}?limit={limit}')
    return response.json()

# Create interactive charts
data = get_market_data('AAPL')
fig = go.Figure(data=go.Candlestick(
    x=[d['timestamp'] for d in data],
    open=[d['open'] for d in data],
    high=[d['high'] for d in data],
    low=[d['low'] for d in data],
    close=[d['close'] for d in data]
))
st.plotly_chart(fig, use_container_width=True)
```

### Session State Integration
```python
# Use session state for persistent data
if 'market_data' not in st.session_state:
    st.session_state.market_data = get_market_data('AAPL')

# Update data based on user selection
symbol = st.selectbox('Select Symbol', ['AAPL', 'MSFT', 'GOOGL'])
if symbol != st.session_state.get('selected_symbol'):
    st.session_state.market_data = get_market_data(symbol)
    st.session_state.selected_symbol = symbol
```

## Future Enhancements

### Planned Features
- Technical indicator calculations (SMA, EMA, RSI, MACD)
- Portfolio performance analytics
- Risk metrics calculation
- Backtesting results analysis
- Real-time data streaming
- Advanced charting endpoints

### Data Sources
- Integration with additional data providers
- Real-time market data feeds
- Alternative data sources (news, sentiment)
- Economic indicators integration