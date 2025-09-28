# Trading System Logging Architecture

## Overview

This document outlines the logging architecture for the trading system, including design decisions, implementation strategy, and configuration management.

**Last Updated**: September 2025  
**Status**: Development Phase  
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
    batch_size: 1000
    async_logging: true
    
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
- [ ] Logging implementation in shared utilities
- [ ] Prefect flow for automatic cleanup
- [ ] Log correlation ID generation strategy
- [ ] Performance optimization for high-volume logging

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
