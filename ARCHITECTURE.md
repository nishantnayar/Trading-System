# Trading System Architecture

## Overview

A production-grade algorithmic trading system designed for local deployment, focusing on equities trading through Alpaca with paper trading capabilities. The system uses a microservices architecture with Prefect orchestration, Python-based services, and a modern web interface.

**Author**: Nishant Nayar  
**Email**: nishant.nayar@hotmail.com  
**Repository**: https://github.com/nishantnayar/trading-system  
**Documentation**: https://nishantnayar.github.io/trading-system

## System Requirements

- **Asset Class**: Equities trading via Alpaca API
- **Data Frequency**: Hourly data ingestion
- **Trading Mode**: Paper trading initially, live trading later
- **Deployment**: Local machine (Windows 10)
- **Architecture**: Microservices with orchestration
- **Data Growth**: Designed to handle growing datasets with Polars

## Technology Stack

### Core Technologies
- **Language**: Python 3.11+
- **Environment**: Anaconda
- **Database**: PostgreSQL (metadata, transactions)
- **Cache/Queue**: Redis (caching, pub/sub)
- **Data Processing**: Polars (analytics, large datasets)
- **Orchestration**: Prefect (workflow management)
- **Validation**: Pydantic (data models, API validation)

### Frontend
- **Backend**: FastAPI
- **Frontend**: HTMX + Plotly + Tailwind CSS
- **Charts**: Plotly.js for financial visualizations
- **Real-time**: WebSocket connections for live updates

### Development & Quality
- **Linting**: Flake8 + Black + isort
- **Type Checking**: mypy
- **Documentation**: MkDocs
- **Logging**: Loguru (consolidated logging)
- **Testing**: pytest + coverage

## Microservices Architecture

### 1. Data Ingestion Service
**Purpose**: Collect market data from Alpaca API

**Components**:
- Alpaca API client
- Data validation (Pydantic models)
- Prefect flows for hourly ingestion
- Data quality checks
- Error handling and retry logic

**Responsibilities**:
- Fetch hourly market data (OHLCV)
- Validate data integrity
- Store raw data in PostgreSQL
- Cache frequently accessed data in Redis
- Publish data events to message queue

**Prefect Flows**:
- `fetch_market_data`: Hourly data collection
- `validate_data_quality`: Data validation pipeline
- `archive_old_data`: Data lifecycle management

### 2. Strategy Engine Service
**Purpose**: Execute trading strategies and generate signals

**Components**:
- Strategy framework (plugin-based)
- Signal generation logic
- Portfolio calculations
- Strategy configuration management

**Responsibilities**:
- Load and execute trading strategies
- Calculate technical indicators
- Generate buy/sell signals
- Manage strategy state and parameters
- Log strategy performance metrics

**Prefect Flows**:
- `run_strategy`: Execute strategy logic
- `calculate_indicators`: Technical analysis
- `generate_signals`: Signal generation
- `backtest_strategy`: Historical strategy testing

### 3. Execution Service
**Purpose**: Execute trades and manage orders

**Components**:
- Alpaca trading API client
- Order management system
- Position tracking
- Trade execution logic

**Responsibilities**:
- Place buy/sell orders
- Manage order lifecycle
- Track positions and P&L
- Handle order fills and partial fills
- Implement order types (market, limit, stop)

**Prefect Flows**:
- `execute_trades`: Process trading signals
- `manage_orders`: Order lifecycle management
- `update_positions`: Position tracking
- `reconcile_trades`: Trade reconciliation

### 4. Risk Management Service
**Purpose**: Monitor and control trading risks

**Components**:
- Position sizing algorithms
- Risk limit validation
- Portfolio risk calculations
- Risk monitoring dashboard

**Responsibilities**:
- Calculate position sizes
- Validate risk limits
- Monitor portfolio exposure
- Generate risk alerts
- Implement circuit breakers

**Prefect Flows**:
- `calculate_position_size`: Position sizing
- `validate_risk_limits`: Risk validation
- `monitor_portfolio_risk`: Continuous risk monitoring
- `generate_risk_alerts`: Risk alerting

### 5. Analytics Service
**Purpose**: Performance analysis and reporting

**Components**:
- Performance calculation engine
- Backtesting framework
- Reporting generation
- Data visualization

**Responsibilities**:
- Calculate strategy performance metrics
- Generate performance reports
- Create backtesting results
- Analyze trade patterns
- Generate portfolio analytics

**Prefect Flows**:
- `calculate_performance`: Performance metrics
- `generate_reports`: Report generation
- `run_backtest`: Historical testing
- `analyze_trades`: Trade analysis

### 6. Notification Service
**Purpose**: Handle alerts and communications

**Components**:
- Email notification system
- SMS alerts (optional)
- Dashboard notifications
- Log aggregation

**Responsibilities**:
- Send trade notifications
- Alert on system errors
- Notify on risk violations
- Aggregate and format logs
- Manage notification preferences

**Prefect Flows**:
- `send_trade_alerts`: Trade notifications
- `monitor_system_health`: System monitoring
- `aggregate_logs`: Log processing
- `send_daily_summary`: Daily reports

## Data Architecture

> **📊 Detailed Database Documentation**: For comprehensive database architecture, session management, and implementation details, see [Database Architecture](docs/development/database.md).

### Database Design

**Two-Database Strategy:**
```
┌─────────────────────────────────────────────────────────┐
│                PostgreSQL Instance                      │
├─────────────────────────────────────────────────────────┤
│  trading_system database  │  Prefect database          │
│  ├── data_ingestion       │  ├── public schema         │
│  ├── strategy_engine      │  │   ├── flow_runs         │
│  ├── execution            │  │   ├── task_runs         │
│  ├── risk_management      │  │   ├── deployments       │
│  ├── analytics            │  │   └── (other Prefect)   │
│  ├── notification         │                            │
│  ├── logging              │                            │
│  └── shared               │                            │
└─────────────────────────────────────────────────────────┘
```

**Core PostgreSQL Tables**:
```sql
-- Data Ingestion Schema
data_ingestion.market_data (symbol, timestamp, open, high, low, close, volume)
data_ingestion.data_quality_logs (symbol, check_type, status, message)

-- Execution Schema
execution.orders (order_id, symbol, side, quantity, price, status, timestamp)
execution.trades (trade_id, order_id, symbol, quantity, price, timestamp)
execution.positions (symbol, quantity, avg_price, unrealized_pnl)

-- Strategy Engine Schema
strategy_engine.strategies (strategy_id, name, parameters, status, created_at)
strategy_engine.strategy_signals (signal_id, strategy_id, symbol, signal, timestamp)
strategy_engine.strategy_performance (strategy_id, date, returns, sharpe_ratio)

-- Risk Management Schema
risk_management.risk_limits (account_id, limit_type, limit_value)
risk_management.risk_events (event_id, type, severity, message, timestamp)

-- Analytics Schema
analytics.portfolio_summary (account_id, symbol, total_value, pnl)
analytics.performance_metrics (strategy, date, returns, sharpe_ratio)

-- Logging Schema
logging.system_logs (log_id, service, level, message, timestamp)
logging.performance_logs (service, operation, execution_time_ms)

-- Shared Schema
shared.audit_log (user_id, table_name, operation, old_values, new_values)
shared.system_config (config_key, config_value, description)
```

**SQLAlchemy ORM:**
- Declarative base for all models
- Automated session management with context managers
- Transaction support with automatic commit/rollback
- Read-only sessions for optimized analytics
- Comprehensive error handling and logging

**Redis Usage**:
- Cached market data (recent bars)
- Session data and temporary calculations
- Message queue for service communication
- Real-time portfolio updates

**Polars DataFrames**:
- Large historical datasets for analysis
- Technical indicator calculations
- Backtesting data processing
- Performance analytics

## Communication Patterns

### Service Communication
- **Synchronous**: REST APIs for real-time requests
- **Asynchronous**: Redis pub/sub for events
- **Batch Processing**: Prefect flows for scheduled tasks
- **Real-time Updates**: WebSocket connections to frontend

### Message Flow
```
Data Ingestion → Strategy Engine → Risk Management → Execution
     ↓                ↓                ↓              ↓
Analytics Service ← Notification Service ← Redis ← PostgreSQL
```

## Security Architecture

### API Security
- Alpaca API keys stored in environment variables
- Rate limiting on all API endpoints
- Input validation with Pydantic models
- SQL injection prevention with ORM

### Data Security
- Database connection encryption
- Secure credential storage
- Audit logging for all trades
- Backup and recovery procedures

## Monitoring & Observability

### Logging Strategy
- **Loguru**: Consolidated logging across all services
- **Structured Logging**: JSON format for analysis
- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Log Rotation**: Daily rotation, 30-day retention
- **Detailed Architecture**: [Logging Architecture](docs/development/logging.md)

### Monitoring
- **System Health**: Service status, database connections
- **Trading Metrics**: P&L, trade count, execution time
- **Performance**: Memory usage, CPU utilization
- **Alerts**: Email notifications for critical events

### Dashboard
- **Real-time Portfolio**: Current positions and P&L
- **Strategy Performance**: Returns, Sharpe ratio, drawdown
- **System Status**: Service health, error rates
- **Trade History**: Recent trades and orders

## Development Workflow

### Environment Setup
```bash
# Create conda environment
conda create -n trading-system python=3.11
conda activate trading-system

# Install dependencies
conda install -c conda-forge postgresql redis
pip install -r requirements.txt

# Setup databases
createdb trading_system
redis-server
```

### Code Quality
```bash
# Pre-commit hooks
pre-commit install

# Code formatting
black .
isort .

# Linting
flake8 .

# Type checking
mypy src/
```

**Configuration Files:**
- `.isort.cfg` - Import sorting configuration (Black-compatible)
- `pytest.ini` - Test configuration with markers
- All tools pre-configured to work together seamlessly

### Testing Strategy
- **Unit Tests**: Individual service functions
- **Integration Tests**: Service interactions
- **End-to-End Tests**: Complete trading workflows
- **Strategy Tests**: Backtesting validation

## Deployment Architecture

### Local Deployment
```
┌─────────────────────────────────────────────────────────┐
│                    Local Machine                        │
├─────────────────────────────────────────────────────────┤
│  PostgreSQL  │  Redis    │  Prefect Server             │
├─────────────────────────────────────────────────────────┤
│  Data        │ Strategy  │ Execution  │ Risk           │
│  Ingestion   │ Engine    │ Service    │ Management     │
├─────────────────────────────────────────────────────────┤
│  Analytics   │ Notification │ FastAPI Web Server      │
├─────────────────────────────────────────────────────────┤
│  Frontend (HTMX + Plotly)                              │
└─────────────────────────────────────────────────────────┘
```

### Service Startup Order
1. PostgreSQL and Redis
2. Prefect Server
3. Microservices (parallel)
4. FastAPI Web Server
5. Frontend

## Configuration Management

### Environment Configuration
```python
# src/config/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    postgres_url: str
    redis_url: str
    
    # Alpaca API
    alpaca_api_key: str
    alpaca_secret_key: str
    alpaca_base_url: str = "https://paper-api.alpaca.markets"
    
    # Prefect
    prefect_api_url: str = "http://localhost:4200"
    
    # Logging
    log_level: str = "INFO"
    log_retention_days: int = 30
    
    class Config:
        env_file = ".env"
```

### Strategy Configuration
```yaml
# config/strategies.yaml
strategies:
  - name: "momentum_strategy"
    enabled: true
    parameters:
      lookback_period: 20
      threshold: 0.02
      max_position_size: 0.1
    risk_limits:
      max_drawdown: 0.05
      max_daily_loss: 0.02
```

## Performance Considerations

### Data Processing
- **Polars**: Optimized for large datasets
- **Batch Processing**: Efficient data pipeline
- **Caching**: Redis for frequently accessed data
- **Indexing**: Database indexes for fast queries

### Scalability
- **Horizontal Scaling**: Multiple service instances
- **Database Optimization**: Query optimization, connection pooling
- **Memory Management**: Efficient data structures
- **Async Processing**: Non-blocking operations

## Future Enhancements

### Phase 1 (Current)
- Paper trading with single strategy
- Basic monitoring and alerts
- Simple web interface

### Phase 2
- Live trading capabilities
- Multiple strategy support
- Advanced analytics
- Mobile-responsive interface

### Phase 3
- Machine learning integration
- Advanced risk management
- Multi-asset support
- Cloud deployment options

## Getting Started

1. **Setup Environment**: Install Anaconda, PostgreSQL, Redis
2. **Clone Repository**: Get the codebase
3. **Install Dependencies**: Create conda environment
4. **Configure**: Set up API keys and database
5. **Run Services**: Start all microservices
6. **Access Dashboard**: Open web interface
7. **Deploy Strategy**: Configure and start trading

This architecture provides a solid foundation for a production-grade trading system that can scale with your needs while maintaining simplicity for local deployment.
