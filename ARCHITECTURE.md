# Trading System Architecture

## Overview

A production-grade algorithmic trading system designed for local deployment, focusing on equities trading through Alpaca with paper trading capabilities. The system uses a modular monolithic architecture with clear service boundaries, Python-based components, and a modern web interface.

**Current Architecture**: Modular monolith with service-oriented design  
**Future Plans**: Microservices architecture with Prefect orchestration (v1.3.0+)

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
- **Cache/Queue**: Redis (caching, planned: pub/sub)
- **Data Processing**: pandas (analytics, data manipulation)
- **Orchestration**: Planned for v1.2.0 (Prefect workflow management)
- **Validation**: Pydantic (data models, API validation)

### Frontend
- **Backend**: FastAPI
- **Frontend**: Streamlit + Plotly Charts + Custom CSS
- **Charts**: Plotly library for interactive financial visualizations
- **Session State**: Persistent data sharing across pages
- **AI Integration**: Ollama LLM for natural language processing
- **Real-time**: Planned for future versions

### Development & Quality
- **Linting**: Flake8 + Black + isort
- **Type Checking**: mypy
- **Documentation**: MkDocs
- **Logging**: Loguru (consolidated logging)
- **Testing**: pytest + coverage

## Service-Oriented Architecture

### Current Architecture (v1.0.0)

The system is implemented as a **modular monolith** with clear service boundaries. Each service is a separate module that can be independently developed and tested, with the flexibility to extract into microservices in future versions.

### 1. Data Ingestion Module
**Purpose**: Collect market data from multiple sources (Polygon.io + Alpaca)

**Components**:
- Polygon.io client (historical data)
- Alpaca API client (real-time trading)
- Yahoo Finance client (additional data source - company info, financials, key statistics)
- Symbol management system
- Data validation (Pydantic models)
- Data quality checks
- Error handling and retry logic
- Timezone handling (UTC storage, Central Time display)

**Responsibilities**:
- Fetch historical market data from Polygon.io (end-of-day)
- Fetch real-time trading data from Alpaca
- Fetch company information and financials from Yahoo Finance
- Manage symbol universe (active/delisted tracking)
- Validate data integrity
- Store raw data in PostgreSQL (UTC timezone)
- Cache frequently accessed data in Redis
- Automatic delisting detection
- Timezone conversion for display (UTC to Central Time)

**Implementation Status**: ✅ Core functionality implemented  
**Future Enhancements**: Prefect workflows for automated data collection (v1.2.0)

### 2. Strategy Engine Module
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

**Implementation Status**: 🚧 Planned for v1.1.0  
**Future Enhancements**: Automated backtesting workflows

### 3. Execution Module
**Purpose**: Execute trades and manage orders via Alpaca API

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

**Implementation Status**: ✅ Core Alpaca integration complete  
**Future Enhancements**: Advanced order types, automated trade reconciliation

### 4. Risk Management Module
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

**Implementation Status**: 🚧 Planned for v1.1.0  
**Future Enhancements**: Real-time risk monitoring, automated alerts

### 5. Analytics Module
**Purpose**: Performance analysis and reporting

**Components**:
- Performance calculation engine
- Data visualization (Plotly Charts)
- Market data analysis
- Interactive dashboards
- Technical indicator calculations
- AI-powered analysis (via Ollama integration)

**Responsibilities**:
- Display market data with professional charts
- Generate performance reports
- Analyze trade patterns
- Portfolio analytics
- Technical indicator visualization
- AI-powered stock screening and analysis
- Natural language query interpretation

**Implementation Status**: ✅ Market data visualization and AI screener complete  
**Future Enhancements**: Strategy performance metrics, backtesting framework

### 6. Notification Module
**Purpose**: Handle alerts and communications

**Components**:
- Email notification system (planned)
- Dashboard notifications
- Log aggregation (Loguru)

**Responsibilities**:
- Send trade notifications
- Alert on system errors
- Notify on risk violations
- Aggregate and format logs
- Manage notification preferences

**Implementation Status**: 🚧 Planned for v1.1.0  
**Future Enhancements**: Email/SMS alerts, automated daily summaries

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
data_ingestion.symbols (symbol, name, exchange, sector, market_cap, status)
data_ingestion.delisted_symbols (symbol, delist_date, last_price, notes)
data_ingestion.symbol_data_status (symbol, date, data_source, status, error_message)
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

## Current Architecture Patterns

### Module Communication (v1.0.0)
- **Direct Function Calls**: In-process module communication
- **Shared Database**: PostgreSQL for data persistence
- **Caching Layer**: Redis for frequently accessed data
- **API Endpoints**: FastAPI REST APIs for frontend

### Future Communication Patterns (v1.3.0+)
- **Synchronous**: REST APIs between microservices
- **Asynchronous**: Redis pub/sub for event-driven architecture
- **Batch Processing**: Prefect flows for scheduled workflows
- **Real-time Updates**: WebSocket connections to frontend

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

### Current Local Deployment (v1.0.0)
```
┌─────────────────────────────────────────────────────────┐
│                    Local Machine                        │
├─────────────────────────────────────────────────────────┤
│  PostgreSQL  │  Redis                                   │
├─────────────────────────────────────────────────────────┤
│  FastAPI Application (main.py)                          │
│  ├── Data Ingestion Module                              │
│  ├── Execution Module (Alpaca Integration)              │
│  ├── Analytics Module                                   │
│  └── Shared Components (Database, Logging, Utils)       │
├─────────────────────────────────────────────────────────┤
│  Frontend (Streamlit + Plotly Charts + Custom CSS)      │
└─────────────────────────────────────────────────────────┘
```

### Startup Process
1. Start PostgreSQL and Redis
2. Run database migrations (if needed)
3. Start FastAPI application: `python main.py`
4. Access Streamlit UI at `http://localhost:8501`

### Future Microservices Deployment (v1.3.0+)
```
┌─────────────────────────────────────────────────────────┐
│  PostgreSQL  │  Redis    │  Prefect Server             │
├─────────────────────────────────────────────────────────┤
│  Data        │ Strategy  │ Execution  │ Risk           │
│  Ingestion   │ Engine    │ Service    │ Management     │
│  :8001       │ :8002     │ :8003      │ :8004          │
├─────────────────────────────────────────────────────────┤
│  Analytics   │ Notification │ API Gateway              │
│  :8005       │ :8006        │ :8000                    │
└─────────────────────────────────────────────────────────┘
```

## Configuration Management

### Environment Configuration
```python
# src/config/settings.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Database
    postgres_url: str
    redis_url: str
    
    # Alpaca API (Real-time Trading)
    alpaca_api_key: str
    alpaca_secret_key: str
    alpaca_base_url: str = "https://paper-api.alpaca.markets"
    
    # Polygon.io API (Historical Data)
    polygon_api_key: str
    polygon_base_url: str = "https://api.polygon.io"
    polygon_data_delay_minutes: int = 15
    
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

## Development Roadmap

### Phase 1 - v1.0.0 (Current) ✅
- Paper trading with Alpaca
- Market data integration (Polygon.io, Yahoo Finance)
- Professional web dashboard
- Database architecture
- Comprehensive logging

### Phase 2 - v1.1.0 (In Progress) 🚧
- Strategy engine implementation
- Backtesting framework
- Risk management module
- Performance analytics
- Notification system

### Phase 3 - v1.2.0 (Planned) 📋
- Prefect workflow orchestration
- Automated data collection
- Scheduled strategy execution
- Advanced backtesting
- Email/SMS notifications

### Phase 4 - v1.3.0 (Future) 🔮
- Microservices architecture
- Service mesh and API gateway
- Horizontal scaling
- Cloud deployment (AWS/Azure/GCP)
- Multi-asset support
- Machine learning integration

## Getting Started

1. **Setup Environment**: Install Anaconda, PostgreSQL, Redis
2. **Clone Repository**: Get the codebase
3. **Install Dependencies**: `pip install -r requirements.txt`
4. **Configure**: Set up API keys in `.env` file
5. **Initialize Database**: `python scripts/setup_databases.py`
6. **Start Application**: `python main.py`
7. **Access Streamlit UI**: Open `http://localhost:8501`

## Architecture Evolution

This architecture follows the **Majestic Monolith** pattern, starting simple and evolving as needed:

- **v1.0 (Current)**: Modular monolith - fast development, easy deployment
- **v1.1-1.2**: Enhanced functionality within monolith
- **v1.3+**: Microservices extraction when scale demands it

This approach provides a solid foundation for a production-grade trading system that can scale with your needs while maintaining simplicity for local deployment and rapid iteration.
