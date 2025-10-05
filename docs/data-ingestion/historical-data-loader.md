# Historical Data Loader

The Historical Data Loader is a comprehensive solution for loading historical market data from Polygon.io into the trading system database. It supports both direct usage and Prefect orchestration.

## Overview

The loader consists of several components:

- **HistoricalDataLoader**: Core class for loading data
- **Prefect Flows**: Orchestrated workflows for data ingestion
- **CLI Script**: Command-line interface for manual operations
- **Database Models**: SQLAlchemy models for market data storage

## Features

- **Batch Processing**: Efficient batch inserts with configurable batch sizes
- **Rate Limiting**: Configurable requests per minute to respect API rate limits
- **Error Handling**: Comprehensive error handling with retry logic
- **Progress Tracking**: Real-time progress monitoring
- **Upsert Logic**: Prevents duplicate data with conflict resolution
- **Timezone Awareness**: All timestamps stored in UTC
- **Symbol Management**: Integration with symbol tracking system

## Quick Start

### Direct Usage

```python
from src.services.data_ingestion.historical_loader import HistoricalDataLoader

# Initialize loader (2 requests per minute for free tier)
loader = HistoricalDataLoader(batch_size=100, requests_per_minute=2)

# Load daily data for a single symbol
records_count = await loader.load_symbol_data(
    symbol="AAPL",
    days_back=30,
    timespan="day",
    multiplier=1
)

# Load hourly data for a single symbol
records_count = await loader.load_symbol_data(
    symbol="AAPL",
    days_back=7,
    timespan="hour",
    multiplier=1
)

# Load 5-minute data for a single symbol
records_count = await loader.load_symbol_data(
    symbol="AAPL",
    days_back=2,
    timespan="minute",
    multiplier=5
)

# Load data for all active symbols
stats = await loader.load_all_symbols_data(
    from_date=date(2023, 1, 1),
    to_date=date(2023, 12, 31)
)
```

### Prefect Flows

```python
from src.services.data_ingestion.flows import (
    daily_data_ingestion_flow,
    backfill_historical_data_flow,
    load_historical_data_flow
)

# Daily data ingestion
result = await daily_data_ingestion_flow(days_back=1)

# Backfill historical data
result = await backfill_historical_data_flow(
    from_date=date(2023, 1, 1),
    to_date=date(2023, 12, 31),
    symbols=["AAPL", "MSFT", "GOOGL"]
)

# Load data with custom parameters
result = await load_historical_data_flow(
    symbols=["AAPL"],
    days_back=365,
    batch_size=50
)
```

### Command Line Interface

```bash
# Load data for a single symbol
python scripts/load_historical_data.py --symbol AAPL --days-back 30

# Load data for all symbols
python scripts/load_historical_data.py --all-symbols --days-back 7

# Load data for specific date range
python scripts/load_historical_data.py --symbol AAPL --from-date 2023-01-01 --to-date 2023-12-31

# Health check
python scripts/load_historical_data.py --health-check

# Load with custom parameters
python scripts/load_historical_data.py --all-symbols --days-back 30 --batch-size 50 --delay 60
```

## Configuration

### Environment Variables

The loader requires the following environment variables:

```bash
# Polygon.io API
POLYGON_API_KEY=your_polygon_api_key
POLYGON_BASE_URL=https://api.polygon.io

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/trading_system
```

### Loader Parameters

- **batch_size**: Number of records to process in each batch (default: 100)
- **requests_per_minute**: Maximum requests per minute (default: 2 for free tier)
- **timespan**: Data granularity ('minute', 'hour', 'day', 'week', 'month', 'quarter', 'year')
- **multiplier**: Number of timespans to aggregate (e.g., 5 with 'minute' = 5-minute bars)
- **max_concurrent_batches**: Maximum number of concurrent batches in Prefect flows (default: 3)
- **symbol_batch_size**: Number of symbols per batch in Prefect flows (default: 50)

## Database Schema

The loader stores data in the `data_ingestion.market_data` table:

```sql
CREATE TABLE data_ingestion.market_data (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    open DECIMAL(15,4),
    high DECIMAL(15,4),
    low DECIMAL(15,4),
    close DECIMAL(15,4),
    volume BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT unique_symbol_timestamp UNIQUE (symbol, timestamp),
    CONSTRAINT positive_prices CHECK (open > 0 AND high > 0 AND low > 0 AND close > 0),
    CONSTRAINT valid_ohlc CHECK (high >= GREATEST(open, close) AND low <= LEAST(open, close))
);
```

## Prefect Flows

### Available Flows

1. **daily_data_ingestion_flow**: Daily data ingestion for all active symbols
2. **backfill_historical_data_flow**: Backfill data for a specific date range
3. **load_historical_data_flow**: General-purpose data loading flow
4. **symbol_health_check_flow**: Check symbol health and detect delisted symbols

### Flow Parameters

- **symbols**: List of symbols to process (None for all active symbols)
- **from_date**: Start date for data loading
- **to_date**: End date for data loading
- **days_back**: Number of days to look back from today
- **batch_size**: Batch size for database inserts
- **delay_between_requests**: Delay between API requests
- **max_concurrent_batches**: Maximum concurrent batches
- **symbol_batch_size**: Number of symbols per batch

## Error Handling

The loader includes comprehensive error handling:

- **API Errors**: Handles Polygon.io API errors with appropriate retry logic
- **Database Errors**: Manages database connection issues and transaction rollbacks
- **Rate Limiting**: Respects API rate limits with configurable delays
- **Data Validation**: Validates OHLCV data before insertion
- **Symbol Status**: Tracks symbol data status for monitoring

## Monitoring and Logging

### Logging

The loader uses structured logging with Loguru:

```python
from loguru import logger

# Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
logger.info("Loading data for symbol: AAPL")
logger.error("Failed to load data: {error}", error=str(e))
```

### Progress Tracking

Monitor loading progress:

```python
# Get loading progress
progress = await loader.get_loading_progress(from_date, to_date)
print(f"Progress: {progress['progress_percent']:.1f}%")

# Check symbol data status
status = await symbol_service.get_symbol_data_status(
    symbol="AAPL",
    date=date.today(),
    data_source="polygon"
)
```

## Performance Optimization

### Batch Processing

- Use appropriate batch sizes (50-200 records)
- Process symbols in batches for large datasets
- Monitor memory usage during batch operations

### Rate Limiting

- Respect Polygon.io rate limits (2 requests/minute for free tier)
- Use `requests_per_minute` parameter to control rate limiting
- Default 30-second delay between requests (60s / 2 requests = 30s)
- Implement exponential backoff for retries

### Database Optimization

- Use upsert logic to prevent duplicates
- Create appropriate indexes on symbol and timestamp
- Monitor database performance during bulk operations

## Troubleshooting

### Common Issues

1. **API Rate Limits**: Increase delays between requests
2. **Database Timeouts**: Reduce batch sizes
3. **Memory Issues**: Process smaller batches
4. **Symbol Not Found**: Check symbol status and validity

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

### Health Checks

Run health checks before loading data:

```python
healthy = await loader.health_check()
if not healthy:
    print("Health check failed - check API and database connections")
```

## Examples

### CLI Usage

```bash
# Load daily data for AAPL (last 30 days, 2 requests/min)
python scripts/load_historical_data.py --symbol AAPL --days-back 30

# Load hourly data for AAPL (last 7 days)
python scripts/load_historical_data.py --symbol AAPL --days-back 7 --timespan hour

# Load 5-minute data for AAPL (last 2 days)
python scripts/load_historical_data.py --symbol AAPL --days-back 2 --timespan minute --multiplier 5

# Load data for all symbols with custom rate limit
python scripts/load_historical_data.py --all-symbols --days-back 7 --requests-per-minute 1

# Load data for specific date range
python scripts/load_historical_data.py --all-symbols --from-date 2023-01-01 --to-date 2023-12-31
```

### Python Usage

See `examples/historical_data_loader_usage.py` for comprehensive usage examples.

## Integration with Prefect

The loader is designed to work seamlessly with Prefect:

```python
from prefect import flow, task
from src.services.data_ingestion.flows import daily_data_ingestion_flow

@flow
async def my_trading_workflow():
    # Load historical data
    data_result = await daily_data_ingestion_flow(days_back=1)
    
    # Continue with other trading operations
    # ...
```

## Best Practices

1. **Start Small**: Test with a few symbols before processing all symbols
2. **Monitor Progress**: Use progress tracking to monitor long-running operations
3. **Handle Errors**: Implement proper error handling and retry logic
4. **Respect Rate Limits**: Use appropriate delays between API requests
5. **Validate Data**: Check data quality after loading
6. **Backup Strategy**: Implement data backup and recovery procedures
7. **Monitoring**: Set up alerts for failed data loads
8. **Documentation**: Document custom configurations and workflows
