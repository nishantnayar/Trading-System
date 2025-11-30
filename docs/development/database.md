# Trading System Database Architecture - Detailed Review

## Overview

This document provides a comprehensive review and detailed analysis of the database architecture for the trading system, including schema design, performance considerations, data flow patterns, and implementation strategies.

**Last Updated**: November 2025  
**Status**: Design Phase  
**Author**: Nishant Nayar

## Database Architecture Design

### 1. Database Distribution Strategy

#### Selected Approach: Separate Databases with Prefect 3.4.14
```
Trading System Database + Prefect Database (Separate)
```

**Benefits:**
- Prefect compatibility with version 3.4.14
- Clean separation of orchestration and trading data
- No workarounds or unsupported configurations
- Future-proof against Prefect updates
- Independent management and monitoring

### 2. Schema Design

#### Core Trading Tables

##### Market Data Table
```sql
CREATE TABLE market_data (
    id BIGSERIAL,
    symbol VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    open DECIMAL(15,4),  -- Increased precision
    high DECIMAL(15,4),
    low DECIMAL(15,4),
    close DECIMAL(15,4),
    volume BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_symbol_timestamp UNIQUE (symbol, timestamp),
    CONSTRAINT positive_prices CHECK (open > 0 AND high > 0 AND low > 0 AND close > 0),
    CONSTRAINT valid_ohlc CHECK (high >= GREATEST(open, close) AND low <= LEAST(open, close))
) PARTITION BY RANGE (timestamp);

-- Indexes for performance
CREATE INDEX idx_market_data_symbol_timestamp ON market_data(symbol, timestamp DESC);
CREATE INDEX idx_market_data_timestamp ON market_data(timestamp DESC);
```

**Design Features:**

1. **Enhanced Constraints**: Unique constraint on (symbol, timestamp)
2. **Increased Precision**: DECIMAL(15,4) for high-priced stocks
3. **Comprehensive Indexing**: Composite indexes for time-series queries
4. **Time-Based Partitioning**: Optimized for large datasets

##### Key Statistics Table

Stores comprehensive financial metrics and fundamental data from Yahoo Finance for stock screening and analysis.

```sql
CREATE TABLE data_ingestion.key_statistics (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    date DATE NOT NULL,
    data_source VARCHAR(50) DEFAULT 'yahoo',
    
    -- Valuation Metrics (9 fields)
    market_cap BIGINT,
    enterprise_value BIGINT,
    trailing_pe NUMERIC(10, 2),
    forward_pe NUMERIC(10, 2),
    peg_ratio NUMERIC(10, 2),
    price_to_book NUMERIC(10, 2),
    price_to_sales NUMERIC(10, 2),
    enterprise_to_revenue NUMERIC(10, 2),
    enterprise_to_ebitda NUMERIC(10, 2),
    
    -- Profitability Metrics (6 fields, stored as decimals: 0.15 = 15%)
    profit_margin NUMERIC(10, 4),
    operating_margin NUMERIC(10, 4),
    return_on_assets NUMERIC(10, 4),
    return_on_equity NUMERIC(10, 4),
    gross_margin NUMERIC(10, 4),
    ebitda_margin NUMERIC(10, 4),
    
    -- Financial Health (10 fields)
    revenue BIGINT,
    revenue_per_share NUMERIC(10, 2),
    earnings_per_share NUMERIC(10, 2),
    total_cash BIGINT,
    total_debt BIGINT,
    debt_to_equity NUMERIC(10, 2),
    current_ratio NUMERIC(10, 2),
    quick_ratio NUMERIC(10, 2),
    free_cash_flow BIGINT,
    operating_cash_flow BIGINT,
    
    -- Growth Metrics (2 fields, stored as decimals)
    revenue_growth NUMERIC(10, 4),
    earnings_growth NUMERIC(10, 4),
    
    -- Trading Metrics (6 fields)
    beta NUMERIC(10, 2),
    fifty_two_week_high NUMERIC(10, 2),
    fifty_two_week_low NUMERIC(10, 2),
    fifty_day_average NUMERIC(10, 2),
    two_hundred_day_average NUMERIC(10, 2),
    average_volume BIGINT,
    
    -- Dividend Metrics (3 fields, stored as decimals)
    dividend_yield NUMERIC(10, 4),
    dividend_rate NUMERIC(10, 2),
    payout_ratio NUMERIC(10, 4),
    
    -- Share Information (6 fields)
    shares_outstanding BIGINT,
    float_shares BIGINT,
    shares_short BIGINT,
    short_ratio NUMERIC(10, 2),
    held_percent_insiders NUMERIC(10, 4),
    held_percent_institutions NUMERIC(10, 4),
    
    -- Metadata
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    CONSTRAINT key_statistics_symbol_date_source_key UNIQUE (symbol, date, data_source),
    CONSTRAINT key_statistics_symbol_fkey FOREIGN KEY (symbol) 
        REFERENCES data_ingestion.symbols(symbol) ON DELETE CASCADE
);

-- Performance indexes
CREATE INDEX idx_key_statistics_symbol ON data_ingestion.key_statistics(symbol);
CREATE INDEX idx_key_statistics_date ON data_ingestion.key_statistics(date);
CREATE INDEX idx_key_statistics_symbol_date ON data_ingestion.key_statistics(symbol, date);

-- Screening indexes for common queries
CREATE INDEX idx_key_statistics_valuation 
    ON data_ingestion.key_statistics(trailing_pe, price_to_book, market_cap);
CREATE INDEX idx_key_statistics_profitability 
    ON data_ingestion.key_statistics(return_on_equity, profit_margin);

-- Auto-update trigger
CREATE OR REPLACE FUNCTION update_key_statistics_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_key_statistics_updated_at
    BEFORE UPDATE ON data_ingestion.key_statistics
    FOR EACH ROW
    EXECUTE FUNCTION update_key_statistics_updated_at();
```

**Design Features:**

1. **Comprehensive Metrics**: 50+ financial indicators covering valuation, profitability, growth, and trading
2. **Screening Optimization**: Dedicated indexes for common stock screening queries
3. **Decimal Precision**: NUMERIC(10,4) for percentage values, NUMERIC(10,2) for ratios
4. **Data Integrity**: Unique constraint on (symbol, date, data_source) prevents duplicates
5. **Automatic Updates**: Trigger maintains updated_at timestamp
6. **Cascade Delete**: Foreign key ensures referential integrity with symbols table

**Use Cases:**

- Stock screening and filtering based on fundamental metrics
- Historical fundamental analysis and trend tracking
- Portfolio fundamental assessment
- Value/growth stock identification
- Risk assessment based on financial health metrics

**Migration Location**: `scripts/09_create_key_statistics_table.sql`  
**SQLAlchemy Model**: `src/shared/database/models/key_statistics.py`

##### Institutional Holders Table

Stores institutional ownership data from Yahoo Finance, tracking major shareholders like investment firms, mutual funds, and pension funds.

```sql
CREATE TABLE data_ingestion.institutional_holders (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(10) NOT NULL,
    date_reported DATE NOT NULL,
    holder_name VARCHAR(255) NOT NULL,
    shares BIGINT,
    value BIGINT,
    percent_held NUMERIC(10, 4),
    data_source VARCHAR(50) DEFAULT 'yahoo',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT institutional_holders_symbol_holder_date_key UNIQUE (symbol, holder_name, date_reported),
    CONSTRAINT institutional_holders_symbol_fkey FOREIGN KEY (symbol) 
        REFERENCES data_ingestion.symbols(symbol) ON DELETE CASCADE
);

-- Performance indexes
CREATE INDEX idx_institutional_holders_symbol ON data_ingestion.institutional_holders(symbol);
CREATE INDEX idx_institutional_holders_date ON data_ingestion.institutional_holders(date_reported);
CREATE INDEX idx_institutional_holders_shares ON data_ingestion.institutional_holders(symbol, shares DESC);
CREATE INDEX idx_institutional_holders_percent ON data_ingestion.institutional_holders(symbol, percent_held DESC);
```

**Design Features:**

1. **Ownership Tracking**: Captures major institutional shareholders and their positions
2. **Historical Data**: Tracks ownership changes over time via date_reported
3. **Top Holders Optimization**: Indexes for quickly finding largest shareholders
4. **Unique Constraint**: Prevents duplicates based on (symbol, holder_name, date_reported)
5. **Value Tracking**: Stores both share count and dollar value of holdings

**Use Cases:**

- Identifying major shareholders and ownership concentration
- Tracking institutional buying/selling trends
- Analyzing ownership structure for risk assessment
- Monitoring whale movements and institutional sentiment

**Migration Location**: `scripts/10_create_institutional_holders_table.sql`  
**SQLAlchemy Model**: `src/shared/database/models/institutional_holders.py`

#### Analytics Schema Tables

##### Technical Indicators Tables

Technical indicators are calculated/derived metrics from market data, used across the system for:
- **Stock Screening**: Fast filtering by RSI, moving averages, volatility
- **Analysis Page**: Displaying current indicator values
- **Strategy Engine**: Signal generation based on technical analysis
- **Backtesting**: Historical indicator values for strategy testing
- **Portfolio Analysis**: Performance metrics and risk assessment

**Schema Decision**: Stored in `analytics` schema (not `data_ingestion`) because they are calculated/derived metrics, not raw ingested data.

**Data Source**: Technical indicators are calculated using **only Yahoo Finance data** (`data_source = 'yahoo'`) from the `market_data` table. This ensures:
- Consistent data source for all calculations
- Single source of truth for technical analysis
- Avoids mixing data from different providers (Yahoo vs Polygon)
- Yahoo data is typically more complete for daily OHLCV data

**Architecture**: Hybrid approach with two tables:
1. **`technical_indicators_latest`**: Latest values for fast screening queries
2. **`technical_indicators`**: Historical time-series for analysis and backtesting

**Latest Values Table** (for fast screening):
```sql
CREATE TABLE analytics.technical_indicators_latest (
    symbol VARCHAR(20) PRIMARY KEY,
    calculated_date DATE NOT NULL,
    
    -- Moving Averages
    sma_20 NUMERIC(15,4),
    sma_50 NUMERIC(15,4),
    sma_200 NUMERIC(15,4),
    ema_12 NUMERIC(15,4),
    ema_26 NUMERIC(15,4),
    ema_50 NUMERIC(15,4),
    
    -- Momentum Indicators
    rsi NUMERIC(5,2),  -- 0-100
    rsi_14 NUMERIC(5,2),  -- Explicit 14-period RSI
    
    -- MACD
    macd_line NUMERIC(15,4),
    macd_signal NUMERIC(15,4),
    macd_histogram NUMERIC(15,4),
    
    -- Bollinger Bands
    bb_upper NUMERIC(15,4),
    bb_middle NUMERIC(15,4),
    bb_lower NUMERIC(15,4),
    bb_position NUMERIC(5,4),  -- Position within bands (0-1)
    bb_width NUMERIC(10,4),  -- Band width as percentage
    
    -- Volatility & Price Changes
    volatility_20 NUMERIC(5,2),  -- Annualized volatility percentage
    price_change_1d NUMERIC(5,2),
    price_change_5d NUMERIC(5,2),
    price_change_30d NUMERIC(5,2),
    
    -- Volume Indicators
    avg_volume_20 BIGINT,
    current_volume BIGINT,
    
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT technical_indicators_latest_symbol_fkey 
        FOREIGN KEY (symbol) 
        REFERENCES data_ingestion.symbols(symbol) 
        ON DELETE CASCADE
);
```

**Time-Series Table** (for historical analysis):
```sql
CREATE TABLE analytics.technical_indicators (
    id BIGSERIAL PRIMARY KEY,
    symbol VARCHAR(20) NOT NULL,
    date DATE NOT NULL,
    
    -- Same indicator fields as latest table
    -- Moving Averages: sma_20, sma_50, sma_200, ema_12, ema_26, ema_50
    -- Momentum: rsi, rsi_14
    -- MACD: macd_line, macd_signal, macd_histogram
    -- Bollinger Bands: bb_upper, bb_middle, bb_lower, bb_position, bb_width
    -- Volatility & Price Changes: volatility_20, price_change_1d, price_change_5d, price_change_30d
    -- Volume: avg_volume_20, current_volume
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_symbol_date UNIQUE (symbol, date),
    CONSTRAINT technical_indicators_symbol_fkey 
        FOREIGN KEY (symbol) 
        REFERENCES data_ingestion.symbols(symbol) 
        ON DELETE CASCADE
);
```

**Design Features:**

1. **Hybrid Storage**: Latest values for fast queries + time-series for historical analysis
2. **Yahoo Data Only**: Calculations use only `data_source = 'yahoo'` from market_data table
3. **Performance Optimization**: Indexes on commonly filtered fields (RSI, SMA, volatility)
4. **Calculation Fallback**: UI can calculate on-the-fly if database values are missing
5. **Daily Updates**: Calculated after market close via scheduled Prefect flows
6. **Incremental Updates**: Only calculates for new market data, skips if already calculated

**Use Cases:**

- Fast stock screening by technical criteria (RSI < 30, price above SMA 50, etc.)
- Displaying current indicator values in Analysis page
- Historical backtesting with time-series indicator data
- Strategy signal generation based on technical analysis
- Portfolio risk assessment using volatility metrics

**Performance Benefits:**

| Approach | Symbols/Second | Storage | Scalability |
|----------|---------------|---------|-------------|
| **On-the-fly Calculation** | 0.5-1 | None | Limited (50 symbols) |
| **Database Storage** | 10-50 | ~50-100 bytes/symbol/day | Excellent (1000+ symbols) |

**Migration Location**: `scripts/17_create_technical_indicators_tables.sql`  
**SQLAlchemy Model**: `src/shared/database/models/technical_indicators.py` (Pending)  
**Calculation Service**: `src/services/analytics/indicator_calculator.py` (Pending)

##### Orders Table
```sql
CREATE TYPE order_side AS ENUM ('buy', 'sell');
CREATE TYPE order_type AS ENUM ('market', 'limit', 'stop', 'stop_limit');
CREATE TYPE order_status AS ENUM ('pending', 'submitted', 'filled', 'partially_filled', 'cancelled', 'rejected');
CREATE TYPE time_in_force AS ENUM ('day', 'gtc', 'ioc', 'fok');

CREATE TABLE orders (
    id BIGSERIAL PRIMARY KEY,
    order_id VARCHAR(100) UNIQUE NOT NULL,
    account_id VARCHAR(50) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    side order_side NOT NULL,
    order_type order_type NOT NULL,
    quantity DECIMAL(15,4) NOT NULL,
    price DECIMAL(15,4),
    stop_price DECIMAL(15,4),
    time_in_force time_in_force DEFAULT 'day',
    status order_status NOT NULL DEFAULT 'pending',
    strategy VARCHAR(100),
    session_id VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT positive_quantity CHECK (quantity > 0),
    CONSTRAINT valid_price CHECK (price IS NULL OR price > 0),
    CONSTRAINT valid_stop_price CHECK (stop_price IS NULL OR stop_price > 0)
);

-- Indexes
CREATE INDEX idx_orders_symbol_status ON orders(symbol, status);
CREATE INDEX idx_orders_strategy ON orders(strategy);
CREATE INDEX idx_orders_created_at ON orders(created_at DESC);
CREATE INDEX idx_orders_account_id ON orders(account_id);
```

##### Trades Table
```sql
CREATE TABLE trades (
    id BIGSERIAL PRIMARY KEY,
    trade_id VARCHAR(100) UNIQUE NOT NULL,
    order_id VARCHAR(100) REFERENCES orders(order_id),
    account_id VARCHAR(50) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    quantity DECIMAL(15,4) NOT NULL,
    price DECIMAL(15,4) NOT NULL,
    commission DECIMAL(10,4) DEFAULT 0,
    executed_at TIMESTAMP WITH TIME ZONE NOT NULL,
    settlement_date DATE,
    strategy VARCHAR(100),
    trade_type VARCHAR(20), -- 'opening', 'closing', 'partial'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT positive_quantity CHECK (quantity > 0),
    CONSTRAINT positive_price CHECK (price > 0),
    CONSTRAINT non_negative_commission CHECK (commission >= 0)
);

-- Indexes
CREATE INDEX idx_trades_symbol_executed_at ON trades(symbol, executed_at DESC);
CREATE INDEX idx_trades_strategy ON trades(strategy);
CREATE INDEX idx_trades_account_id ON trades(account_id);
```

##### Positions Table
```sql
CREATE TABLE positions (
    id BIGSERIAL PRIMARY KEY,
    account_id VARCHAR(50) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    quantity DECIMAL(15,4) NOT NULL,
    avg_price DECIMAL(15,4) NOT NULL,
    market_value DECIMAL(15,4),
    unrealized_pnl DECIMAL(15,4),
    realized_pnl DECIMAL(15,4) DEFAULT 0,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Constraints
    CONSTRAINT unique_account_symbol UNIQUE (account_id, symbol),
    CONSTRAINT non_negative_quantity CHECK (quantity >= 0)
);

-- Indexes
CREATE INDEX idx_positions_account_id ON positions(account_id);
CREATE INDEX idx_positions_symbol ON positions(symbol);
CREATE INDEX idx_positions_last_updated ON positions(last_updated DESC);
```

### 3. Database Performance Considerations

#### Indexing Strategy

##### Comprehensive Indexing Design
```sql
-- Market Data Indexes
CREATE INDEX idx_market_data_symbol_timestamp ON market_data(symbol, timestamp DESC);
CREATE INDEX idx_market_data_timestamp ON market_data(timestamp DESC);
CREATE INDEX idx_market_data_symbol ON market_data(symbol);

-- Trading Indexes
CREATE INDEX idx_orders_symbol_status ON orders(symbol, status);
CREATE INDEX idx_orders_strategy ON orders(strategy);
CREATE INDEX idx_orders_created_at ON orders(created_at DESC);
CREATE INDEX idx_orders_account_id ON orders(account_id);

CREATE INDEX idx_trades_symbol_executed_at ON trades(symbol, executed_at DESC);
CREATE INDEX idx_trades_strategy ON trades(strategy);
CREATE INDEX idx_trades_account_id ON trades(account_id);

-- Position Indexes
CREATE INDEX idx_positions_account_id ON positions(account_id);
CREATE INDEX idx_positions_symbol ON positions(symbol);

-- Logging Indexes
CREATE INDEX idx_system_logs_timestamp ON system_logs(timestamp DESC);
CREATE INDEX idx_system_logs_service_timestamp ON system_logs(service, timestamp DESC);
CREATE INDEX idx_system_logs_level_timestamp ON system_logs(level, timestamp DESC);
CREATE INDEX idx_system_logs_correlation ON system_logs(correlation_id);
CREATE INDEX idx_system_logs_event_type ON system_logs(event_type);

-- Performance Logs Indexes
CREATE INDEX idx_performance_logs_service_timestamp ON performance_logs(service, timestamp DESC);
CREATE INDEX idx_performance_logs_operation ON performance_logs(operation);
```

#### Partitioning Strategy

##### Time-Based Partitioning for Large Tables
```sql
-- Partition market_data by year
CREATE TABLE market_data (
    id BIGSERIAL,
    symbol VARCHAR(20) NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    open DECIMAL(15,4),
    high DECIMAL(15,4),
    low DECIMAL(15,4),
    close DECIMAL(15,4),
    volume BIGINT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    PRIMARY KEY (id, timestamp)
) PARTITION BY RANGE (timestamp);

-- Create partitions for each year
CREATE TABLE market_data_y2024 PARTITION OF market_data
FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

CREATE TABLE market_data_y2025 PARTITION OF market_data
FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');

-- Auto-create future partitions
CREATE OR REPLACE FUNCTION create_monthly_partition(table_name text, start_date date)
RETURNS void AS $$
DECLARE
    partition_name text;
    end_date date;
BEGIN
    partition_name := table_name || '_' || to_char(start_date, 'YYYY_MM');
    end_date := start_date + interval '1 month';
    
    EXECUTE format('CREATE TABLE %I PARTITION OF %I FOR VALUES FROM (%L) TO (%L)',
                   partition_name, table_name, start_date, end_date);
END;
$$ LANGUAGE plpgsql;
```

### 4. Data Consistency and Concurrency

#### Transaction Management

##### Transaction Strategy Design
```python
# src/shared/database/transaction_manager.py
from contextlib import contextmanager
from sqlalchemy.orm import Session
from sqlalchemy import text

class TransactionManager:
    def __init__(self, engine):
        self.engine = engine
    
    @contextmanager
    def transaction(self, isolation_level='READ_COMMITTED'):
        """Context manager for database transactions"""
        connection = self.engine.connect()
        transaction = connection.begin()
        
        try:
            # Set isolation level
            connection.execute(text(f"SET TRANSACTION ISOLATION LEVEL {isolation_level}"))
            
            session = Session(bind=connection)
            yield session
            
            transaction.commit()
        except Exception as e:
            transaction.rollback()
            raise e
        finally:
            session.close()
            connection.close()
    
    @contextmanager
    def read_only_transaction(self):
        """Read-only transaction for analytics queries"""
        with self.transaction('READ_COMMITTED') as session:
            yield session
```

#### Optimistic Locking Implementation
```python
# src/shared/database/optimistic_locking.py
from sqlalchemy import Column, Integer, DateTime
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class OptimisticLockingMixin:
    version = Column(Integer, default=1, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def update_with_version(self, session, **kwargs):
        """Update with optimistic locking"""
        current_version = self.version
        self.version += 1
        
        result = session.query(self.__class__).filter(
            self.__class__.id == self.id,
            self.__class__.version == current_version
        ).update(kwargs)
        
        if result == 0:
            raise OptimisticLockingError("Record was modified by another process")
        
        return result
```

### 5. Data Synchronization Patterns

#### Event-Driven Synchronization

##### Event Bus Design
```python
# src/shared/events/data_sync.py
import redis
import json
from typing import Dict, Any, List
from datetime import datetime

class DataSyncEventBus:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
        self.pubsub = self.redis.pubsub()
    
    def publish_trade_event(self, trade_data: Dict[str, Any]):
        """Publish trade execution event"""
        event = {
            'type': 'trade_executed',
            'service': 'execution',
            'data': trade_data,
            'timestamp': datetime.utcnow().isoformat(),
            'correlation_id': trade_data.get('trade_id')
        }
        
        self.redis.publish('data_sync:trades', json.dumps(event))
    
    def publish_market_data_event(self, market_data: Dict[str, Any]):
        """Publish market data update event"""
        event = {
            'type': 'market_data_updated',
            'service': 'data_ingestion',
            'data': market_data,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.redis.publish('data_sync:market_data', json.dumps(event))
    
    def subscribe_to_events(self, event_types: List[str], callback):
        """Subscribe to data sync events"""
        for event_type in event_types:
            self.pubsub.subscribe(f'data_sync:{event_type}')
        
        for message in self.pubsub.listen():
            if message['type'] == 'message':
                event = json.loads(message['data'])
                callback(event)
```

##### Data Synchronization Service
```python
# src/shared/data_sync/synchronizer.py
class DataSynchronizer:
    def __init__(self, event_bus: DataSyncEventBus, analytics_db: Engine):
        self.event_bus = event_bus
        self.analytics_db = analytics_db
        self.setup_event_handlers()
    
    def setup_event_handlers(self):
        """Setup event handlers for data synchronization"""
        self.event_bus.subscribe_to_events(
            ['trades', 'market_data', 'positions'],
            self.handle_data_event
        )
    
    def handle_data_event(self, event: Dict[str, Any]):
        """Handle incoming data synchronization events"""
        event_type = event['type']
        
        if event_type == 'trade_executed':
            self.sync_trade_data(event['data'])
        elif event_type == 'market_data_updated':
            self.sync_market_data(event['data'])
        elif event_type == 'position_updated':
            self.sync_position_data(event['data'])
    
    def sync_trade_data(self, trade_data: Dict[str, Any]):
        """Sync trade data to analytics database"""
        with self.analytics_db.connect() as conn:
            # Update portfolio summary
            conn.execute(text("""
                INSERT INTO portfolio_summary (account_id, symbol, total_value, realized_pnl)
                VALUES (:account_id, :symbol, :total_value, :realized_pnl)
                ON CONFLICT (account_id, symbol) 
                DO UPDATE SET 
                    total_value = portfolio_summary.total_value + :total_value,
                    realized_pnl = portfolio_summary.realized_pnl + :realized_pnl,
                    last_updated = NOW()
            """), trade_data)
            
            # Update performance metrics
            conn.execute(text("""
                INSERT INTO performance_metrics (strategy, date, total_trades, win_rate)
                VALUES (:strategy, CURRENT_DATE, 1, :win_rate)
                ON CONFLICT (strategy, date)
                DO UPDATE SET 
                    total_trades = performance_metrics.total_trades + 1,
                    win_rate = (performance_metrics.win_rate * performance_metrics.total_trades + :win_rate) / (performance_metrics.total_trades + 1)
            """), trade_data)
```

### 6. Database Monitoring and Maintenance

#### Performance Monitoring
```python
# src/shared/monitoring/db_monitoring.py
class DatabaseMonitoring:
    def __init__(self, db_connections: Dict[str, Engine]):
        self.connections = db_connections
        self.metrics = {}
    
    def track_query_performance(self, service: str, query: str, execution_time: float):
        """Track query performance metrics"""
        if service not in self.metrics:
            self.metrics[service] = {
                'query_count': 0,
                'total_time': 0,
                'slow_queries': []
            }
        
        self.metrics[service]['query_count'] += 1
        self.metrics[service]['total_time'] += execution_time
        
        if execution_time > 1.0:  # 1 second threshold
            self.metrics[service]['slow_queries'].append({
                'query': query,
                'execution_time': execution_time,
                'timestamp': datetime.utcnow()
            })
    
    def get_performance_summary(self):
        """Get database performance summary"""
        summary = {}
        for service, metrics in self.metrics.items():
            summary[service] = {
                'avg_query_time': metrics['total_time'] / metrics['query_count'] if metrics['query_count'] > 0 else 0,
                'total_queries': metrics['query_count'],
                'slow_query_count': len(metrics['slow_queries'])
            }
        return summary
```

#### Automated Maintenance
```python
# src/shared/maintenance/db_maintenance.py
class DatabaseMaintenance:
    def __init__(self, db_connections: Dict[str, Engine]):
        self.connections = db_connections
    
    def run_vacuum_analyze(self, service: str):
        """Run VACUUM ANALYZE on service database"""
        with self.connections[service].connect() as conn:
            conn.execute(text("VACUUM ANALYZE"))
    
    def cleanup_old_logs(self, service: str, retention_days: int = 30):
        """Clean up old log entries"""
        with self.connections[service].connect() as conn:
            # Archive old logs
            conn.execute(text("""
                INSERT INTO archived_system_logs 
                SELECT * FROM system_logs 
                WHERE created_at < NOW() - INTERVAL '%s days'
            """), (retention_days,))
            
            # Delete archived logs
            conn.execute(text("""
                DELETE FROM system_logs 
                WHERE created_at < NOW() - INTERVAL '%s days'
            """), (retention_days,))
    
    def update_statistics(self, service: str):
        """Update database statistics"""
        with self.connections[service].connect() as conn:
            conn.execute(text("ANALYZE"))
```

### 7. Security Considerations

#### Database Security Implementation
```python
# src/shared/security/db_security.py
class DatabaseSecurity:
    def __init__(self, db_connections: Dict[str, Engine]):
        self.connections = db_connections
    
    def setup_row_level_security(self, service: str):
        """Setup row-level security for multi-tenant data"""
        with self.connections[service].connect() as conn:
            # Enable RLS on sensitive tables
            conn.execute(text("ALTER TABLE trades ENABLE ROW LEVEL SECURITY"))
            conn.execute(text("ALTER TABLE positions ENABLE ROW LEVEL SECURITY"))
            conn.execute(text("ALTER TABLE orders ENABLE ROW LEVEL SECURITY"))
            
            # Create policies
            conn.execute(text("""
                CREATE POLICY trades_account_policy ON trades
                FOR ALL TO trading_app
                USING (account_id = current_setting('app.current_account_id'))
            """))
    
    def audit_data_access(self, service: str, user_id: str, table_name: str, operation: str):
        """Audit data access for compliance"""
        with self.connections[service].connect() as conn:
            conn.execute(text("""
                INSERT INTO audit_log (user_id, table_name, operation, timestamp)
                VALUES (:user_id, :table_name, :operation, NOW())
            """), {
                'user_id': user_id,
                'table_name': table_name,
                'operation': operation
            })
```

## SQLAlchemy ORM and Session Management

### Overview

The trading system uses SQLAlchemy ORM (Object-Relational Mapping) to interact with PostgreSQL. This provides a Pythonic interface to the database while maintaining type safety and preventing SQL injection attacks.

### Declarative Base

All database models inherit from a common declarative base:

```python
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# All models inherit from Base
class MarketData(Base):
    __tablename__ = "market_data"
    __table_args__ = {'schema': 'data_ingestion'}
    # ... column definitions
```

**Purpose:**
- Provides metadata registry for all tables
- Enables ORM mapping between Python classes and database tables
- Tracks relationships and foreign keys
- Provides query interface

### Session Management Design

#### Automated Session Management

The system uses **context managers** for automatic session lifecycle management:

```python
# Write operations
with db_transaction() as session:
    order = Order(symbol='AAPL', quantity=100)
    session.add(order)
    # Auto-commit on success, auto-rollback on error

# Read operations
with db_readonly_session() as session:
    results = session.query(MarketData).filter_by(symbol='AAPL').all()
```

#### Two Session Types

**1. Transaction Session (`db_transaction`)**

For write operations that modify data:

```python
@contextmanager
def db_transaction() -> Generator[Session, None, None]:
    """
    Database transaction context manager with automatic commit/rollback
    
    Features:
    - Automatic commit on success
    - Automatic rollback on error
    - Connection pooling
    - Error logging
    - Always closes session
    
    Usage:
        with db_transaction() as session:
            order = Order(symbol='AAPL', quantity=100)
            session.add(order)
    
    Use cases:
    - Creating orders, trades, positions
    - Updating risk limits
    - Recording strategy signals
    - Any data modification
    """
```

**2. Read-Only Session (`db_readonly_session`)**

For read operations that don't modify data:

```python
@contextmanager
def db_readonly_session() -> Generator[Session, None, None]:
    """
    Read-only database session for analytics and reporting
    
    Features:
    - No write operations allowed
    - Optimized for read performance
    - No transaction overhead
    - Connection pooling
    
    Usage:
        with db_readonly_session() as session:
            data = session.query(MarketData).filter(...).all()
    
    Use cases:
    - Analytics queries
    - Dashboard data
    - Reporting
    - Backtesting
    """
```

**Performance Benefits of Read-Only Sessions:**
- No Write-Ahead Log (WAL) overhead
- Reduced locking overhead
- PostgreSQL can optimize query execution
- Lower resource consumption
- Can leverage read replicas (future scaling)

#### Schema Handling

Schemas are specified in model definitions using `__table_args__`:

```python
class MarketData(Base):
    __tablename__ = "market_data"
    __table_args__ = {'schema': 'data_ingestion'}  # Explicit schema
    
    id = Column(BigInteger, primary_key=True)
    symbol = Column(String(20), nullable=False)
    # ...
```

**Benefits:**
- Schema is explicit in code
- No connection string magic
- Works with automated session management
- Maintains schema isolation

#### Error Handling Strategy

The session manager implements comprehensive error handling:

```python
try:
    yield session
    session.commit()
    logger.debug("Transaction committed successfully")
    
except IntegrityError as e:
    session.rollback()
    logger.error(f"Database integrity error: {e}")
    raise  # Constraint violations, duplicate keys
    
except OperationalError as e:
    session.rollback()
    logger.error(f"Database operational error: {e}")
    raise  # Connection issues, timeouts
    
except DataError as e:
    session.rollback()
    logger.error(f"Database data error: {e}")
    raise  # Invalid data types, out of range
    
except Exception as e:
    session.rollback()
    logger.error(f"Unexpected database error: {e}")
    raise
    
finally:
    session.close()  # Always close
```

**Error Categories:**
- **IntegrityError** - Constraint violations, duplicate keys
- **OperationalError** - Connection problems, timeouts
- **DataError** - Invalid data types, out of range values
- **ProgrammingError** - SQL syntax errors

**Error Handling Benefits:**
- Centralized error logging (all DB errors captured)
- Categorized errors for different handling strategies
- Exceptions re-raised for caller to handle
- Stack traces preserved for debugging
- Monitoring and alerting ready

#### Connection Pooling

Connection pooling is configured in `src/config/database.py`:

```python
engine = create_engine(
    database_url,
    poolclass=QueuePool,
    pool_size=10,         # Keep 10 connections open
    max_overflow=20,      # Allow 20 more if needed
    pool_timeout=30,      # Wait 30s for available connection
    pool_recycle=3600     # Recycle connections after 1 hour
)
```

**Benefits:**
- Reuses existing connections (faster)
- Prevents connection exhaustion
- Automatic connection management
- Configurable pool size per workload

### Usage Examples

#### Example 1: Create Order (Write Operation)

```python
from src.services.execution.models import Order, OrderSide
from src.shared.database.base import db_transaction

def create_order(symbol: str, quantity: int, price: float):
    """Create a new trading order"""
    with db_transaction() as session:
        order = Order(
            order_id=generate_id(),
            account_id='ACC123',
            symbol=symbol,
            quantity=quantity,
            price=price,
            side=OrderSide.BUY,
            status=OrderStatus.PENDING
        )
        session.add(order)
        # Auto-commit on success
        return order.order_id
```

#### Example 2: Query Market Data (Read Operation)

```python
from src.services.data_ingestion.models import MarketData
from src.shared.database.base import db_readonly_session
from datetime import datetime, timedelta

def get_market_history(symbol: str, days: int):
    """Get historical market data"""
    with db_readonly_session() as session:
        cutoff = datetime.now() - timedelta(days=days)
        return session.query(MarketData)\
            .filter(MarketData.symbol == symbol)\
            .filter(MarketData.timestamp >= cutoff)\
            .order_by(MarketData.timestamp.desc())\
            .all()
```

#### Example 3: Complex Transaction (Multiple Operations)

```python
from src.shared.database.base import db_transaction

def execute_trade(order_id: str, execution_price: float):
    """Execute a trade and update related records"""
    with db_transaction() as session:
        # 1. Get and update order
        order = session.query(Order).filter_by(order_id=order_id).first()
        if not order:
            raise ValueError(f"Order {order_id} not found")
        
        order.status = OrderStatus.FILLED
        order.updated_at = datetime.now(timezone.utc)
        
        # 2. Create trade record
        trade = Trade(
            trade_id=generate_id(),
            order_id=order_id,
            account_id=order.account_id,
            symbol=order.symbol,
            quantity=order.quantity,
            price=execution_price,
            executed_at=datetime.now(timezone.utc)
        )
        session.add(trade)
        
        # 3. Update or create position
        position = session.query(Position).filter_by(
            account_id=order.account_id,
            symbol=order.symbol
        ).first()
        
        if position:
            # Update existing position
            position.quantity += order.quantity
            position.avg_price = calculate_avg_price(position, order)
            position.last_updated = datetime.now(timezone.utc)
        else:
            # Create new position
            position = Position(
                account_id=order.account_id,
                symbol=order.symbol,
                quantity=order.quantity,
                avg_price=execution_price
            )
            session.add(position)
        
        # All operations committed together or all rolled back
        return trade.trade_id
```

#### Example 4: Analytics Query (Aggregation)

```python
from src.shared.database.base import db_readonly_session
from sqlalchemy import func

def get_portfolio_summary(account_id: str):
    """Get aggregated portfolio metrics"""
    with db_readonly_session() as session:
        summary = session.query(
            Position.symbol,
            Position.quantity,
            Position.avg_price,
            Position.unrealized_pnl,
            func.sum(Position.market_value).label('total_value')
        )\
        .filter(Position.account_id == account_id)\
        .filter(Position.quantity > 0)\
        .group_by(Position.symbol)\
        .all()
        
        return summary
```

### Design Principles

| Principle | Implementation | Benefit |
|-----------|----------------|---------|
| **Automation** | Context managers | Prevents connection leaks |
| **Separation** | Read/Write sessions | Performance optimization |
| **Explicitness** | Schema in models | Clear and maintainable |
| **Simplicity** | Single database | No distributed transactions |
| **Observability** | Error logging | Monitoring and debugging |
| **Safety** | Auto-rollback | Data consistency |
| **Efficiency** | Connection pooling | Resource optimization |

### Transaction Isolation

The system uses PostgreSQL's default isolation level:

- **Isolation Level**: READ COMMITTED
- **Behavior**: Queries see only committed data
- **Concurrency**: High (minimal locking)
- **Use Case**: Suitable for most trading operations

For operations requiring stronger guarantees:

```python
from sqlalchemy import text

with db_transaction() as session:
    # Set higher isolation level if needed
    session.execute(text("SET TRANSACTION ISOLATION LEVEL SERIALIZABLE"))
    # Your operations here
```

### Best Practices

**DO:**
- ✅ Use `db_transaction()` for all write operations
- ✅ Use `db_readonly_session()` for analytics and reporting
- ✅ Keep transactions short and focused
- ✅ Handle exceptions at the application level
- ✅ Use connection pooling (already configured)
- ✅ Specify schema in model definitions

**DON'T:**
- ❌ Mix read and write sessions (use write session if needed)
- ❌ Keep transactions open for long periods
- ❌ Catch and ignore database errors
- ❌ Create sessions manually (use context managers)
- ❌ Use distributed transactions (not needed)
- ❌ Modify read-only session data

### Advanced Features

#### Manual Session Management (Advanced)

For cases requiring explicit control:

```python
from src.shared.database.base import get_session

def advanced_operation():
    """Advanced use case with manual session management"""
    session = get_session()
    try:
        # Your operations
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
```

⚠️ **Warning**: Manual session management requires careful handling. Prefer context managers.

#### Nested Transactions (Savepoints)

For complex operations requiring partial rollback:

```python
with db_transaction() as session:
    order = Order(...)
    session.add(order)
    
    # Create savepoint
    savepoint = session.begin_nested()
    try:
        # Risky operation
        risky_update()
        savepoint.commit()
    except Exception:
        # Rollback to savepoint, main transaction continues
        savepoint.rollback()
```

---

## Database Setup Options

### Option 1: Python Script (Automated)
Run the database setup script:

```bash
python scripts/setup_databases.py
```

This script will:
- Create the `Prefect` database
- Create service-specific schemas in `trading_system`
- Configure Prefect to use PostgreSQL
- Note: Prefect will automatically initialize its tables when the server starts

### Option 2: SQL Scripts (Manual)
For more control or if you prefer SQL, run the scripts manually:

```bash
# 1. Create databases and schemas
psql -U postgres -h localhost -p 5432 -f scripts/01_create_databases.sql

# 2. Create core tables
psql -U postgres -h localhost -p 5432 -d trading_system -f scripts/02_create_core_tables.sql

# 3. Create indexes
psql -U postgres -h localhost -p 5432 -d trading_system -f scripts/03_create_indexes.sql

# 4. Verify setup
psql -U postgres -h localhost -p 5432 -d trading_system -f scripts/04_verify_setup.sql
```

The SQL scripts provide:
- Simple, transparent database setup
- Easy to modify and customize
- Clear error messages
- Step-by-step verification

### What Gets Created

#### Databases
- `trading_system` - Main trading database
- `Prefect` - Prefect orchestration database

#### Schemas in trading_system
- `data_ingestion` - Market data and quality logs
- `strategy_engine` - Strategies, signals, and performance
- `execution` - Orders, trades, and positions
- `risk_management` - Risk limits and events
- `analytics` - Portfolio and performance analytics
- `notification` - Alert configurations and logs
- `logging` - System and performance logs
- `shared` - Common utilities and configuration

#### Core Tables
- **Market Data**: `market_data`, `key_statistics`, `institutional_holders`, `data_quality_logs`
- **Trading**: `orders`, `trades`, `positions`
- **Strategy**: `strategies`, `strategy_signals`, `strategy_performance`
- **Risk**: `risk_limits`, `risk_events`
- **Analytics**: `portfolio_summary`, `performance_metrics`
- **Notification**: `notification_configs`, `notification_logs`
- **Logging**: `system_logs`, `performance_logs`
- **Shared**: `audit_log`, `system_config`

## Implementation Strategy

### Database Architecture Decision: Separate Databases

#### **Prefect 3.4.14 Integration**
Given Prefect 3.4.14's limitations with custom schemas, we're implementing a **separate database strategy**:

```
┌─────────────────────────────────────────────────────────┐
│                PostgreSQL Instance                      │
├─────────────────────────────────────────────────────────┤
│  trading_system database  │  prefect database          │
│  ├── data_ingestion       │  ├── public schema         │
│  ├── strategy_engine      │  │   ├── flow_runs         │
│  ├── execution            │  │   ├── task_runs         │
│  ├── risk_management      │  │   ├── deployments       │
│  ├── analytics            │  │   ├── work_pools        │
│  ├── notification         │  │   ├── blocks            │
│  └── logging              │  │   └── (other Prefect)   │
└─────────────────────────────────────────────────────────┘
```

#### **Why Separate Databases:**
- **Prefect Compatibility**: Works exactly as Prefect 3.4.14 expects
- **Clean Architecture**: Clear separation of orchestration and trading data
- **No Workarounds**: No hacks or unsupported configurations
- **Future-Proof**: Compatible with Prefect updates
- **Operational Simplicity**: Independent management and monitoring

### Phase 1: Database Foundation & Setup

#### **1.1 Environment Setup**
- **PostgreSQL Installation**: Local PostgreSQL server setup
- **Database Creation**: Create `trading_system` and `prefect` databases
- **Connection Configuration**: Environment variables, connection strings
- **Database User Setup**: Service-specific users with appropriate permissions

#### **1.2 Prefect Database Setup**
```sql
-- Create Prefect database
CREATE DATABASE prefect;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE prefect TO postgres;
```

**Prefect Configuration:**
```bash
# Configure Prefect to use PostgreSQL
prefect config set PREFECT_API_DATABASE_CONNECTION_URL="postgresql+asyncpg://postgres:password@localhost:5432/prefect"

# Initialize Prefect database
prefect database upgrade
```

#### **1.3 Trading System Database Setup**
```sql
-- Create trading system database
CREATE DATABASE trading_system;

-- Create service-specific schemas
CREATE SCHEMA data_ingestion;
CREATE SCHEMA strategy_engine;
CREATE SCHEMA execution;
CREATE SCHEMA risk_management;
CREATE SCHEMA analytics;
CREATE SCHEMA notification;
CREATE SCHEMA logging;
CREATE SCHEMA shared;
```

#### **1.4 Environment Configuration**
```env
# Trading System Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
TRADING_DB_NAME=trading_system
TRADING_DB_USER=postgres
TRADING_DB_PASSWORD=your_password_here

# Prefect Database
PREFECT_DB_NAME=prefect
PREFECT_DB_USER=postgres
PREFECT_DB_PASSWORD=your_password_here

# Prefect Configuration
PREFECT_API_DATABASE_CONNECTION_URL=postgresql+asyncpg://postgres:password@localhost:5432/prefect

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_URL=redis://localhost:6379/0
```

### Phase 2: Schema Implementation

#### **2.1 Core Trading Tables**
- **Market Data Tables**: Enhanced with constraints and partitioning
- **Trading Operations**: Orders, trades, positions with proper relationships
- **Strategy Management**: Strategy configuration and performance tracking
- **System Logging**: Structured log storage

#### **2.2 Service-Specific Schemas**
- **data_ingestion**: Market data, symbols management, key statistics, institutional holders, company info, data quality logs, ingestion status
  - Symbol tables: `symbols`, `delisted_symbols`, `symbol_data_status` (see [SymbolService API](../api/data-ingestion.md#symbolservice-api) section)
- **strategy_engine**: Strategies, signals, performance metrics
- **execution**: Orders, trades, positions, execution logs
- **risk_management**: Risk limits, events, position limits
- **analytics**: Performance calculations, reports, analytics
- **notification**: Alert configurations, notification logs
- **logging**: Centralized system logs from all services

### Phase 3: Connection Management

#### **3.1 Database Connection Strategy**
```python
# src/config/database.py
class DatabaseConfig:
    # Trading System Database
    TRADING_DB_URL = "postgresql://postgres:password@localhost:5432/trading_system"
    
    # Prefect Database
    PREFECT_DB_URL = "postgresql://postgres:password@localhost:5432/prefect"
    
    # Service-specific schemas
    SCHEMAS = {
        'data_ingestion': 'data_ingestion',
        'strategy_engine': 'strategy_engine',
        'execution': 'execution',
        'risk_management': 'risk_management',
        'analytics': 'analytics',
        'notification': 'notification',
        'logging': 'logging',
        'shared': 'shared'
    }
```

#### **3.2 Connection Pooling**
- **Trading System**: Service-specific connection pools
- **Prefect**: Dedicated connection pool
- **Redis**: Shared cache and message queue
- **Monitoring**: Connection health and performance tracking

### Phase 4: Data Synchronization

#### **4.1 Event-Driven Synchronization**
- **Redis Pub/Sub**: Cross-service data synchronization
- **Analytics Database**: Real-time updates to shared analytics
- **Log Aggregation**: Centralized logging from all services
- **Performance Metrics**: Real-time performance tracking

#### **4.2 Data Consistency**
- **Eventual Consistency**: Event-driven updates between services
- **Conflict Resolution**: Handling concurrent updates
- **Data Validation**: Multi-level data validation
- **Audit Trails**: Complete data lineage tracking

## Implementation Recommendations

### Phase 1: Schema Improvements
1. **Update Core Tables** with improved constraints and data types
2. **Implement Comprehensive Indexing** strategy
3. **Add Partitioning** for large tables
4. **Create Audit Tables** for compliance

### Phase 2: Performance Optimization
1. **Implement Connection Pooling** with proper configuration
2. **Add Query Performance Monitoring**
3. **Create Automated Maintenance** procedures
4. **Implement Caching** strategies

### Phase 3: Advanced Features
1. **Add Row-Level Security** for multi-tenancy
2. **Implement Data Encryption** for sensitive data
3. **Create Backup and Recovery** procedures
4. **Add Real-time Monitoring** dashboards

## Key Benefits of Enhanced Architecture

### 1. Performance
- Optimized queries with proper indexing
- Partitioned tables for large datasets
- Connection pooling for concurrent access
- Query performance monitoring

### 2. Reliability
- Data consistency with proper constraints
- Optimistic locking for concurrent updates
- Automated maintenance procedures
- Comprehensive error handling

### 3. Security
- Row-level security for data isolation
- Audit logging for compliance
- Data encryption for sensitive information
- Access control and monitoring

### 4. Maintainability
- Clear schema documentation
- Automated maintenance procedures
- Performance monitoring and alerting
- Comprehensive testing strategies

This enhanced database architecture provides a solid foundation for a production-grade trading system with proper performance, reliability, and security characteristics.

---

**Note**: This document will be updated as we implement the database architecture and gain more insights into the system requirements.
