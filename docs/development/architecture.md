# Trading System Comprehensive Architecture

## Overview

A production-grade algorithmic trading system designed for local deployment, focusing on equities trading through Alpaca with paper trading capabilities. The system uses a microservices architecture with Prefect orchestration, Python-based services, and a modern web interface.

**Author**: Nishant Nayar  
**Email**: nishant.nayar@hotmail.com  
**Repository**: https://github.com/nishantnayar/trading-system  
**Documentation**: https://nishantnayar.github.io/trading-system  
**Last Updated**: September 2025  
**Status**: Design Phase

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
- **Database**: PostgreSQL (metadata, transactions, logs)
- **Cache/Queue**: Redis (caching, pub/sub)
- **Data Processing**: Polars (analytics, large datasets)
- **Orchestration**: Prefect (workflow management)
- **Validation**: Pydantic (data models, API validation)

### Frontend
- **Backend**: FastAPI
- **Frontend**: HTMX + Plotly + Tailwind CSS
- **Charts**: Plotly.js for financial visualizations
- **Updates**: Periodic refresh (every 5-10 minutes)

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

## Database Architecture

> **📊 Detailed Database Analysis**: For a comprehensive review of database schema design, performance considerations, and implementation strategies, see [Database Architecture Detailed Review](database.md).

### Database Connectivity Strategy

#### Separate Database Architecture with Prefect 3.4.14

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

#### Trading System Database (Service-Specific Schemas)
- **Data Ingestion**: `market_data`, `data_quality_logs`, `ingestion_status`
- **Strategy Engine**: `strategies`, `strategy_signals`, `strategy_configs`
- **Execution**: `orders`, `trades`, `positions`, `execution_logs`
- **Risk Management**: `risk_limits`, `risk_events`, `position_limits`
- **Analytics**: `performance_metrics`, `reports`, `analytics_cache`
- **Notification**: `alert_configs`, `notification_logs`
- **Logging**: `system_logs`, `trading_logs`, `performance_logs`

#### Prefect Database (Orchestration)
- **Flow Management**: `flow_runs`, `task_runs`, `deployments`
- **Work Pools**: `work_pools`, `workers`
- **Blocks**: `blocks`, `block_documents`
- **UI State**: `ui_settings`, `saved_searches`

#### Why Separate Databases:
- **Prefect Compatibility**: Works exactly as Prefect 3.4.14 expects
- **Clean Architecture**: Clear separation of orchestration and trading data
- **No Workarounds**: No hacks or unsupported configurations
- **Future-Proof**: Compatible with Prefect updates
- **Operational Simplicity**: Independent management and monitoring

### Database Schema

#### Core Trading Tables
```sql
-- Market Data Storage (Enhanced Design)
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
    
    -- Constraints
    CONSTRAINT unique_symbol_timestamp UNIQUE (symbol, timestamp),
    CONSTRAINT positive_prices CHECK (open > 0 AND high > 0 AND low > 0 AND close > 0)
) PARTITION BY RANGE (timestamp);

-- Trading Operations (Enhanced Design)
CREATE TYPE order_side AS ENUM ('buy', 'sell');
CREATE TYPE order_type AS ENUM ('market', 'limit', 'stop', 'stop_limit');
CREATE TYPE order_status AS ENUM ('pending', 'submitted', 'filled', 'partially_filled', 'cancelled', 'rejected');

CREATE TABLE orders (
    id BIGSERIAL PRIMARY KEY,
    order_id VARCHAR(100) UNIQUE NOT NULL,
    account_id VARCHAR(50) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    side order_side NOT NULL,
    order_type order_type NOT NULL,
    quantity DECIMAL(15,4) NOT NULL,
    price DECIMAL(15,4),
    status order_status NOT NULL DEFAULT 'pending',
    strategy VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

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
    strategy VARCHAR(100),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE positions (
    id BIGSERIAL PRIMARY KEY,
    account_id VARCHAR(50) NOT NULL,
    symbol VARCHAR(20) NOT NULL,
    quantity DECIMAL(15,4) NOT NULL,
    avg_price DECIMAL(15,4) NOT NULL,
    market_value DECIMAL(15,4),
    unrealized_pnl DECIMAL(15,4),
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    CONSTRAINT unique_account_symbol UNIQUE (account_id, symbol)
);
```

#### Strategy Management Tables
```sql
-- Strategy Configuration
CREATE TABLE strategies (
    id SERIAL PRIMARY KEY,
    strategy_id VARCHAR(100) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    parameters JSONB,
    status VARCHAR(20) DEFAULT 'inactive', -- 'active', 'inactive', 'paused'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Strategy Signals
CREATE TABLE strategy_signals (
    id SERIAL PRIMARY KEY,
    signal_id VARCHAR(100) UNIQUE NOT NULL,
    strategy_id VARCHAR(100) REFERENCES strategies(strategy_id),
    symbol VARCHAR(20) NOT NULL,
    signal VARCHAR(20) NOT NULL, -- 'buy', 'sell', 'hold'
    strength DECIMAL(5,2), -- Signal strength 0-1
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Strategy Performance
CREATE TABLE strategy_performance (
    id SERIAL PRIMARY KEY,
    strategy_id VARCHAR(100) REFERENCES strategies(strategy_id),
    date DATE NOT NULL,
    returns DECIMAL(10,4),
    sharpe_ratio DECIMAL(8,4),
    max_drawdown DECIMAL(8,4),
    total_trades INTEGER,
    win_rate DECIMAL(5,2),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

#### Logging Tables
```sql
-- System Logs
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

-- Trading Logs
CREATE TABLE trading_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    trade_id VARCHAR(100),
    symbol VARCHAR(20),
    side VARCHAR(10),
    quantity DECIMAL(10,2),
    price DECIMAL(10,2),
    strategy VARCHAR(100),
    execution_time_ms INTEGER,
    status VARCHAR(50),
    error_message TEXT,
    correlation_id VARCHAR(100)
);

-- Performance Logs
CREATE TABLE performance_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    service VARCHAR(50),
    operation VARCHAR(100),
    execution_time_ms INTEGER,
    memory_usage_mb INTEGER,
    cpu_usage_percent DECIMAL(5,2),
    metadata JSONB
);
```

### Concurrent Database Access

#### Connection Pooling Strategy
```python
# Service-specific connection pools
class ServiceConnectionPool:
    def __init__(self, service_name: str, postgres_url: str):
        self.service_name = service_name
        self.engine = create_engine(
            postgres_url,
            poolclass=QueuePool,
            pool_size=10,           # Base connections per service
            max_overflow=20,        # Additional connections when needed
            pool_pre_ping=True,     # Validate connections
            pool_recycle=3600,      # Recycle connections hourly
            echo=False
        )
```

#### Event-Driven Data Synchronization
```python
# Data synchronization between services
class DataSyncEventBus:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)
    
    def publish_data_event(self, event_type: str, service: str, data: Dict[Any, Any]):
        """Publish data change event"""
        event = {
            'type': event_type,
            'service': service,
            'data': data,
            'timestamp': datetime.utcnow().isoformat()
        }
        self.redis.publish(f'data_sync:{event_type}', json.dumps(event))
```

## UI Architecture

### Design Philosophy

#### Core Principles
1. **Log-Driven Interface**: UI components are powered by structured log data from PostgreSQL
2. **Analysis-Focused**: Emphasis on monitoring, analysis, and configuration rather than trading execution
3. **No Real-time Requirements**: Periodic updates (5-10 minutes) align with hourly data ingestion
4. **No Trading Interface**: Automated trading decisions handled by strategy engine
5. **Simple & Maintainable**: HTMX + Plotly + Tailwind CSS for lightweight, responsive interface

#### Technology Stack
- **Backend**: FastAPI (Python web framework)
- **Frontend**: HTMX + Plotly + Tailwind CSS
- **Charts**: Plotly.js for financial visualizations
- **Database**: PostgreSQL (structured logs, trading data, system state)
- **Updates**: Periodic refresh (every 5-10 minutes)

### UI Components

#### 1. System Health Dashboard
```html
<!-- System Status from Logs -->
<div class="system-status" 
     hx-get="/api/logs/system-health" 
     hx-trigger="every 5m">
    <div class="status-grid">
        <div class="service-status">
            <h4>Data Ingestion</h4>
            <span class="status-indicator" data-service="data_ingestion">
                Loading...
            </span>
        </div>
        <div class="service-status">
            <h4>Strategy Engine</h4>
            <span class="status-indicator" data-service="strategy_engine">
                Loading...
            </span>
        </div>
        <div class="service-status">
            <h4>Execution Service</h4>
            <span class="status-indicator" data-service="execution">
                Loading...
            </span>
        </div>
    </div>
</div>
```

#### 2. Portfolio Analysis Interface
```html
<!-- Portfolio Dashboard -->
<div class="portfolio-dashboard">
    <div class="portfolio-summary">
        <h3>Portfolio Performance</h3>
        <div class="summary-metrics">
            <div class="metric">
                <span class="label">Total Value:</span>
                <span class="value" id="total-value">Loading...</span>
            </div>
            <div class="metric">
                <span class="label">Today's P&L:</span>
                <span class="value" id="daily-pnl">Loading...</span>
            </div>
            <div class="metric">
                <span class="label">Sharpe Ratio:</span>
                <span class="value" id="sharpe-ratio">Loading...</span>
            </div>
        </div>
    </div>
    
    <div class="portfolio-chart">
        <div id="portfolio-performance-chart" 
             hx-get="/api/portfolio/performance-chart" 
             hx-trigger="load, every 15m">
            Loading portfolio chart...
        </div>
    </div>
</div>
```

#### 3. Log Analysis Interface
```html
<!-- Log Viewer -->
<div class="log-viewer">
    <div class="log-controls">
        <div class="filter-group">
            <label>Service:</label>
            <select name="service" hx-get="/api/logs/filtered" hx-target="#log-content">
                <option value="">All Services</option>
                <option value="data_ingestion">Data Ingestion</option>
                <option value="strategy_engine">Strategy Engine</option>
                <option value="execution">Execution</option>
                <option value="risk_management">Risk Management</option>
                <option value="analytics">Analytics</option>
                <option value="notification">Notification</option>
            </select>
        </div>
        
        <div class="filter-group">
            <label>Log Level:</label>
            <select name="level">
                <option value="">All Levels</option>
                <option value="ERROR">ERROR</option>
                <option value="WARNING">WARNING</option>
                <option value="INFO">INFO</option>
                <option value="DEBUG">DEBUG</option>
            </select>
        </div>
        
        <div class="filter-group">
            <label>Time Range:</label>
            <select name="time_range">
                <option value="1h">Last Hour</option>
                <option value="24h">Last 24 Hours</option>
                <option value="7d">Last 7 Days</option>
            </select>
        </div>
    </div>
    
    <div id="log-content" 
         hx-get="/api/logs/recent" 
         hx-trigger="load, every 30s">
        Loading logs...
    </div>
</div>
```

### Backend API Architecture

#### Log-Driven API Endpoints
```python
# src/web/api/logs.py
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from src.shared.database.connection import get_db

router = APIRouter(prefix="/api/logs", tags=["logs"])

@router.get("/health/{service}")
async def get_service_health(service: str, db: Session = Depends(get_db)):
    """Get health status for a specific service from logs"""
    # Query system_logs for recent service activity
    # Return health indicators based on log patterns
    
@router.get("/performance/{service}")
async def get_service_performance(service: str, db: Session = Depends(get_db)):
    """Get performance metrics for a service from performance_logs"""
    # Query performance_logs table
    # Return execution times, memory usage, etc.
    
@router.get("/errors/summary")
async def get_error_summary(db: Session = Depends(get_db)):
    """Get error summary from system_logs"""
    # Query system_logs for ERROR level entries
    # Return error counts, trends, etc.
```

#### Trading Data Endpoints
```python
# src/web/api/trading.py
@router.get("/portfolio/summary")
async def get_portfolio_summary(db: Session = Depends(get_db)):
    """Get portfolio summary from positions and trades tables"""
    # Query positions table for current holdings
    # Calculate total value, P&L, etc.
    
@router.get("/strategies/list")
async def get_strategies_list(db: Session = Depends(get_db)):
    """Get list of strategies from strategies table"""
    # Query strategies table
    # Return active/inactive strategies
    
@router.get("/trading/activity")
async def get_trading_activity(db: Session = Depends(get_db)):
    """Get recent trading activity from trades table"""
    # Query trades table for recent activity
    # Return trade history, performance metrics
```

## Logging Architecture

> **📝 Detailed Logging Analysis**: For comprehensive logging architecture, structured logging patterns, and implementation strategies, see [Logging Architecture Detailed Review](logging.md).

### Logging Strategy
- **Loguru**: Consolidated logging across all services
- **Structured Logging**: JSON format for analysis
- **Log Levels**: DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Log Rotation**: Daily rotation, 30-day retention
- **Database Integration**: PostgreSQL tables for structured log storage

### Log Categories
```
📊 Trading Logs:     Trade executions, orders, positions
🔧 System Logs:      Service health, errors, startup/shutdown
⚡ Performance Logs: Execution times, memory usage
🧠 Strategy Logs:    Signal generation, backtesting results
⚠️  Risk Logs:       Risk calculations, violations, alerts
```

### Service-Specific Logging
| Service | Log Level | Focus Area |
|---------|-----------|------------|
| Data Ingestion | INFO | Market data fetch, validation |
| Strategy Engine | DEBUG | Signal generation, calculations |
| Execution | INFO | Order placement, trade execution |
| Risk Management | WARNING | Risk calculations, violations |
| Analytics | INFO | Performance calculations, reports |
| Notification | INFO | Alert delivery, communication |

## Prefect Orchestration Architecture

### Prefect 3.4.14 Integration Strategy

#### **Orchestration Philosophy**
- **Workflow-First**: All trading operations are Prefect flows
- **Service Coordination**: Prefect orchestrates microservice interactions
- **Scheduled Execution**: Time-based and event-driven flow execution
- **Error Handling**: Built-in retry, failure handling, and monitoring
- **State Management**: Prefect manages flow state and data passing

#### **Prefect Server Architecture**
```
┌─────────────────────────────────────────────────────────┐
│                Prefect Server                          │
│                (Port 4200)                             │
├─────────────────────────────────────────────────────────┤
│  Flow Management  │  Task Execution  │  Monitoring     │
│  ├── Deployments  │  ├── Work Pools  │  ├── UI         │
│  ├── Flow Runs    │  ├── Workers     │  ├── Logs       │
│  └── Schedules    │  └── Tasks       │  └── Metrics    │
└─────────────────────────────────────────────────────────┘
```

### Service-Specific Prefect Flows

#### **1. Data Ingestion Flows**
```python
@flow(name="fetch_market_data", retries=3, retry_delay_seconds=60)
def fetch_market_data(symbols: List[str], start_time: datetime):
    """Hourly market data collection from Alpaca API"""
    # Fetch data from Alpaca
    # Validate data quality
    # Store in PostgreSQL
    # Cache in Redis
    # Publish data events

@flow(name="validate_data_quality", retries=2)
def validate_data_quality(data: pd.DataFrame):
    """Data validation and quality checks"""
    # Check for missing values
    # Validate price ranges
    # Check volume consistency
    # Flag data quality issues

@flow(name="archive_old_data", schedule=CronSchedule(cron="0 2 * * *"))
def archive_old_data(retention_days: int = 90):
    """Daily data archival and cleanup"""
    # Archive old market data
    # Clean up temporary files
    # Update data retention policies
```

#### **2. Strategy Engine Flows**
```python
@flow(name="run_strategy", retries=2, timeout_seconds=300)
def run_strategy(strategy_id: str, symbols: List[str]):
    """Execute trading strategy logic"""
    # Load strategy configuration
    # Fetch required market data
    # Calculate technical indicators
    # Generate trading signals
    # Update strategy state

@flow(name="calculate_indicators", retries=1)
def calculate_indicators(symbol: str, lookback_period: int):
    """Technical indicator calculations"""
    # Fetch historical data
    # Calculate moving averages
    # Compute RSI, MACD, etc.
    # Store indicator values

@flow(name="generate_signals", retries=1)
def generate_signals(strategy_id: str, symbol: str):
    """Generate buy/sell signals based on strategy logic"""
    # Load strategy parameters
    # Analyze market conditions
    # Generate signal strength
    # Store signal in database

@flow(name="backtest_strategy", timeout_seconds=1800)
def backtest_strategy(strategy_id: str, start_date: datetime, end_date: datetime):
    """Historical strategy testing"""
    # Load historical data
    # Run strategy simulation
    # Calculate performance metrics
    # Generate backtest report
```

#### **3. Execution Service Flows**
```python
@flow(name="execute_trades", retries=3, retry_delay_seconds=30)
def execute_trades(signals: List[Dict]):
    """Process trading signals and execute trades"""
    # Validate signals
    # Check risk limits
    # Place orders with Alpaca
    # Update order status
    # Log execution details

@flow(name="manage_orders", retries=2)
def manage_orders():
    """Order lifecycle management"""
    # Check pending orders
    # Update order status
    # Handle partial fills
    # Process cancellations

@flow(name="update_positions", retries=1)
def update_positions():
    """Position tracking and P&L calculation"""
    # Fetch current positions
    # Calculate unrealized P&L
    # Update position records
    # Generate position reports

@flow(name="reconcile_trades", schedule=CronSchedule(cron="0 */6 * * *"))
def reconcile_trades():
    """Trade reconciliation with broker"""
    # Fetch trades from Alpaca
    # Compare with local records
    # Resolve discrepancies
    # Update trade status
```

#### **4. Risk Management Flows**
```python
@flow(name="calculate_position_size", retries=1)
def calculate_position_size(symbol: str, signal_strength: float):
    """Position sizing based on risk parameters"""
    # Load risk parameters
    # Calculate portfolio value
    # Determine position size
    # Validate against limits

@flow(name="validate_risk_limits", retries=1)
def validate_risk_limits(proposed_trade: Dict):
    """Risk limit validation before trade execution"""
    # Check position limits
    # Validate exposure limits
    # Check drawdown limits
    # Approve or reject trade

@flow(name="monitor_portfolio_risk", schedule=CronSchedule(cron="*/15 * * * *"))
def monitor_portfolio_risk():
    """Continuous portfolio risk monitoring"""
    # Calculate current exposure
    # Check risk metrics
    # Generate alerts if needed
    # Update risk dashboard

@flow(name="generate_risk_alerts", retries=2)
def generate_risk_alerts(risk_event: Dict):
    """Risk alert generation and notification"""
    # Format risk message
    # Send email alerts
    # Update risk dashboard
    # Log risk events
```

#### **5. Analytics Service Flows**
```python
@flow(name="calculate_performance", retries=1, timeout_seconds=600)
def calculate_performance(strategy_id: str, period: str):
    """Performance metrics calculation"""
    # Fetch trade data
    # Calculate returns
    # Compute Sharpe ratio
    # Calculate drawdown
    # Store performance metrics

@flow(name="generate_reports", schedule=CronSchedule(cron="0 18 * * *"))
def generate_reports():
    """Daily performance report generation"""
    # Calculate daily metrics
    # Generate performance charts
    # Create summary report
    # Send email reports

@flow(name="run_backtest", timeout_seconds=3600)
def run_backtest(strategy_config: Dict, start_date: datetime, end_date: datetime):
    """Comprehensive strategy backtesting"""
    # Load historical data
    # Run strategy simulation
    # Calculate performance metrics
    # Generate detailed report
    # Store backtest results

@flow(name="analyze_trades", retries=1)
def analyze_trades(strategy_id: str):
    """Trade pattern analysis"""
    # Fetch trade history
    # Analyze win/loss patterns
    # Calculate trade statistics
    # Identify improvement areas
```

#### **6. Notification Service Flows**
```python
@flow(name="send_trade_alerts", retries=3)
def send_trade_alerts(trade_data: Dict):
    """Trade execution notifications"""
    # Format trade message
    # Send email notification
    # Update dashboard
    # Log notification

@flow(name="monitor_system_health", schedule=CronSchedule(cron="*/5 * * * *"))
def monitor_system_health():
    """System health monitoring and alerting"""
    # Check service status
    # Monitor database connections
    # Check API availability
    # Send alerts if issues found

@flow(name="aggregate_logs", schedule=CronSchedule(cron="0 1 * * *"))
def aggregate_logs():
    """Daily log aggregation and analysis"""
    # Collect logs from all services
    # Analyze error patterns
    # Generate log summary
    # Clean up old logs

@flow(name="send_daily_summary", schedule=CronSchedule(cron="0 19 * * *"))
def send_daily_summary():
    """Daily trading summary email"""
    # Calculate daily P&L
    # Summarize trades
    # Generate performance metrics
    # Send summary email
```

### Prefect Flow Orchestration Patterns

#### **1. Sequential Flow Execution**
```python
@flow(name="trading_pipeline")
def trading_pipeline():
    """Complete trading pipeline execution"""
    # Step 1: Fetch market data
    market_data = fetch_market_data(symbols=["AAPL", "GOOGL"])
    
    # Step 2: Run strategies
    signals = run_strategy("momentum_strategy", ["AAPL", "GOOGL"])
    
    # Step 3: Validate risk
    approved_trades = validate_risk_limits(signals)
    
    # Step 4: Execute trades
    if approved_trades:
        execute_trades(approved_trades)
    
    # Step 5: Update positions
    update_positions()
    
    # Step 6: Send notifications
    send_trade_alerts(approved_trades)
```

#### **2. Parallel Flow Execution**
```python
@flow(name="parallel_analytics")
def parallel_analytics():
    """Run analytics flows in parallel"""
    with Flow("parallel_analytics") as flow:
        # Run these flows in parallel
        performance_task = calculate_performance.submit("strategy_1", "1M")
        backtest_task = run_backtest.submit(strategy_config, start_date, end_date)
        analysis_task = analyze_trades.submit("strategy_1")
        
        # Wait for all to complete
        results = [performance_task, backtest_task, analysis_task]
        return results
```

#### **3. Conditional Flow Execution**
```python
@flow(name="conditional_trading")
def conditional_trading(market_condition: str):
    """Conditional trading based on market conditions"""
    if market_condition == "volatile":
        # Run conservative strategy
        run_strategy("conservative_strategy")
    elif market_condition == "stable":
        # Run aggressive strategy
        run_strategy("aggressive_strategy")
    else:
        # Run default strategy
        run_strategy("default_strategy")
```

## Prefect Deployment Strategy

### Prefect 3.4.14 Deployment Architecture

#### **Deployment Overview**
Prefect 3.4.14 will be deployed as a self-hosted server with PostgreSQL backend, providing workflow orchestration for all trading system microservices.

#### **Prefect Server Architecture**
```
┌─────────────────────────────────────────────────────────┐
│                Prefect Server                          │
│                (Port 4200)                             │
├─────────────────────────────────────────────────────────┤
│  API Server    │  UI Server    │  Database             │
│  ├── REST API  │  ├── Web UI   │  ├── Flow Runs        │
│  ├── GraphQL   │  ├── Dashboard│  ├── Task Runs        │
│  └── WebSocket │  └── Explorer │  ├── Deployments      │
│                                     ├── Work Pools      │
│                                     └── Blocks          │
└─────────────────────────────────────────────────────────┘
```

### Prefect Local Development Deployment

#### **Local Development Setup (Recommended)**
```bash
# Start Prefect server locally
prefect server start --host 0.0.0.0 --port 4200

# Configure database
prefect config set PREFECT_API_DATABASE_CONNECTION_URL="postgresql+asyncpg://postgres:password@localhost:5432/prefect"

# Initialize database
prefect database upgrade
```

**Benefits:**
- Simple setup and management
- Direct access to local services
- Easy debugging and development
- No additional infrastructure
- Perfect for development and testing

### Prefect Configuration

#### **Prefect Server Configuration**
```yaml
# prefect.yaml
prefect:
  api:
    database:
      connection_url: "postgresql+asyncpg://postgres:password@localhost:5432/prefect"
      echo: false
      pool_size: 10
      max_overflow: 20
      pool_pre_ping: true
      pool_recycle: 3600
  
  server:
    host: "0.0.0.0"
    port: 4200
    ui:
      enabled: true
      host: "0.0.0.0"
      port: 4200
  
  work_pools:
    - name: "trading-pool"
      type: "process"
      base_job_template:
        job_configuration:
          command: "python -m src.services.{service}.main"
          env:
            PREFECT_API_URL: "http://localhost:4200/api"
            POSTGRES_HOST: "localhost"
            REDIS_HOST: "localhost"
```

#### **Environment Configuration**
```env
# Prefect Configuration
PREFECT_API_URL=http://localhost:4200/api
PREFECT_API_DATABASE_CONNECTION_URL=postgresql+asyncpg://postgres:password@localhost:5432/prefect
PREFECT_LOGGING_LEVEL=INFO
PREFECT_LOGGING_TO_API_ENABLED=true
PREFECT_SERVER_API_HOST=0.0.0.0
PREFECT_UI_URL=http://localhost:4200
```

### Prefect Work Pool Configuration

#### **Trading System Work Pools**
```python
# src/shared/prefect/work_pools.py
from prefect import get_client
from prefect.client.schemas.actions import WorkPoolCreate

async def setup_work_pools():
    """Setup work pools for trading system services"""
    async with get_client() as client:
        # Data Ingestion Pool
        await client.create_work_pool(
            WorkPoolCreate(
                name="data-ingestion-pool",
                type="process",
                base_job_template={
                    "job_configuration": {
                        "command": "python -m src.services.data_ingestion.main",
                        "env": {
                            "PREFECT_API_URL": "http://localhost:4200/api",
                            "SERVICE_NAME": "data_ingestion"
                        }
                    }
                }
            )
        )
        
        # Strategy Engine Pool
        await client.create_work_pool(
            WorkPoolCreate(
                name="strategy-engine-pool",
                type="process",
                base_job_template={
                    "job_configuration": {
                        "command": "python -m src.services.strategy_engine.main",
                        "env": {
                            "PREFECT_API_URL": "http://localhost:4200/api",
                            "SERVICE_NAME": "strategy_engine"
                        }
                    }
                }
            )
        )
        
        # Execution Pool
        await client.create_work_pool(
            WorkPoolCreate(
                name="execution-pool",
                type="process",
                base_job_template={
                    "job_configuration": {
                        "command": "python -m src.services.execution.main",
                        "env": {
                            "PREFECT_API_URL": "http://localhost:4200/api",
                            "SERVICE_NAME": "execution"
                        }
                    }
                }
            )
        )
```

### Prefect Flow Deployment

#### **Flow Deployment Strategy**
```python
# src/shared/prefect/deployments.py
from prefect import flow
from prefect.deployments import Deployment
from prefect.server.schemas.schedules import CronSchedule

def deploy_trading_flows():
    """Deploy all trading system flows"""
    
    # Data Ingestion Flows
    fetch_market_data_deployment = Deployment.build_from_flow(
        flow=fetch_market_data,
        name="fetch-market-data",
        schedule=CronSchedule(cron="0 * * * *"),  # Every hour
        work_pool_name="data-ingestion-pool",
        tags=["data-ingestion", "scheduled"]
    )
    
    # Strategy Engine Flows
    run_strategy_deployment = Deployment.build_from_flow(
        flow=run_strategy,
        name="run-strategy",
        schedule=CronSchedule(cron="5 * * * *"),  # 5 minutes after hour
        work_pool_name="strategy-engine-pool",
        tags=["strategy", "scheduled"]
    )
    
    # Execution Flows
    execute_trades_deployment = Deployment.build_from_flow(
        flow=execute_trades,
        name="execute-trades",
        work_pool_name="execution-pool",
        tags=["execution", "triggered"]
    )
    
    # Deploy all flows
    fetch_market_data_deployment.apply()
    run_strategy_deployment.apply()
    execute_trades_deployment.apply()
```

### Prefect Monitoring & Observability

#### **Flow Monitoring Configuration**
```python
# src/shared/prefect/monitoring.py
from prefect import get_client
from prefect.events import emit_event

class PrefectMonitoring:
    def __init__(self):
        self.client = get_client()
    
    async def monitor_flow_runs(self):
        """Monitor flow run status and performance"""
        async with self.client:
            # Get recent flow runs
            flow_runs = await self.client.read_flow_runs(
                limit=100,
                sort="START_TIME_DESC"
            )
            
            # Check for failed runs
            failed_runs = [run for run in flow_runs if run.state_type == "FAILED"]
            
            if failed_runs:
                await self.handle_failed_runs(failed_runs)
    
    async def handle_failed_runs(self, failed_runs):
        """Handle failed flow runs"""
        for run in failed_runs:
            # Emit failure event
            await emit_event(
                event="flow-run-failed",
                resource={"prefect.resource.id": f"prefect.flow-run.{run.id}"},
                payload={
                    "flow_name": run.name,
                    "error_message": run.state.message,
                    "start_time": run.start_time,
                    "end_time": run.end_time
                }
            )
```

### Prefect Security Configuration

#### **Database Security**
```sql
-- Create Prefect database user
CREATE USER prefect_user WITH PASSWORD 'prefect_password';

-- Grant permissions
GRANT CONNECT ON DATABASE prefect TO prefect_user;
GRANT USAGE ON SCHEMA public TO prefect_user;
GRANT CREATE ON SCHEMA public TO prefect_user;

-- Grant table permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO prefect_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO prefect_user;
```

#### **API Security**
```python
# src/shared/prefect/security.py
from prefect.server.api.server import create_app
from prefect.server.database import get_database_engine
from prefect.settings import PREFECT_API_KEY

def configure_prefect_security():
    """Configure Prefect security settings"""
    
    # API Key authentication
    if PREFECT_API_KEY:
        app = create_app()
        app.add_middleware(
            APIKeyMiddleware,
            api_key=PREFECT_API_KEY
        )
    
    # CORS configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:8000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
```

### Prefect Deployment Scripts

#### **Prefect Server Startup Script**
```bash
#!/bin/bash
# start_prefect.sh

echo "Starting Prefect Server..."

# Check if PostgreSQL is running
if ! pg_isready -h localhost -p 5432; then
    echo "PostgreSQL is not running. Please start PostgreSQL first."
    exit 1
fi

# Check if Prefect database exists
if ! psql -h localhost -U postgres -lqt | cut -d \| -f 1 | grep -qw prefect; then
    echo "Creating Prefect database..."
    createdb -h localhost -U postgres prefect
fi

# Configure Prefect
echo "Configuring Prefect..."
prefect config set PREFECT_API_DATABASE_CONNECTION_URL="postgresql+asyncpg://postgres:password@localhost:5432/prefect"
prefect config set PREFECT_API_URL="http://localhost:4200/api"

# Initialize database
echo "Initializing Prefect database..."
prefect database upgrade

# Start Prefect server
echo "Starting Prefect server..."
prefect server start --host 0.0.0.0 --port 4200 --log-level INFO
```

#### **Prefect Worker Startup Script**
```bash
#!/bin/bash
# start_prefect_worker.sh

echo "Starting Prefect Worker..."

# Check if Prefect server is running
if ! curl -s http://localhost:4200/api/health > /dev/null; then
    echo "Prefect server is not running. Please start Prefect server first."
    exit 1
fi

# Start worker
echo "Starting Prefect worker..."
prefect worker start --pool trading-pool --limit 10
```

### Prefect Troubleshooting

#### **Common Issues and Solutions**

**1. Database Connection Issues**
```bash
# Check database connection
psql -h localhost -U postgres -d prefect -c "SELECT 1;"

# Check Prefect database tables
psql -h localhost -U postgres -d prefect -c "\dt"
```

**2. Flow Deployment Issues**
```bash
# Check flow deployments
prefect deployment ls

# Check work pools
prefect work-pool ls

# Check workers
prefect worker ls
```

**3. Flow Run Issues**
```bash
# Check flow runs
prefect flow-run ls

# Check specific flow run
prefect flow-run inspect <flow-run-id>

# Check flow run logs
prefect flow-run logs <flow-run-id>
```

### Prefect Performance Optimization

#### **Database Optimization**
```sql
-- Create indexes for Prefect tables
CREATE INDEX idx_flow_runs_state_type ON flow_run(state_type);
CREATE INDEX idx_flow_runs_start_time ON flow_run(start_time);
CREATE INDEX idx_task_runs_state_type ON task_run(state_type);
CREATE INDEX idx_task_runs_start_time ON task_run(start_time);
```

#### **Connection Pooling**
```python
# src/shared/prefect/connection_pool.py
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

def create_prefect_engine():
    """Create optimized Prefect database engine"""
    return create_engine(
        "postgresql+asyncpg://postgres:password@localhost:5432/prefect",
        poolclass=QueuePool,
        pool_size=10,
        max_overflow=20,
        pool_pre_ping=True,
        pool_recycle=3600,
        echo=False
    )
```

### Prefect Backup and Recovery

#### **Database Backup**
```bash
#!/bin/bash
# backup_prefect.sh

echo "Backing up Prefect database..."

# Create backup
pg_dump -h localhost -U postgres -d prefect > prefect_backup_$(date +%Y%m%d_%H%M%S).sql

echo "Prefect database backup completed."
```

#### **Flow Configuration Backup**
```bash
#!/bin/bash
# backup_prefect_config.sh

echo "Backing up Prefect configuration..."

# Export flows
prefect flow ls --format json > flows_backup_$(date +%Y%m%d_%H%M%S).json

# Export deployments
prefect deployment ls --format json > deployments_backup_$(date +%Y%m%d_%H%M%S).json

echo "Prefect configuration backup completed."
```

### Prefect Monitoring & Observability

#### **Flow Monitoring**
- **Flow Run Status**: Real-time flow execution status
- **Task Dependencies**: Visual flow dependency graphs
- **Performance Metrics**: Execution time, success rates
- **Error Tracking**: Detailed error logs and stack traces
- **Retry Logic**: Automatic retry with exponential backoff

#### **Prefect UI Features**
- **Flow Dashboard**: Visual flow execution monitoring
- **Log Viewer**: Real-time log streaming
- **Metrics Dashboard**: Performance and usage metrics
- **Flow Editor**: Visual flow creation and editing
- **Deployment Management**: Flow deployment and scheduling

## Communication Patterns

### Service Communication
- **Synchronous**: REST APIs for real-time requests
- **Asynchronous**: Redis pub/sub for events
- **Batch Processing**: Prefect flows for scheduled tasks
- **Data Synchronization**: Event-driven updates between services

### Message Flow
```
Data Ingestion → Strategy Engine → Risk Management → Execution
     ↓                ↓                ↓              ↓
Analytics Service ← Notification Service ← Redis ← PostgreSQL
```

### Prefect Flow Orchestration
```
Market Data Flow → Strategy Flow → Risk Flow → Execution Flow
       ↓               ↓            ↓           ↓
   Analytics Flow ← Notification Flow ← Monitoring Flow
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
mypy .
```

### Testing Strategy
- **Unit Tests**: Individual service functions
- **Integration Tests**: Service interactions
- **End-to-End Tests**: Complete trading workflows
- **Strategy Tests**: Backtesting validation

## Deployment Architecture

### Local Deployment Strategy

#### **Deployment Overview**
The trading system is designed for local deployment on Windows 10, providing a complete self-contained trading environment with all services running on a single machine.

#### **System Architecture**
```
┌─────────────────────────────────────────────────────────┐
│                    Local Machine                        │
│                  (Windows 10)                          │
├─────────────────────────────────────────────────────────┤
│  Infrastructure Layer                                   │
│  ├── PostgreSQL (Port 5432)                            │
│  ├── Redis (Port 6379)                                 │
│  └── Prefect Server (Port 4200)                        │
├─────────────────────────────────────────────────────────┤
│  Microservices Layer                                    │
│  ├── Data Ingestion    │  Strategy Engine              │
│  ├── Execution Service │  Risk Management              │
│  └── Analytics Service │  Notification Service         │
├─────────────────────────────────────────────────────────┤
│  Web Layer                                              │
│  ├── FastAPI Web Server (Port 8000)                    │
│  └── Frontend (HTMX + Plotly + Tailwind CSS)          │
└─────────────────────────────────────────────────────────┘
```

### Service Deployment Strategy

#### **1. Infrastructure Services**
```yaml
# Infrastructure deployment order
infrastructure:
  - postgresql:     # Database server
    port: 5432
    databases: [trading_system, prefect]
    schemas: [data_ingestion, strategy_engine, execution, risk_management, analytics, notification, logging]
  
  - redis:          # Cache and message queue
    port: 6379
    databases: [0, 1, 2, 3, 4, 5]
  
  - prefect:        # Workflow orchestration
    port: 4200
    database: prefect
    ui_enabled: true
```

#### **2. Microservices Deployment**
```yaml
# Microservices deployment configuration
microservices:
  data_ingestion:
    port: 8001
    database_schema: data_ingestion
    dependencies: [postgresql, redis]
    prefect_flows: [fetch_market_data, validate_data_quality, archive_old_data]
  
  strategy_engine:
    port: 8002
    database_schema: strategy_engine
    dependencies: [postgresql, redis]
    prefect_flows: [run_strategy, calculate_indicators, generate_signals, backtest_strategy]
  
  execution:
    port: 8003
    database_schema: execution
    dependencies: [postgresql, redis, alpaca_api]
    prefect_flows: [execute_trades, manage_orders, update_positions, reconcile_trades]
  
  risk_management:
    port: 8004
    database_schema: risk_management
    dependencies: [postgresql, redis]
    prefect_flows: [calculate_position_size, validate_risk_limits, monitor_portfolio_risk, generate_risk_alerts]
  
  analytics:
    port: 8005
    database_schema: analytics
    dependencies: [postgresql, redis]
    prefect_flows: [calculate_performance, generate_reports, run_backtest, analyze_trades]
  
  notification:
    port: 8006
    database_schema: notification
    dependencies: [postgresql, redis, email_service]
    prefect_flows: [send_trade_alerts, monitor_system_health, aggregate_logs, send_daily_summary]
```

#### **3. Web Layer Deployment**
```yaml
# Web layer deployment
web_layer:
  fastapi_server:
    port: 8000
    dependencies: [all_microservices, postgresql, redis]
    endpoints: [api, health, metrics, logs]
  
  frontend:
    technology: [htmx, plotly, tailwind_css]
    static_files: [css, js, images]
    api_integration: fastapi_server
```

### Deployment Phases

#### **Phase 1: Infrastructure Setup**
```bash
# 1. Start PostgreSQL
pg_ctl start -D "C:\Program Files\PostgreSQL\15\data"

# 2. Start Redis
redis-server

# 3. Initialize Prefect
prefect server start
```

#### **Phase 2: Database Initialization**
```bash
# 1. Create databases
createdb trading_system
createdb prefect

# 2. Run database migrations
alembic upgrade head

# 3. Initialize Prefect database
prefect database upgrade
```

#### **Phase 3: Microservices Deployment**
```bash
# 1. Start microservices in parallel
python -m src.services.data_ingestion.main &
python -m src.services.strategy_engine.main &
python -m src.services.execution.main &
python -m src.services.risk_management.main &
python -m src.services.analytics.main &
python -m src.services.notification.main &

# 2. Verify service health
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health
curl http://localhost:8004/health
curl http://localhost:8005/health
curl http://localhost:8006/health
```

#### **Phase 4: Web Layer Deployment**
```bash
# 1. Start FastAPI server
python -m src.web.main

# 2. Verify web server
curl http://localhost:8000/health
```

### Service Startup Order
1. **Infrastructure**: PostgreSQL → Redis → Prefect Server
2. **Database**: Create databases → Run migrations → Initialize Prefect
3. **Microservices**: Start all services in parallel
4. **Web Layer**: FastAPI server → Frontend
5. **Verification**: Health checks → Service discovery → Flow deployment

### Deployment Configuration

#### **Environment Variables**
```env
# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
TRADING_DB_NAME=trading_system
PREFECT_DB_NAME=prefect
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password_here

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_URL=redis://localhost:6379/0

# Prefect Configuration
PREFECT_API_URL=http://localhost:4200/api
PREFECT_API_DATABASE_CONNECTION_URL=postgresql+asyncpg://postgres:password@localhost:5432/prefect

# Service Configuration
DATA_INGESTION_PORT=8001
STRATEGY_ENGINE_PORT=8002
EXECUTION_PORT=8003
RISK_MANAGEMENT_PORT=8004
ANALYTICS_PORT=8005
NOTIFICATION_PORT=8006
WEB_SERVER_PORT=8000

# Alpaca API Configuration
ALPACA_API_KEY=your_api_key
ALPACA_SECRET_KEY=your_secret_key
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# Logging Configuration
LOG_LEVEL=INFO
LOG_RETENTION_DAYS=30
```


### Deployment Scripts

#### **Startup Script**
```bash
#!/bin/bash
# start_trading_system.sh

echo "Starting Trading System..."

# Phase 1: Infrastructure
echo "Starting infrastructure services..."
pg_ctl start -D "C:\Program Files\PostgreSQL\15\data"
redis-server --daemonize yes
prefect server start --host 0.0.0.0 --port 4200 &

# Wait for services to be ready
sleep 10

# Phase 2: Database initialization
echo "Initializing databases..."
createdb trading_system
createdb prefect
alembic upgrade head
prefect database upgrade

# Phase 3: Start microservices
echo "Starting microservices..."
python -m src.services.data_ingestion.main &
python -m src.services.strategy_engine.main &
python -m src.services.execution.main &
python -m src.services.risk_management.main &
python -m src.services.analytics.main &
python -m src.services.notification.main &

# Wait for services to be ready
sleep 15

# Phase 4: Start web server
echo "Starting web server..."
python -m src.web.main &

echo "Trading system started successfully!"
echo "Web UI: http://localhost:8000"
echo "Prefect UI: http://localhost:4200"
```

#### **Shutdown Script**
```bash
#!/bin/bash
# stop_trading_system.sh

echo "Stopping Trading System..."

# Stop web server
pkill -f "src.web.main"

# Stop microservices
pkill -f "src.services"

# Stop Prefect
pkill -f "prefect server"

# Stop Redis
redis-cli shutdown

# Stop PostgreSQL
pg_ctl stop -D "C:\Program Files\PostgreSQL\15\data"

echo "Trading system stopped successfully!"
```

### Health Monitoring

#### **Service Health Checks**
```python
# src/shared/health/health_checker.py
class HealthChecker:
    def __init__(self):
        self.services = {
            'postgresql': 'localhost:5432',
            'redis': 'localhost:6379',
            'prefect': 'localhost:4200',
            'data_ingestion': 'localhost:8001',
            'strategy_engine': 'localhost:8002',
            'execution': 'localhost:8003',
            'risk_management': 'localhost:8004',
            'analytics': 'localhost:8005',
            'notification': 'localhost:8006',
            'web_server': 'localhost:8000'
        }
    
    def check_all_services(self):
        """Check health of all services"""
        health_status = {}
        for service, endpoint in self.services.items():
            try:
                response = requests.get(f"http://{endpoint}/health", timeout=5)
                health_status[service] = response.status_code == 200
            except:
                health_status[service] = False
        return health_status
```

#### **Deployment Verification**
```python
# src/scripts/verify_deployment.py
def verify_deployment():
    """Verify all services are running correctly"""
    health_checker = HealthChecker()
    health_status = health_checker.check_all_services()
    
    all_healthy = all(health_status.values())
    
    if all_healthy:
        print("✅ All services are healthy!")
        return True
    else:
        print("❌ Some services are unhealthy:")
        for service, status in health_status.items():
            print(f"  {service}: {'✅' if status else '❌'}")
        return False
```

### Production Considerations

#### **Performance Optimization**
- **Connection Pooling**: Optimize database connections
- **Caching Strategy**: Implement Redis caching
- **Resource Monitoring**: Monitor CPU, memory, disk usage
- **Log Rotation**: Implement log rotation and cleanup

#### **Security Hardening**
- **API Keys**: Secure storage of Alpaca API keys
- **Database Security**: Proper user permissions
- **Network Security**: Firewall configuration
- **Audit Logging**: Complete audit trail

#### **Backup Strategy**
- **Database Backups**: Daily automated backups
- **Configuration Backups**: Version control for configurations
- **Log Backups**: Centralized log storage
- **Disaster Recovery**: Recovery procedures and testing

### Deployment Checklist

#### **Pre-Deployment**
- [ ] PostgreSQL installed and configured
- [ ] Redis installed and configured
- [ ] Python environment set up
- [ ] Dependencies installed
- [ ] Environment variables configured
- [ ] Alpaca API keys obtained

#### **Deployment**
- [ ] Infrastructure services started
- [ ] Databases created and migrated
- [ ] Microservices deployed
- [ ] Web server started
- [ ] Health checks passed
- [ ] Prefect flows deployed

#### **Post-Deployment**
- [ ] All services responding
- [ ] Database connections working
- [ ] Prefect UI accessible
- [ ] Trading system functional
- [ ] Monitoring configured
- [ ] Backup procedures tested

## Timezone Strategy

### Overview
The trading system handles three primary timezones to ensure accurate data processing, trading operations, and user experience:

- **UTC**: Universal storage and vendor data (database storage)
- **EST/EDT**: Trading operations (market timezone)
- **CST/CDT**: User interface (your local timezone)

### Core Principles

1. **Storage**: All timestamps stored in UTC in database
2. **Processing**: Internal operations use UTC
3. **Display**: Convert to user's timezone (Central) for UI
4. **Trading**: Convert to market timezone (Eastern) for trading operations
5. **Vendor Data**: Handle incoming UTC data from external sources

### Timezone Configuration

#### Environment Variables
```env
# Timezone Configuration
DEFAULT_TIMEZONE=UTC
USER_TIMEZONE=America/Chicago
TRADING_TIMEZONE=America/New_York
VENDOR_TIMEZONE=UTC
```

#### Timezone Constants
```python
# src/shared/utils/timezone.py
from zoneinfo import ZoneInfo

# Timezone definitions
UTC = ZoneInfo("UTC")
CENTRAL = ZoneInfo("America/Chicago")
EASTERN = ZoneInfo("America/New_York")

# Timezone aliases for clarity
USER_TIMEZONE = CENTRAL
TRADING_TIMEZONE = EASTERN
STORAGE_TIMEZONE = UTC
```

### Reusable Utility Functions

#### 1. Timezone Configuration
```python
def get_central_timezone() -> ZoneInfo:
    """Get Central timezone (user's local timezone)"""
    return ZoneInfo("America/Chicago")

def get_eastern_timezone() -> ZoneInfo:
    """Get Eastern timezone (trading timezone)"""
    return ZoneInfo("America/New_York")

def get_utc_timezone() -> ZoneInfo:
    """Get UTC timezone (storage timezone)"""
    return ZoneInfo("UTC")

# Current time in different timezones
def now_utc() -> datetime:
    """Get current time in UTC"""
    return datetime.now(UTC)

def now_central() -> datetime:
    """Get current time in Central timezone"""
    return datetime.now(CENTRAL)

def now_eastern() -> datetime:
    """Get current time in Eastern timezone"""
    return datetime.now(EASTERN)
```

#### 2. Conversion Functions
```python
def to_utc(dt: datetime, tz: ZoneInfo) -> datetime:
    """Convert datetime to UTC"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=tz)
    return dt.astimezone(UTC)

def to_central(dt: datetime) -> datetime:
    """Convert datetime to Central timezone"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(CENTRAL)

def to_eastern(dt: datetime) -> datetime:
    """Convert datetime to Eastern timezone"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=UTC)
    return dt.astimezone(EASTERN)

def convert_timezone(dt: datetime, from_tz: ZoneInfo, to_tz: ZoneInfo) -> datetime:
    """Convert datetime between timezones"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=from_tz)
    return dt.astimezone(to_tz)

# Smart conversion (detects source timezone)
def smart_convert_to_utc(dt: datetime) -> datetime:
    """Smart conversion to UTC, handling naive datetimes"""
    if dt.tzinfo is None:
        # Assume naive datetime is in UTC
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)

def smart_convert_to_central(dt: datetime) -> datetime:
    """Smart conversion to Central timezone"""
    utc_dt = smart_convert_to_utc(dt)
    return utc_dt.astimezone(CENTRAL)

def smart_convert_to_eastern(dt: datetime) -> datetime:
    """Smart conversion to Eastern timezone"""
    utc_dt = smart_convert_to_utc(dt)
    return utc_dt.astimezone(EASTERN)
```

#### 3. Trading-Specific Utilities
```python
def is_market_hours(dt: datetime) -> bool:
    """Check if datetime is during market hours (9:30 AM - 4:00 PM EST)"""
    eastern_dt = to_eastern(dt)
    market_open = eastern_dt.replace(hour=9, minute=30, second=0, microsecond=0)
    market_close = eastern_dt.replace(hour=16, minute=0, second=0, microsecond=0)
    
    # Check if it's a weekday
    if eastern_dt.weekday() >= 5:  # Saturday = 5, Sunday = 6
        return False
    
    return market_open <= eastern_dt <= market_close

def get_next_market_open(dt: datetime) -> datetime:
    """Get next market open time in UTC"""
    eastern_dt = to_eastern(dt)
    next_open = eastern_dt.replace(hour=9, minute=30, second=0, microsecond=0)
    
    # If it's past today's market open, get tomorrow's
    if eastern_dt.time() > next_open.time():
        next_open += timedelta(days=1)
    
    # Skip weekends
    while next_open.weekday() >= 5:
        next_open += timedelta(days=1)
    
    return to_utc(next_open, EASTERN)

def get_last_market_close(dt: datetime) -> datetime:
    """Get last market close time in UTC"""
    eastern_dt = to_eastern(dt)
    last_close = eastern_dt.replace(hour=16, minute=0, second=0, microsecond=0)
    
    # If it's before today's market close, get yesterday's
    if eastern_dt.time() < last_close.time():
        last_close -= timedelta(days=1)
    
    # Skip weekends
    while last_close.weekday() >= 5:
        last_close -= timedelta(days=1)
    
    return to_utc(last_close, EASTERN)

def get_trading_day(dt: datetime) -> date:
    """Get trading day for a given datetime"""
    eastern_dt = to_eastern(dt)
    
    # If before market open, use previous trading day
    if eastern_dt.time() < time(9, 30):
        eastern_dt -= timedelta(days=1)
    
    # Skip weekends
    while eastern_dt.weekday() >= 5:
        eastern_dt -= timedelta(days=1)
    
    return eastern_dt.date()

# Timezone-aware business logic
def get_trading_timestamp(dt: datetime) -> datetime:
    """Convert to EST for trading operations"""
    return to_eastern(dt)

def get_display_timestamp(dt: datetime) -> datetime:
    """Convert to Central for UI display"""
    return to_central(dt)
```

#### 4. Data Processing Utilities
```python
def normalize_vendor_timestamp(dt: datetime, vendor_tz: str = "UTC") -> datetime:
    """Normalize vendor timestamp to UTC"""
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
    
    if dt.tzinfo is None:
        # Assume vendor timezone
        vendor_zone = ZoneInfo(vendor_tz)
        dt = dt.replace(tzinfo=vendor_zone)
    
    return dt.astimezone(UTC)

def process_market_data_timestamps(data: List[Dict]) -> List[Dict]:
    """Process market data timestamps to UTC"""
    processed_data = []
    for record in data:
        if 'timestamp' in record:
            record['timestamp'] = normalize_vendor_timestamp(record['timestamp'])
        processed_data.append(record)
    return processed_data

# Database operations
def ensure_utc_timestamp(dt: datetime) -> datetime:
    """Ensure timestamp is in UTC for database storage"""
    if dt.tzinfo is None:
        # Assume naive datetime is in UTC
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)

def format_for_database(dt: datetime) -> datetime:
    """Format timestamp for database storage (UTC)"""
    return ensure_utc_timestamp(dt)
```

#### 5. Logging and Display
```python
def log_with_timezone(message: str, level: str, tz: ZoneInfo = None):
    """Log message with timezone context"""
    if tz is None:
        tz = CENTRAL  # Default to user timezone
    
    timestamp = datetime.now(tz)
    formatted_message = f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S %Z')}] {message}"
    
    # Use appropriate log level
    if level.upper() == "ERROR":
        logger.error(formatted_message)
    elif level.upper() == "WARNING":
        logger.warning(formatted_message)
    elif level.upper() == "INFO":
        logger.info(formatted_message)
    else:
        logger.debug(formatted_message)

def format_timestamp_for_logging(dt: datetime) -> str:
    """Format timestamp for logging with timezone info"""
    central_dt = to_central(dt)
    return central_dt.strftime('%Y-%m-%d %H:%M:%S %Z')

# UI formatting
def format_for_display(dt: datetime, format_str: str = None) -> str:
    """Format timestamp for UI display"""
    if format_str is None:
        format_str = '%Y-%m-%d %H:%M:%S %Z'
    
    central_dt = to_central(dt)
    return central_dt.strftime(format_str)

def format_trading_time(dt: datetime) -> str:
    """Format timestamp for trading context (Eastern)"""
    eastern_dt = to_eastern(dt)
    return eastern_dt.strftime('%Y-%m-%d %H:%M:%S %Z')
```

#### 6. Validation and Error Handling
```python
class TimezoneError(Exception):
    """Custom exception for timezone-related errors"""
    pass

def validate_timezone_aware(dt: datetime) -> bool:
    """Validate that datetime is timezone-aware"""
    return dt.tzinfo is not None

def ensure_timezone_aware(dt: datetime, default_tz: ZoneInfo = None) -> datetime:
    """Ensure datetime is timezone-aware"""
    if dt.tzinfo is None:
        if default_tz is None:
            default_tz = UTC
        return dt.replace(tzinfo=default_tz)
    return dt

def handle_timezone_conversion_error(dt: datetime, target_tz: ZoneInfo) -> datetime:
    """Handle timezone conversion errors gracefully"""
    try:
        return dt.astimezone(target_tz)
    except Exception as e:
        logger.error(f"Timezone conversion error: {e}")
        # Fallback to UTC
        return ensure_timezone_aware(dt, UTC).astimezone(target_tz)
```

### Database Integration

#### Updated Database Mixins
```python
# src/shared/database/mixins.py
from src.shared.utils.timezone import ensure_utc_timestamp

class TimestampMixin:
    """Adds timezone-aware created_at timestamp to models"""
    
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        comment="Timestamp when record was created (UTC)",
    )
    
    def set_created_at(self, dt: datetime = None):
        """Set created_at timestamp in UTC"""
        if dt is None:
            dt = datetime.now()
        self.created_at = ensure_utc_timestamp(dt)

class UpdateTimestampMixin(TimestampMixin):
    """Adds timezone-aware created_at and updated_at timestamps to models"""
    
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
        comment="Timestamp when record was last updated (UTC)",
    )
    
    def set_updated_at(self, dt: datetime = None):
        """Set updated_at timestamp in UTC"""
        if dt is None:
            dt = datetime.now()
        self.updated_at = ensure_utc_timestamp(dt)
```

### API Response Formatting

#### Timezone-Aware API Responses
```python
# src/web/api/timezone_helpers.py
from src.shared.utils.timezone import to_central, format_for_display

def format_api_timestamp(dt: datetime) -> str:
    """Format timestamp for API responses (Central timezone)"""
    return format_for_display(dt)

def format_trading_timestamp(dt: datetime) -> str:
    """Format timestamp for trading context (Eastern timezone)"""
    return format_trading_time(dt)

# Pydantic model with timezone conversion
class TimestampResponse(BaseModel):
    timestamp: str
    timezone: str = "America/Chicago"  # Central timezone
    
    @classmethod
    def from_datetime(cls, dt: datetime):
        return cls(
            timestamp=format_for_display(dt),
            timezone="America/Chicago"
        )
```

### Usage Examples

#### Data Ingestion (Vendor sends UTC)
```python
# Vendor data comes in UTC
vendor_data = {"timestamp": "2024-01-15T14:30:00Z"}
utc_time = normalize_vendor_timestamp(parse_iso(vendor_data["timestamp"]))

# Store in database (already UTC)
db_record = {"timestamp": utc_time}
```

#### Trading Operations (Convert to EST)
```python
# Convert to Eastern for trading
trading_time = get_trading_timestamp(utc_time)

# Check if market is open
if is_market_hours(trading_time):
    # Execute trade
    execute_trade(symbol, quantity, price, trading_time)
```

#### UI Display (Convert to Central)
```python
# Convert to Central for display
display_time = get_display_timestamp(utc_time)

# Format for UI
formatted_time = format_for_display(display_time)
```

#### Logging (With timezone context)
```python
# Log with timezone context
log_with_timezone(f"Trade executed at {trading_time}", "INFO")

# Format timestamp for logging
log_timestamp = format_timestamp_for_logging(utc_time)
```

### Benefits

1. **Consistency**: All timestamps handled uniformly across the system
2. **Clarity**: Explicit timezone conversions with clear function names
3. **Maintainability**: Centralized timezone logic in utility functions
4. **Reliability**: Robust error handling for timezone conversion issues
5. **Performance**: Optimized conversion functions with minimal overhead
6. **Testability**: Isolated, testable utility functions
7. **User Experience**: Timestamps displayed in user's local timezone
8. **Trading Accuracy**: Trading operations use correct market timezone

### Testing Strategy

#### Timezone Test Cases
```python
# tests/unit/test_timezone.py
def test_timezone_conversions():
    """Test timezone conversion functions"""
    utc_time = datetime(2024, 1, 15, 14, 30, 0, tzinfo=UTC)
    
    # Test conversion to Central
    central_time = to_central(utc_time)
    assert central_time.hour == 8  # 14:30 UTC = 08:30 CST
    
    # Test conversion to Eastern
    eastern_time = to_eastern(utc_time)
    assert eastern_time.hour == 9  # 14:30 UTC = 09:30 EST

def test_market_hours():
    """Test market hours detection"""
    # Market open time (9:30 AM EST)
    market_open = datetime(2024, 1, 15, 9, 30, 0, tzinfo=EASTERN)
    assert is_market_hours(market_open)
    
    # Market close time (4:00 PM EST)
    market_close = datetime(2024, 1, 15, 16, 0, 0, tzinfo=EASTERN)
    assert is_market_hours(market_close)
    
    # After hours
    after_hours = datetime(2024, 1, 15, 18, 0, 0, tzinfo=EASTERN)
    assert not is_market_hours(after_hours)

def test_vendor_data_normalization():
    """Test vendor data timestamp normalization"""
    # UTC timestamp from vendor
    vendor_timestamp = "2024-01-15T14:30:00Z"
    normalized = normalize_vendor_timestamp(vendor_timestamp)
    
    assert normalized.tzinfo == UTC
    assert normalized.hour == 14
    assert normalized.minute == 30
```

This comprehensive timezone strategy ensures that your trading system handles timezones correctly across all components while maintaining data integrity and providing a consistent user experience.

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

---

**Note**: This document consolidates information from multiple architecture documents and will be updated as we make more architectural decisions and implement the system.
