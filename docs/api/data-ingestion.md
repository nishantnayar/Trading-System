# Data Ingestion Architecture

## Overview

The Data Ingestion Service is a critical component of the trading system responsible for collecting, validating, and storing market data from various financial data providers. This document outlines the architecture, design patterns, and implementation details for the data ingestion pipeline.

**Current Data Sources:**
- **Polygon.io Free Tier** (Historical end-of-day data for backtesting)
- **Alpaca Markets** (Real-time trading data and account information)

**Hybrid Strategy:**
- **Polygon.io**: Historical data, backtesting, strategy development, symbol management
- **Alpaca**: Real-time trading, position management, order execution

**Symbol Management:**
- **Database-driven symbol tracking** with automatic delisting detection
- **100 initial symbols** configured for data collection
- **Active/delisted status tracking** to avoid unnecessary API calls
- **Data ingestion status monitoring** per symbol and date

**Future Data Sources:**
- Alpha Vantage (Real-time data alternative)
- IEX Cloud (Additional market data)
- Yahoo Finance (Free real-time quotes)
- Custom data feeds

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    External Data Sources                        │
├─────────────────────────────────────────────────────────────────┤
│  Polygon.io     │  Alpaca       │  Future Sources               │
│  (Historical    │  (Real-time   │  (Alpha Vantage, etc.)        │
│   End-of-Day)   │   Trading)    │                               │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                Data Ingestion Service                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ Provider    │  │ Data        │  │ Rate        │            │
│  │ Clients     │  │ Validators  │  │ Limiters    │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ Error       │  │ Data        │  │ Quality     │            │
│  │ Handlers    │  │ Transformers│  │ Monitors    │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Storage Layer                                │
├─────────────────────────────────────────────────────────────────┤
│  PostgreSQL      │  Redis Cache   │  Polars DataFrames          │
│  (Metadata)      │  (Hot Data)    │  (Analytics)                │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                 Prefect Orchestration                           │
├─────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ End-of-Day  │  │ Historical  │  │ Data        │            │
│  │ Updates     │  │ Backfill    │  │ Quality     │            │
│  │ (Polygon)   │  │ (Polygon)   │  │ Monitoring  │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐            │
│  │ Real-time   │  │ Trading     │  │ Account     │            │
│  │ Trading     │  │ Execution   │  │ Monitoring  │            │
│  │ (Alpaca)    │  │ (Alpaca)    │  │ (Alpaca)    │            │
│  └─────────────┘  └─────────────┘  └─────────────┘            │
└─────────────────────────────────────────────────────────────────┘
```

## Core Components

### 1. Provider Clients

Each data provider has its own client implementation that handles:
- Authentication and API key management
- Rate limiting and quota management
- Error handling and retry logic
- Data format standardization

#### Polygon.io Client
- **Rate Limiting**: 5 calls/minute (free tier)
- **Data Types**: End-of-day data, basic market data
- **Real-time**: **Not available** on free tier (end-of-day only)
- **Historical**: 2 years of data available (not 5 years)
- **WebSocket**: **Not available** on free tier

#### Alpaca Client
- **Rate Limiting**: 200 calls/minute
- **Data Types**: Account data, positions, orders, trades
- **Real-time**: Live trading data
- **Integration**: Existing implementation in `src/services/alpaca/`

### 2. Data Validators

Pydantic models ensure data quality and consistency:

```python
# Example: Market Data Model
class MarketDataBar(BaseModel):
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    source: str = "polygon"
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
```

### 3. Rate Limiters

Intelligent rate limiting strategies for each provider:

```python
class RateLimiter:
    def __init__(self, calls_per_minute: int, safety_margin: float = 0.8):
        self.calls_per_minute = calls_per_minute
        self.safety_margin = safety_margin
        self.actual_limit = int(calls_per_minute * safety_margin)
        self.call_history = deque()
    
    async def acquire(self) -> bool:
        # Implementation with sliding window
        pass
```

### 4. Data Transformers

Convert provider-specific data formats to standardized internal format:

```python
class DataTransformer:
    def transform_polygon_bar(self, raw_data: dict) -> MarketDataBar:
        # Transform Polygon.io format to internal format
        pass
    
    def transform_alpaca_trade(self, raw_data: dict) -> TradeData:
        # Transform Alpaca format to internal format
        pass
```

## Hybrid Data Strategy

### Strategic Approach

Our trading system uses a **hybrid data strategy** that maximizes the value of free data sources while ensuring real-time trading capabilities:

#### **Polygon.io Free Tier - Historical & Backtesting**
- **Purpose**: Strategy development, backtesting, and historical analysis
- **Data Type**: End-of-day OHLCV data
- **Timeframe**: 2 years of historical data
- **Rate Limit**: 5 calls/minute
- **Use Cases**:
  - Historical backtesting of trading strategies
  - Long-term trend analysis
  - Portfolio optimization
  - Strategy development and validation

#### **Alpaca Markets - Real-Time Trading**
- **Purpose**: Live trading operations and account management
- **Data Type**: Real-time account data, positions, orders
- **Timeframe**: Live/real-time
- **Rate Limit**: 200 calls/minute
- **Use Cases**:
  - Real-time order execution
  - Position monitoring
  - Account balance tracking
  - Trade execution and management

### Benefits of Hybrid Approach

1. **Cost Efficiency**: Leverage free Polygon.io data for historical analysis
2. **Real-Time Capability**: Use Alpaca for live trading operations
3. **Comprehensive Coverage**: Historical + real-time data coverage
4. **Scalability**: Easy to upgrade individual components as needed
5. **Risk Mitigation**: Diversified data sources reduce dependency

### Data Flow Architecture

```
Historical Strategy Development:
Polygon.io → Historical Data → Backtesting → Strategy Validation

Real-Time Trading Execution:
Alpaca → Live Account Data → Strategy Engine → Order Execution

Data Integration:
Historical Performance + Real-Time Execution = Complete Trading System
```

## Data Sources

### Polygon.io Integration

#### Free Tier Capabilities
- **API Calls**: 5 per minute (300 per hour)
- **Historical Data**: 2 years available
- **Real-time Data**: **Not available** (end-of-day only)
- **Data Types**: End-of-day OHLCV bars, basic market data
- **WebSocket**: **Not available** on free tier
- **Delayed Data**: **Not available** (end-of-day only)

#### Data Collection Strategy

**Historical Backfill**
```
1. Download 2 years of daily end-of-day data (1 call per symbol)
2. Download recent end-of-day data for active symbols
3. Batch multiple symbols per call when possible
4. Store in PostgreSQL with compression
```

**End-of-Day Updates**
```
1. Daily: Update end-of-day data after market close
2. Use 4 calls/minute (80% of limit) for safety
3. Prioritize symbols in trading universe
4. Cache recent data in Redis
```

**Note**: Free tier only provides end-of-day data, not intraday or real-time data.

#### Implications for Trading Strategies

**Limitations of End-of-Day Data:**
- **No Intraday Trading**: Cannot execute strategies that require minute/hourly data
- **Delayed Execution**: Can only place orders based on previous day's close
- **Limited Technical Analysis**: Many indicators require intraday data
- **Backtesting Constraints**: Historical testing limited to daily timeframes

**Suitable Strategy Types:**
- **Swing Trading**: Hold positions for days/weeks
- **Position Trading**: Long-term investment strategies
- **End-of-Day Rebalancing**: Portfolio rebalancing based on daily close
- **Fundamental Analysis**: Strategies based on company fundamentals

**Alternative Data Sources for Real-Time:**
- **Alpaca Markets**: Provides real-time trading data for positions/orders
- **Yahoo Finance**: Free real-time quotes (with limitations)
- **Alpha Vantage**: Real-time data with higher rate limits

#### Rate Limiting Strategy
```python
# Free Tier: 5 calls/minute
# Strategy: Use 4 calls/minute (80% safety margin)
# Batch Strategy: Group symbols when possible

class PolygonRateLimiter:
    def __init__(self):
        self.calls_per_minute = 4  # 80% of 5
        self.sliding_window = deque(maxlen=self.calls_per_minute)
    
    async def can_make_call(self) -> bool:
        now = time.time()
        # Remove calls older than 1 minute
        while self.sliding_window and now - self.sliding_window[0] > 60:
            self.sliding_window.popleft()
        
        return len(self.sliding_window) < self.calls_per_minute
```

### Alpaca Integration

#### Existing Implementation
- **Client**: Located in `src/services/alpaca/client.py`
- **Rate Limiting**: 200 calls/minute
- **Data Types**: Account, positions, orders, trades
- **Integration**: Already integrated with trading system

#### Enhancement Plan
- Standardize data models with other providers
- Add data quality monitoring
- Implement caching layer
- Add error recovery mechanisms

## Storage Architecture

### PostgreSQL Schema

```sql
-- Data Ingestion Schema
CREATE SCHEMA data_ingestion;

-- Symbols Management Table
CREATE TABLE data_ingestion.symbols (
    symbol VARCHAR(10) PRIMARY KEY,
    name VARCHAR(255),
    exchange VARCHAR(50),
    sector VARCHAR(100),
    market_cap BIGINT,
    status VARCHAR(20) DEFAULT 'active', -- active, delisted, suspended
    added_date TIMESTAMP DEFAULT NOW(),
    last_updated TIMESTAMP DEFAULT NOW()
);

-- Delisted Symbols Tracking
CREATE TABLE data_ingestion.delisted_symbols (
    symbol VARCHAR(10) PRIMARY KEY,
    delist_date DATE,
    last_price DECIMAL(10,2),
    notes TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

-- Data Ingestion Status Tracking
CREATE TABLE data_ingestion.symbol_data_status (
    symbol VARCHAR(10),
    date DATE,
    data_source VARCHAR(50), -- 'polygon', 'alpaca'
    status VARCHAR(20), -- 'success', 'failed', 'no_data'
    error_message TEXT,
    last_attempt TIMESTAMP DEFAULT NOW(),
    PRIMARY KEY (symbol, date, data_source)
);

-- Market Data Table
CREATE TABLE data_ingestion.market_data (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    open DECIMAL(10,4) NOT NULL,
    high DECIMAL(10,4) NOT NULL,
    low DECIMAL(10,4) NOT NULL,
    close DECIMAL(10,4) NOT NULL,
    volume BIGINT NOT NULL,
    source VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    UNIQUE(symbol, timestamp, source)
);

-- Data Quality Logs
CREATE TABLE data_ingestion.data_quality_logs (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10),
    check_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    message TEXT,
    timestamp TIMESTAMPTZ DEFAULT NOW()
);

-- Provider Configuration
CREATE TABLE data_ingestion.provider_config (
    provider_name VARCHAR(50) PRIMARY KEY,
    api_key_hash VARCHAR(255),
    rate_limit_per_minute INTEGER,
    is_active BOOLEAN DEFAULT TRUE,
    last_updated TIMESTAMPTZ DEFAULT NOW()
);

-- Create indexes
CREATE INDEX idx_symbols_status ON data_ingestion.symbols(status);
CREATE INDEX idx_symbol_data_status_symbol_date ON data_ingestion.symbol_data_status(symbol, date);
CREATE INDEX idx_market_data_symbol_timestamp ON data_ingestion.market_data(symbol, timestamp);
CREATE INDEX idx_market_data_timestamp ON data_ingestion.market_data(timestamp);
CREATE INDEX idx_data_quality_logs_timestamp ON data_ingestion.data_quality_logs(timestamp);
```

### Redis Caching Strategy

```python
# Cache Keys Structure
CACHE_KEYS = {
    "recent_bars": "data:bars:{symbol}:{timeframe}",
    "active_symbols": "data:active_symbols",
    "rate_limits": "rate_limit:{provider}",
    "last_update": "data:last_update:{symbol}",
}

# Cache TTL Strategy
CACHE_TTL = {
    "recent_bars": 300,  # 5 minutes
    "active_symbols": 3600,  # 1 hour
    "rate_limits": 60,  # 1 minute
    "last_update": 300,  # 5 minutes
}
```

### Polars DataFrames

For large-scale analytics and backtesting:

```python
import polars as pl

class DataAnalytics:
    def __init__(self):
        self.analytics_cache = {}
    
    def load_market_data(self, symbols: List[str], start_date: datetime, end_date: datetime) -> pl.DataFrame:
        # Load data from PostgreSQL into Polars DataFrame
        # Optimize for time-series operations
        pass
    
    def calculate_technical_indicators(self, df: pl.DataFrame) -> pl.DataFrame:
        # Vectorized technical indicator calculations
        pass
```

## Prefect Flows

### Hybrid Data Ingestion Flows

The system uses separate flows for different data sources and purposes:

#### **Polygon.io Flows (Historical & Backtesting)**

```python
@flow(name="historical_data_backfill")
async def historical_data_backfill_flow(
    symbols: List[str],
    start_date: datetime,
    end_date: datetime,
    provider: str = "polygon"
):
    """Backfill historical market data"""
    
    # Validate inputs
    validate_symbols(symbols)
    validate_date_range(start_date, end_date)
    
    # Create rate limiter
    rate_limiter = get_rate_limiter(provider)
    
    # Process symbols in batches
    for symbol_batch in chunk_list(symbols, batch_size=4):
        for symbol in symbol_batch:
            # Check rate limit
            await rate_limiter.acquire()
            
            # Fetch data
            data = await fetch_historical_data(symbol, start_date, end_date, provider)
            
            # Validate and transform
            validated_data = validate_and_transform(data)
            
            # Store in database
            await store_market_data(validated_data)
            
            # Log progress
            logger.info(f"Backfilled {symbol} from {start_date} to {end_date}")
```

### 2. End-of-Day Update Flow

```python
@flow(name="end_of_day_data_update")
async def end_of_day_data_update_flow():
    """Update end-of-day market data for active symbols"""
    
    # Get active symbols from configuration
    active_symbols = get_active_symbols()
    
    # Create rate limiter
    rate_limiter = get_rate_limiter("polygon")
    
    # Process symbols in batches
    for symbol_batch in chunk_list(active_symbols, batch_size=4):
        for symbol in symbol_batch:
            # Check rate limit
            await rate_limiter.acquire()
            
            # Fetch end-of-day data (latest available)
            eod_data = await fetch_end_of_day_data(symbol, "polygon")
            
            # Validate data quality
            if validate_data_quality(eod_data):
                # Store in database
                await store_market_data(eod_data)
                
                # Update cache
                await update_cache(symbol, eod_data)
            else:
                # Log quality issues
                await log_data_quality_issue(symbol, eod_data)
```

**Note**: This flow runs daily after market close since free tier only provides end-of-day data.

#### **Alpaca Flows (Real-Time Trading)**

```python
@flow(name="alpaca_account_monitoring")
async def alpaca_account_monitoring_flow():
    """Monitor Alpaca account status and positions"""
    
    # Get account information
    account_data = await fetch_alpaca_account()
    
    # Get current positions
    positions = await fetch_alpaca_positions()
    
    # Update account cache
    await update_account_cache(account_data, positions)
    
    # Log account status
    logger.info(f"Account Status: {account_data.status}")

@flow(name="alpaca_order_monitoring")
async def alpaca_order_monitoring_flow():
    """Monitor active orders and executions"""
    
    # Get active orders
    active_orders = await fetch_alpaca_orders(status="open")
    
    # Check for filled orders
    filled_orders = await fetch_alpaca_orders(status="filled")
    
    # Process order updates
    for order in filled_orders:
        await process_order_execution(order)
    
    # Update order cache
    await update_order_cache(active_orders, filled_orders)
```

### 3. Data Quality Monitoring Flow

```python
@flow(name="data_quality_monitoring")
async def data_quality_monitoring_flow():
    """Monitor data quality and detect anomalies"""
    
    # Check for missing data
    missing_data = await detect_missing_data()
    
    # Check for data anomalies
    anomalies = await detect_data_anomalies()
    
    # Check for stale data
    stale_data = await detect_stale_data()
    
    # Generate quality report
    quality_report = generate_quality_report(missing_data, anomalies, stale_data)
    
    # Store quality metrics
    await store_quality_metrics(quality_report)
    
    # Send alerts if needed
    if quality_report.alert_level > 0:
        await send_quality_alert(quality_report)
```

## Configuration Management

### Environment Variables

```bash
# Polygon.io Configuration (Historical Data)
POLYGON_API_KEY=your_polygon_api_key
POLYGON_RATE_LIMIT_PER_MINUTE=4
POLYGON_BASE_URL=https://api.polygon.io
POLYGON_UPDATE_INTERVAL=86400  # 24 hours (end-of-day)

# Alpaca Configuration (Real-Time Trading)
ALPACA_API_KEY=your_alpaca_api_key
ALPACA_SECRET_KEY=your_alpaca_secret_key
ALPACA_BASE_URL=https://paper-api.alpaca.markets
ALPACA_UPDATE_INTERVAL=60  # 1 minute (real-time)

# Data Ingestion Configuration
DATA_INGESTION_ACTIVE_SYMBOLS=AAPL,MSFT,GOOGL,TSLA
DATA_INGESTION_CACHE_TTL=300  # 5 minutes
DATA_INGESTION_MAX_RETRIES=3

# Hybrid Strategy Configuration
ENABLE_HISTORICAL_BACKFILL=true
ENABLE_REALTIME_TRADING=true
HISTORICAL_DATA_SOURCE=polygon
REALTIME_TRADING_SOURCE=alpaca
```

### Settings Configuration

```python
# Add to src/config/settings.py
class DataIngestionSettings(BaseSettings):
    # Polygon.io (Historical Data)
    polygon_api_key: str = Field(default="", alias="POLYGON_API_KEY")
    polygon_rate_limit_per_minute: int = Field(default=4, alias="POLYGON_RATE_LIMIT_PER_MINUTE")
    polygon_base_url: str = Field(default="https://api.polygon.io", alias="POLYGON_BASE_URL")
    polygon_update_interval: int = Field(default=86400, alias="POLYGON_UPDATE_INTERVAL")  # 24 hours
    
    # Alpaca (Real-Time Trading)
    alpaca_update_interval: int = Field(default=60, alias="ALPACA_UPDATE_INTERVAL")  # 1 minute
    
    # Data Ingestion
    active_symbols: List[str] = Field(default=["AAPL", "MSFT", "GOOGL"], alias="DATA_INGESTION_ACTIVE_SYMBOLS")
    cache_ttl: int = Field(default=300, alias="DATA_INGESTION_CACHE_TTL")
    max_retries: int = Field(default=3, alias="DATA_INGESTION_MAX_RETRIES")
    
    # Hybrid Strategy
    enable_historical_backfill: bool = Field(default=True, alias="ENABLE_HISTORICAL_BACKFILL")
    enable_realtime_trading: bool = Field(default=True, alias="ENABLE_REALTIME_TRADING")
    historical_data_source: str = Field(default="polygon", alias="HISTORICAL_DATA_SOURCE")
    realtime_trading_source: str = Field(default="alpaca", alias="REALTIME_TRADING_SOURCE")
    
    # Data Quality
    quality_check_interval: int = Field(default=3600, alias="DATA_QUALITY_CHECK_INTERVAL")  # 1 hour
    max_missing_data_threshold: float = Field(default=0.05, alias="MAX_MISSING_DATA_THRESHOLD")  # 5%
    anomaly_detection_enabled: bool = Field(default=True, alias="ANOMALY_DETECTION_ENABLED")
```

## Error Handling and Recovery

### Error Types and Strategies

1. **API Rate Limit Errors**
   - Implement exponential backoff
   - Queue requests for later processing
   - Log rate limit violations

2. **Network Errors**
   - Retry with exponential backoff
   - Circuit breaker pattern
   - Fallback to cached data

3. **Data Quality Errors**
   - Validate data before storage
   - Log quality issues
   - Alert on critical errors

4. **Database Errors**
   - Connection pooling and retry
   - Transaction rollback
   - Data consistency checks

### Circuit Breaker Implementation

```python
class CircuitBreaker:
    def __init__(self, failure_threshold: int = 5, timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
    
    async def call(self, func, *args, **kwargs):
        if self.state == "OPEN":
            if time.time() - self.last_failure_time > self.timeout:
                self.state = "HALF_OPEN"
            else:
                raise Exception("Circuit breaker is OPEN")
        
        try:
            result = await func(*args, **kwargs)
            self.on_success()
            return result
        except Exception as e:
            self.on_failure()
            raise e
```

## Monitoring and Observability

### Key Metrics

1. **Data Ingestion Metrics**
   - API calls per minute
   - Data points ingested per hour
   - Success/failure rates
   - Data freshness

2. **Quality Metrics**
   - Missing data percentage
   - Data anomalies detected
   - Validation failures
   - Cache hit rates

3. **Performance Metrics**
   - Ingestion latency
   - Database write performance
   - Cache performance
   - Error rates

### Logging Strategy

```python
# Structured logging for data ingestion
logger.info(
    "Data ingestion completed",
    extra={
        "symbol": symbol,
        "provider": "polygon",
        "data_points": len(data),
        "duration_seconds": duration,
        "success": True
    }
)
```

### Health Checks

```python
@flow(name="data_ingestion_health_check")
async def data_ingestion_health_check():
    """Comprehensive health check for data ingestion"""
    
    health_status = {
        "status": "healthy",
        "checks": {}
    }
    
    # Check API connectivity
    health_status["checks"]["api_connectivity"] = await check_api_connectivity()
    
    # Check database connectivity
    health_status["checks"]["database"] = await check_database_connectivity()
    
    # Check cache connectivity
    health_status["checks"]["cache"] = await check_cache_connectivity()
    
    # Check data freshness
    health_status["checks"]["data_freshness"] = await check_data_freshness()
    
    # Check rate limit status
    health_status["checks"]["rate_limits"] = await check_rate_limit_status()
    
    # Determine overall status
    if any(check["status"] != "healthy" for check in health_status["checks"].values()):
        health_status["status"] = "unhealthy"
    
    return health_status
```

## Future Enhancements

### Phase 1: Additional Data Sources
- Alpha Vantage integration
- IEX Cloud integration
- Yahoo Finance integration
- Custom data feeds

### Phase 2: Advanced Features
- Real-time WebSocket streaming
- Machine learning for data quality
- Advanced anomaly detection
- Data lineage tracking

### Phase 3: Scalability
- Horizontal scaling
- Data partitioning
- Advanced caching strategies
- Multi-region deployment

## Getting Started

### Hybrid Data Ingestion Setup

1. **Setup Configuration**
   ```bash
   # Add Polygon.io API key for historical data
   export POLYGON_API_KEY=your_polygon_api_key_here
   
   # Add Alpaca credentials for real-time trading (if not already set)
   export ALPACA_API_KEY=your_alpaca_api_key_here
   export ALPACA_SECRET_KEY=your_alpaca_secret_key_here
   
   # Configure hybrid strategy
   export ENABLE_HISTORICAL_BACKFILL=true
   export ENABLE_REALTIME_TRADING=true
   ```

2. **Install Dependencies**
   ```bash
   # Historical data processing
   pip install polygon-api-client
   pip install polars
   
   # Real-time trading (already installed)
   pip install alpaca-trade-api
   ```

3. **Run Database Migrations**
   ```bash
   # Create database schemas and tables
   python scripts/setup_databases.py
   
   # Create symbol management tables
   python scripts/05_create_symbol_tables.sql
   ```

4. **Populate Initial Symbols**
   ```bash
   # The system is configured with 100 initial symbols
   # Symbol management is handled by the SymbolService class
   # Automatic delisting detection is enabled
   ```

5. **Start Data Ingestion**
   ```bash
   # Start Prefect server
   prefect server start
   
   # Deploy Polygon.io flows (historical data)
   prefect deployment create polygon_data_flows.py
   
   # Deploy Alpaca flows (real-time trading)
   prefect deployment create alpaca_trading_flows.py
   ```

6. **Monitor Progress**
   - **Historical Data**: Check Prefect UI for Polygon.io backfill flows
   - **Real-Time Trading**: Monitor Alpaca account and order flows
   - **Symbol Management**: Track active/delisted symbols in database
   - **Data Quality**: Review logs for both data sources
   - **Database**: Verify data in PostgreSQL for both sources

### Symbol Management Features

- **Automatic Delisting Detection**: System automatically detects and marks delisted symbols
- **Data Ingestion Status Tracking**: Monitor success/failure of data collection per symbol
- **100 Initial Symbols**: Pre-configured symbol universe for data collection
- **Database-Driven Management**: All symbol operations go through the database
- **No Delisting Reason Tracking**: Simplified approach focusing on active/inactive status

## Troubleshooting

### Common Issues

1. **Rate Limit Exceeded**
   - Check rate limiter configuration
   - Verify API key limits
   - Review call frequency

2. **Data Quality Issues**
   - Check data validation rules
   - Review provider data format
   - Verify timestamp handling

3. **Performance Issues**
   - Check database indexes
   - Review cache configuration
   - Monitor memory usage

### Debug Commands

```bash
# Check data ingestion status
python -m src.services.data_ingestion.health_check

# Validate data quality
python -m src.services.data_ingestion.validate_data

# Test API connectivity
python -m src.services.data_ingestion.test_connectivity
```

This documentation provides a comprehensive foundation for implementing the data ingestion architecture. It can be extended as new data sources are added and the system evolves.