# Trading System Logging Architecture

## Overview

This document outlines the logging architecture for the trading system, including design decisions, implementation strategy, and configuration management.

**Last Updated**: October 2025  
**Status**: Implementation Phase  
**Author**: Nishant Nayar

## Design Decisions

### 1. Logging Framework
- **Primary**: Loguru (consolidated logging across all services)
- **Secondary**: PostgreSQL tables for structured log storage
- **Rationale**: Loguru provides excellent performance and features, PostgreSQL enables queryable log analysis

### 2. Log Retention Strategy
- **Approach**: Simple two-tier retention
- **Active Logs**: 30 days (real-time monitoring, hot queries)
- **Archived Logs**: 30-90 days (historical analysis, reports)
- **Cleanup**: Automatic daily cleanup at 2 AM
- **Storage**: Same database, different tables

### 3. Compliance Requirements
- **Status**: No compliance requirements
- **Focus**: Debugging, performance monitoring, system health
- **Audit Trail**: Basic audit logging for system operations

### 4. Log Aggregation
- **Method**: PostgreSQL tables for structured log storage
- **Benefits**: SQL queries, indexing, correlation with trading data
- **Integration**: Seamless with existing database infrastructure

## Architecture Components

### 1. Log Categories
```
📊 Trading Logs:     Trade executions, orders, positions
🔧 System Logs:      Service health, errors, startup/shutdown
⚡ Performance Logs: Execution times, memory usage
🧠 Strategy Logs:    Signal generation, backtesting results
⚠️  Risk Logs:       Risk calculations, violations, alerts
```

### 2. Log Levels
```
ERROR:   System failures, API errors, trading failures
WARNING: Risk violations, performance issues, retries
INFO:    Normal operations, trade executions, data flow
DEBUG:   Detailed execution (development only)
```

### 3. Service-Specific Logging
| Service | Log Level | Focus Area |
|---------|-----------|------------|
| Data Ingestion | INFO | Market data fetch, validation |
| Strategy Engine | DEBUG | Signal generation, calculations |
| Execution | INFO | Order placement, trade execution |
| Risk Management | WARNING | Risk calculations, violations |
| Analytics | INFO | Performance calculations, reports |
| Notification | INFO | Alert delivery, communication |

## Implementation Architecture

### 1. Dual Logging System

```
┌─────────────────────────────────────────────────────────┐
│                  Application Code                       │
├─────────────────────────────────────────────────────────┤
│              Logging Module (src/shared/logging/)       │
│  ├── logger.py         # Main logger setup             │
│  ├── handlers.py       # Custom handlers (DB, file)    │
│  ├── formatters.py     # Log formatting                │
│  └── config.py         # Configuration loader          │
├─────────────────────────────────────────────────────────┤
│         Loguru (File)           PostgreSQL (DB)        │
│  ├── logs/trading.log      ├── logging.system_logs    │
│  ├── logs/errors.log       ├── logging.performance    │
│  └── logs/{service}.log    └── logging.trading_logs   │
└─────────────────────────────────────────────────────────┘
```

### 2. Key Features

#### Feature 1: Automatic Service Detection
```python
# Automatically detects which service is logging
from src.shared.logging import get_logger

logger = get_logger(__name__)  # Detects service from module name
logger.info("Data ingestion started")
# → Logs to: logs/data_ingestion.log AND logging.system_logs
```

#### Feature 2: Dual Output (File + Database)
```python
# Single log statement goes to BOTH:
logger.info("Order created", order_id="ORD123", symbol="AAPL")

# File output (logs/execution.log):
# 2025-10-01 10:30:45.123 | INFO | execution:create_order:42 | Order created

# Database output (logging.system_logs):
# {
#   timestamp: 2025-10-01 10:30:45.123,
#   service: 'execution',
#   level: 'INFO',
#   message: 'Order created',
#   metadata: {'order_id': 'ORD123', 'symbol': 'AAPL'}
# }
```

#### Feature 3: Correlation ID Tracking
```python
# Track related operations across services
with correlation_context("trade-12345"):
    logger.info("Order placed")
    # ... order execution ...
    logger.info("Position updated")
    # ... position update ...
    
# All logs have correlation_id='trade-12345'
# Easy to trace complete flow!
```

#### Feature 4: Performance Tracking
```python
from src.shared.logging import log_performance

@log_performance
def execute_trade(order_id):
    # Your code here
    pass
    
# Automatically logs:
# - Execution time
# - Memory usage (optional)
# - Function arguments (optional)
# Stored in logging.performance_logs
```

#### Feature 5: Structured Logging
```python
# Pass structured data
logger.info(
    "Trade executed",
    trade_id="TRD123",
    symbol="AAPL",
    quantity=100,
    price=150.25,
    commission=1.50
)

# Stored as JSONB in database
# Easy to query and analyze!
```

### 3. Logger Setup Options

#### Option A: Simple Setup (Recommended)
```python
from src.shared.logging import setup_logging

# Setup once at application startup
setup_logging()

# Use everywhere
from loguru import logger
logger.info("Application started")
```

**Pros:**
- Simple to use
- One-time setup
- Works everywhere
- No boilerplate

**Cons:**
- Less control per module
- Global configuration

#### Option B: Service-Specific Setup
```python
from src.shared.logging import get_service_logger

# Each service gets its own logger
logger = get_service_logger("data_ingestion")
logger.info("Market data fetched")
# → Logs to logs/data_ingestion.log
```

**Pros:**
- Service-specific configuration
- Isolated log files
- Different log levels per service

**Cons:**
- More setup code
- Need to specify service name

#### Option C: Context-Aware Logger (Advanced)
```python
from src.shared.logging import get_logger

# Automatically detects service from module name
logger = get_logger(__name__)  
# __name__ = 'src.services.execution.order_manager'
# → Detected service: 'execution'
# → Logs to: logs/execution.log
```

**Pros:**
- Automatic service detection
- No hardcoding service names
- Clean code
- Recommended approach!

**Cons:**
- Relies on module structure

### 4. Database Handler Design

#### Batching Strategy
- **Method**: Async batching with fallback
- **Batch Size**: 100 records or 10 seconds
- **Fallback**: Write to file if database fails
- **Benefits**: Performance + reliability

#### Log Levels for Database
- **Files**: DEBUG+ (complete debugging info)
- **Database**: INFO+ (reduce noise, better performance)
- **Rationale**: Debug logs too verbose for DB, important logs in DB for analytics

#### Error Handling
```python
# Graceful degradation strategy
try:
    write_to_database(log)
except DatabaseError:
    try:
        write_to_fallback_file(log)
    except IOError:
        print(f"CRITICAL: Failed to log: {log}", file=sys.stderr)
        # Never fail the application due to logging!
```

## Database Schema

### 1. Active Logs Table
```sql
CREATE TABLE system_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    service VARCHAR(50) NOT NULL,
    level VARCHAR(10) NOT NULL,
    event_type VARCHAR(100),
    message TEXT,
    correlation_id VARCHAR(100),
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX idx_system_logs_timestamp ON system_logs(timestamp);
CREATE INDEX idx_system_logs_service ON system_logs(service);
CREATE INDEX idx_system_logs_level ON system_logs(level);
CREATE INDEX idx_system_logs_correlation ON system_logs(correlation_id);
```

### 2. Archived Logs Table
```sql
CREATE TABLE archived_system_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    service VARCHAR(50) NOT NULL,
    level VARCHAR(10) NOT NULL,
    event_type VARCHAR(100),
    message TEXT,
    correlation_id VARCHAR(100),
    metadata JSONB,
    archived_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### 3. Specialized Log Tables
```sql
-- Trading-specific logs
CREATE TABLE trading_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    trade_id VARCHAR(100),
    symbol VARCHAR(20),
    side VARCHAR(10),
    quantity DECIMAL,
    price DECIMAL,
    strategy VARCHAR(100),
    execution_time_ms INTEGER,
    status VARCHAR(50),
    error_message TEXT,
    correlation_id VARCHAR(100)
);

-- Performance logs
CREATE TABLE performance_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    service VARCHAR(50),
    operation VARCHAR(100),
    execution_time_ms INTEGER,
    memory_usage_mb INTEGER,
    cpu_usage_percent DECIMAL,
    metadata JSONB
);
```

## Configuration

### 1. Logging Configuration (config/logging.yaml)
```yaml
logging:
  # Log Levels
  level: "INFO"
  root_level: "INFO"
  
  # Log Rotation
  rotation:
    size: "10 MB"
    time: "daily"
    retention: "30 days"
    compression: true
    
  # Log Format
  format: "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} | {message}"
  
  # Log Files
  files:
    main: "logs/trading.log"
    errors: "logs/errors.log"
    system: "logs/system.log"
    trades: "logs/trades.log"
    performance: "logs/performance.log"
    
  # Database Logging
  database:
    enabled: true
    active_table: "system_logs"
    archive_table: "archived_system_logs"
    batch_size: 100
    batch_timeout: 10  # seconds
    async_logging: true
    fallback_to_file: true
    
  # Retention Settings
  retention:
    active_days: 30
    archive_days: 90
    cleanup_schedule: "0 2 * * *"  # Daily at 2 AM
    
  # Service-specific Logging
  services:
    data_ingestion:
      level: "INFO"
      file: "logs/data_ingestion.log"
    strategy_engine:
      level: "DEBUG"
      file: "logs/strategy_engine.log"
    execution:
      level: "INFO"
      file: "logs/execution.log"
    risk_management:
      level: "WARNING"
      file: "logs/risk_management.log"
    analytics:
      level: "INFO"
      file: "logs/analytics.log"
    notification:
      level: "INFO"
      file: "logs/notification.log"
      
  # Structured Logging
  structured: true
  json_format: false
  
  # Performance Logging
  performance:
    enabled: true
    log_execution_time: true
    log_memory_usage: true
    log_database_queries: false
```

### 2. Environment Settings
```python
# src/config/settings.py
class LoggingSettings(BaseSettings):
    # File retention
    file_retention_days: int = 30
    file_archive_after_days: int = 7
    
    # Database retention
    database_retention_days: int = 30
    database_archive_after_days: int = 7
    
    # Cleanup schedule
    cleanup_schedule: str = "0 2 * * *"
    cleanup_batch_size: int = 1000
    
    # Retention policies
    trading_logs_retention: int = 90
    performance_logs_retention: int = 30
    system_logs_retention: int = 30
    error_logs_retention: int = 90
```

## Usage Patterns

### Pattern 1: Simple Logging
```python
from loguru import logger

logger.info("Application started")
logger.error("Failed to connect to API", error=str(e))
```

### Pattern 2: Structured Logging
```python
logger.info(
    "Order executed",
    order_id="ORD123",
    symbol="AAPL",
    quantity=100,
    price=150.25,
    execution_time_ms=45
)
```

### Pattern 3: Performance Tracking
```python
from src.shared.logging import log_performance

@log_performance
def calculate_indicators(symbol: str, period: int):
    # Heavy calculation
    pass
```

### Pattern 4: Correlation Tracking
```python
from src.shared.logging import correlation_context

async def process_trade_flow(trade_id):
    with correlation_context(trade_id):
        await validate_risk()      # Logged with trade_id
        await execute_order()      # Logged with trade_id
        await update_position()    # Logged with trade_id
```

## Implementation Strategy

### 1. Dual Logging Approach
```
Service → Loguru → File + PostgreSQL
                ↓
        Structured Data → Database
                ↓
        SQL Queries → Analysis
```

### 2. Automatic Cleanup Process
- **Schedule**: Daily at 2 AM via Prefect flows
- **Process**: 
  1. Archive logs older than 30 days
  2. Delete archived logs older than 90 days
  3. Log cleanup results
- **Monitoring**: Cleanup operation logs (future enhancement)

### 3. Log Analysis Capabilities
```sql
-- Find all logs related to a specific trade
SELECT * FROM system_logs 
WHERE correlation_id = 'trade_12345'
ORDER BY timestamp;

-- Link trading logs with system logs
SELECT t.*, s.message, s.level
FROM trading_logs t
JOIN system_logs s ON t.trade_id = s.correlation_id
WHERE t.symbol = 'AAPL';

-- Performance analysis
SELECT service, AVG(execution_time_ms) as avg_time
FROM performance_logs 
WHERE timestamp > NOW() - INTERVAL '1 day'
GROUP BY service;
```

## Implementation Phases

### Phase 1: Core Logging (Essential)
1. Basic Loguru setup
2. File logging with rotation
3. Service detection
4. Configuration loading

### Phase 2: Database Integration (Important)
1. Database handler
2. Async batching
3. Fallback mechanism
4. Structured logging

### Phase 3: Advanced Features (Nice to Have)
1. Correlation ID tracking
2. Performance decorator
3. Log aggregation utilities
4. Dashboard integration

### Phase 4: Monitoring (Future)
1. Real-time log streaming
2. Error alerting
3. Performance dashboards
4. Anomaly detection

## Future Enhancements

### 1. Phase 2 (Post-MVP)
- [ ] Real-time log monitoring dashboard
- [ ] Log analysis tools with charts
- [ ] Automated alerting based on log patterns
- [ ] Log correlation analysis tools

### 2. Phase 3 (Advanced)
- [ ] Machine learning for log pattern detection
- [ ] Predictive alerting based on log trends
- [ ] Advanced log visualization
- [ ] Integration with external monitoring tools

## Open Questions

### 1. Implementation Details
- [x] Logging implementation in shared utilities
- [x] Prefect flow for automatic cleanup
- [x] Log correlation ID generation strategy
- [x] Performance optimization for high-volume logging

### 2. Monitoring & Alerts
- [ ] Real-time log monitoring requirements
- [ ] Alert thresholds for error rates
- [ ] Performance degradation detection
- [ ] System health indicators

### 3. Development vs Production
- [ ] Different logging levels for environments
- [ ] Development debugging tools
- [ ] Production log optimization
- [ ] Testing log configurations

## Next Steps

1. **Database Schema**: Implement log tables in PostgreSQL
2. **Logging Utilities**: Create shared logging utilities
3. **Service Integration**: Integrate logging in each microservice
4. **Cleanup Automation**: Implement Prefect cleanup flows
5. **Testing**: Test logging configuration and cleanup processes

---

**Note**: This document will be updated as we make more architectural decisions and implement the logging system.
