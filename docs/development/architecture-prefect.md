# Trading System Prefect Architecture

> **Status**: ✅ Phase 1 Complete (v1.0.0) | 🚧 Additional Phases In Progress (v1.1.0)

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
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                Prefect Server                          â”‚
â”‚                (Port 4200)                             â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚  Flow Management  â”‚  Task Execution  â”‚  Monitoring     â”‚
â”‚  â”œâ”€â”€ Deployments  â”‚  â”œâ”€â”€ Work Pools  â”‚  â”œâ”€â”€ UI         â”‚
â”‚  â”œâ”€â”€ Flow Runs    â”‚  â”œâ”€â”€ Workers     â”‚  â”œâ”€â”€ Logs       â”‚
â”‚  â””â”€â”€ Schedules    â”‚  â””â”€â”€ Tasks       â”‚  â””â”€â”€ Metrics    â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
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
â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
â”‚                Prefect Server                          â”‚
â”‚                (Port 4200)                             â”‚
â”œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”¤
â”‚  API Server    â”‚  UI Server    â”‚  Database             â”‚
â”‚  â”œâ”€â”€ REST API  â”‚  â”œâ”€â”€ Web UI   â”‚  â”œâ”€â”€ Flow Runs        â”‚
â”‚  â”œâ”€â”€ GraphQL   â”‚  â”œâ”€â”€ Dashboardâ”‚  â”œâ”€â”€ Task Runs        â”‚
â”‚  â””â”€â”€ WebSocket â”‚  â””â”€â”€ Explorer â”‚  â”œâ”€â”€ Deployments      â”‚
â”‚                                     â”œâ”€â”€ Work Pools      â”‚
â”‚                                     â””â”€â”€ Blocks          â”‚
â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
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

#### **Trading System Database Backup**

The trading database (`data_ingestion`, `analytics` schemas) is backed up weekly via Prefect at 4 AM UTC Sunday, after weekend data ingestion jobs. Backups are written to `backups/trading_backup_YYYYMMDD.dump`.

- **Automated**: Prefect flow `Weekly Database Backup` (scheduled)
- **Manual**: `python scripts/backup_trading_db.py`
- **Restore**: `pg_restore -h localhost -U postgres -d trading_system --clean --if-exists backups/trading_backup_YYYYMMDD.dump`
- **Config**: Uses `.env` for DB connection; set `PGDMP_PATH` if pg_dump is not in PATH (Windows default: `C:\Program Files\PostgreSQL\17\bin\pg_dump.exe`)

#### **Prefect Database Backup**
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

### Prefect Implementation Plan

#### Overview

This section outlines the implementation plan for integrating Prefect workflow orchestration into the Trading System. The goal is to replace manual script execution with automated, scheduled, and monitored workflows that provide better observability, error handling, and reliability.

**Current State:**
- Prefect dependencies already in `requirements.txt` (prefect>=2.14.0)
- Manual scripts exist: `load_historical_data.py`, `load_yahoo_data.py`, `populate_technical_indicators.py`
- Architecture documentation includes Prefect flows (not yet implemented)
- Database tracking via `load_runs` table for incremental loading
- Separate database strategy: `trading_system` and `prefect` databases

**Target State:**
- Automated scheduled workflows for data ingestion
- Centralized workflow monitoring via Prefect UI
- Retry logic and error handling built into flows
- Task dependencies and orchestration
- Work pools for resource management
- Integration with existing logging and database infrastructure

#### Directory Structure

```
src/
â”œâ”€â”€ shared/
â”‚   â””â”€â”€ prefect/
â”‚       â”œâ”€â”€ __init__.py
â”‚       â”œâ”€â”€ config.py              # Prefect configuration
â”‚       â”œâ”€â”€ flows/
â”‚       â”‚   â”œâ”€â”€ __init__.py
â”‚       â”‚   â”œâ”€â”€ data_ingestion/
â”‚       â”‚   â”‚   â”œâ”€â”€ __init__.py
â”‚       â”‚   â”‚   â”œâ”€â”€ polygon_flows.py      # Polygon.io data flows
â”‚       â”‚   â”‚   â”œâ”€â”€ yahoo_flows.py        # Yahoo Finance flows
â”‚       â”‚   â”‚   â””â”€â”€ validation_flows.py   # Data quality checks
â”‚       â”‚   â”œâ”€â”€ analytics/
â”‚       â”‚   â”‚   â”œâ”€â”€ __init__.py
â”‚       â”‚   â”‚   â””â”€â”€ indicator_flows.py    # Technical indicators
â”‚       â”‚   â””â”€â”€ maintenance/
â”‚       â”‚       â”œâ”€â”€ __init__.py
â”‚       â”‚       â””â”€â”€ cleanup_flows.py      # Data archival, cleanup
â”‚       â”œâ”€â”€ deployments/
â”‚       â”‚   â”œâ”€â”€ __init__.py
â”‚       â”‚   â””â”€â”€ deployments.py            # Deployment definitions
â”‚       â”œâ”€â”€ tasks/
â”‚       â”‚   â”œâ”€â”€ __init__.py
â”‚       â”‚   â”œâ”€â”€ data_ingestion.py         # Reusable data ingestion tasks
â”‚       â”‚   â””â”€â”€ validation.py             # Data validation tasks
â”‚       â””â”€â”€ utils/
â”‚           â”œâ”€â”€ __init__.py
â”‚           â””â”€â”€ helpers.py                # Prefect utilities
â””â”€â”€ ...

scripts/
â”œâ”€â”€ prefect/
â”‚   â”œâ”€â”€ start_prefect_server.py          # Server startup script
â”‚   â”œâ”€â”€ start_prefect_worker.py          # Worker startup script
â”‚   â””â”€â”€ deploy_flows.py                  # Deployment script
â””â”€â”€ ...
```

#### Implementation Phases

##### Phase 1: Foundation Setup (Week 1) âœ… COMPLETE

**Status:** Completed December 2025

**Objectives:**
- âœ… Set up Prefect configuration
- âœ… Create directory structure
- âœ… Configure Prefect database connection
- â¸ï¸ Create base utilities and helpers (deferred to Phase 2+)

**Tasks Completed:**
1. âœ… Create Prefect Configuration
   - âœ… `src/shared/prefect/config.py` - Prefect settings from environment
   - âœ… Update `src/config/settings.py` with Prefect settings (3 essential fields)
   - âœ… Update `deployment/env.example` with Prefect variables

2. âœ… Database Setup
   - âœ… Verified `prefect` database exists (via existing database.py support)
   - âœ… Documented connection string format
   - â¸ï¸ Database initialization script (not needed - database.py handles it)

3. â¸ï¸ Base Infrastructure (deferred)
   - â¸ï¸ `src/shared/prefect/utils/helpers.py` - Common utilities (will add when needed)
   - âœ… Logging integration with existing Loguru setup (via Prefect's built-in support)
   - â¸ï¸ Error handling patterns (will add in Phase 2 with flows)

**Test Results:** All 6 integration tests passing

##### Phase 2: Data Ingestion Flows - Polygon.io (Week 1-2)

**Objectives:**
- Convert `load_historical_data.py` to Prefect flows
- Implement scheduled data ingestion
- Add retry logic and error handling
- Integrate with existing `load_runs` tracking

**Tasks:**
1. Create Polygon Flows
   - `src/shared/prefect/flows/data_ingestion/polygon_flows.py`
   - Daily end-of-day data ingestion flow
   - Historical backfill flow
   - Incremental update flow

2. Create Reusable Tasks
   - `src/shared/prefect/tasks/data_ingestion.py`
   - Task for loading single symbol
   - Task for loading all symbols
   - Task for updating load_runs tracking

3. Flow Features
   - Retry on API failures (3 retries, 60s delay)
   - Incremental loading using `load_runs` table
   - Parallel processing for multiple symbols
   - Health checks before execution

**Schedules:**
- **Daily EOD Update**: `0 20 * * 1-5` (8 PM CT, weekdays) - After market close
- **Hourly Update** (optional): `0 * * * 1-5` (Every hour during market hours)

##### Phase 3: Data Ingestion Flows - Yahoo Finance (Week 2-3)

**Objectives:**
- Convert `load_yahoo_data.py` to Prefect flows
- Support multiple data types (market data, company info, key statistics, etc.)
- Implement efficient batch processing

**Tasks:**
1. Create Yahoo Flows
   - `src/shared/prefect/flows/data_ingestion/yahoo_flows.py`
   - Market data ingestion flow
   - Company information update flow
   - Key statistics update flow
   - Financial statements update flow
   - Institutional holders update flow
   - Company officers update flow

2. Flow Features
   - Rate limiting (delay between requests)
   - Batch processing for multiple symbols
   - Conditional loading based on update frequency
   - Error handling with detailed logging

**Schedules:**
- **Market Data (Daily End-of-Day)**: `15 22 * * 1-5` (22:15 UTC Mon-Fri, after US market close) - Fetches hourly bars
- **Company Info (Weekly)**: `0 2 * * 0` (2 AM UTC Sunday) - Weekly updates
- **Key Statistics (Weekly)**: `0 3 * * 0` (3 AM UTC Sunday)
- **Company Data Combined (Weekly)**: `0 2 * * 0` (2 AM UTC Sunday) - Runs company info first, then key statistics
- **Financial Statements (Quarterly)**: `0 9 1 * *` (9 AM CT, 1st of month) - After earnings
- **Institutional Holders (Monthly)**: `0 9 1 * *` (9 AM CT, 1st of month)

##### Phase 4: Analytics Flows - Technical Indicators (Week 3)

**Objectives:**
- Convert `populate_technical_indicators.py` to Prefect flows
- Scheduled indicator calculations
- Integration with data ingestion flows

**Tasks:**
1. Create Indicator Flows
   - `src/shared/prefect/flows/analytics/indicator_flows.py`
   - Daily indicator calculation flow
   - Historical backfill flow
   - Missing data backfill flow

2. Flow Features
   - Calculate indicators after market data ingestion
   - Batch processing for multiple symbols
   - Incremental calculation (only missing dates)

**Schedules:**
- **Daily Calculation**: `0 21 * * 1-5` (9 PM CT, weekdays) - After data ingestion
- **Historical Backfill**: On-demand or scheduled monthly

##### Phase 5: Data Validation & Quality Flows (Week 3-4)

**Objectives:**
- Implement data quality validation
- Automated data quality monitoring
- Alerting on data quality issues

**Tasks:**
1. Create Validation Flows
   - `src/shared/prefect/flows/data_ingestion/validation_flows.py`
   - Data completeness checks
   - Price range validation
   - Volume consistency checks
   - Missing data detection

2. Create Validation Tasks
   - `src/shared/prefect/tasks/validation.py`
   - Reusable validation tasks

**Schedules:**
- **Daily Validation**: `0 22 * * 1-5` (10 PM CT, weekdays) - After data ingestion

##### Phase 6: Maintenance Flows (Week 4)

**Objectives:**
- Data archival and cleanup
- Log rotation
- Database maintenance

**Tasks:**
1. Create Maintenance Flows
   - `src/shared/prefect/flows/maintenance/cleanup_flows.py`
   - Old data archival
   - Log cleanup
   - Database optimization

**Schedules:**
- **Data Archival**: `0 2 * * 0` (2 AM CT, Sunday) - Weekly
- **Log Cleanup**: `0 1 * * *` (1 AM CT, daily)

##### Phase 7: Deployment & Monitoring (Week 4-5)

**Objectives:**
- Create deployment scripts
- Set up Prefect server
- Configure work pools
- Monitoring and observability

**Tasks:**
1. Deployment Configuration
   - `src/shared/prefect/deployments/deployments.py`
   - Deployment definitions for all flows
   - Work pool configuration
   - Schedule definitions

2. Server Setup
   - `scripts/prefect/start_prefect_server.py`
   - `scripts/prefect/start_prefect_worker.py`
   - `scripts/prefect/deploy_flows.py`

3. Monitoring
   - Prefect UI configuration
   - Logging integration
   - Metrics collection

#### Configuration Details

##### Environment Variables

Add to `deployment/env.example`:

```bash
# Prefect Configuration
PREFECT_API_URL=http://localhost:4200/api
PREFECT_API_DATABASE_CONNECTION_URL=postgresql+asyncpg://postgres:password@localhost:5432/prefect
PREFECT_LOGGING_LEVEL=INFO
PREFECT_LOGGING_TO_API_ENABLED=true
PREFECT_SERVER_API_HOST=0.0.0.0
PREFECT_UI_URL=http://localhost:4200

# Prefect Work Pools
PREFECT_WORK_POOL_DATA_INGESTION=default-agent-pool
PREFECT_WORK_POOL_ANALYTICS=default-agent-pool
PREFECT_WORK_POOL_MAINTENANCE=default-agent-pool

# Prefect Flow Configuration
PREFECT_FLOW_RETRY_ATTEMPTS=3
PREFECT_FLOW_RETRY_DELAY_SECONDS=60
PREFECT_FLOW_TIMEOUT_SECONDS=3600
```

##### Settings Configuration

Update `src/config/settings.py` to include:

```python
# Prefect Configuration
prefect_api_url: str = Field(
    default="http://localhost:4200/api",
    alias="PREFECT_API_URL"
)
prefect_db_url: str = Field(
    default="postgresql+asyncpg://postgres:password@localhost:5432/prefect",
    alias="PREFECT_API_DATABASE_CONNECTION_URL"
)
prefect_logging_level: str = Field(
    default="INFO",
    alias="PREFECT_LOGGING_LEVEL"
)
```

#### Flow Design Patterns

##### Data Ingestion Flow Pattern

```python
from prefect import flow, task
from prefect.tasks import task_input_hash
from datetime import timedelta

@task(
    retries=3,
    retry_delay_seconds=60,
    cache_key_fn=task_input_hash,
    cache_expiration=timedelta(hours=1)
)
async def load_symbol_data_task(symbol: str, days_back: int):
    """Load data for a single symbol"""
    # Implementation using existing HistoricalDataLoader
    pass

@flow(
    name="polygon-daily-ingestion",
    retries=2,
    timeout_seconds=3600
)
async def polygon_daily_ingestion():
    """Daily end-of-day data ingestion from Polygon.io"""
    # Get active symbols
    # Load data for each symbol
    # Update load_runs tracking
    # Validate data quality
    pass
```

##### Task Dependencies

```python
@flow(name="data-ingestion-pipeline")
async def data_ingestion_pipeline():
    """Complete data ingestion pipeline"""
    # Step 1: Load Polygon data
    polygon_result = await polygon_daily_ingestion()
    
    # Step 2: Load Yahoo data (after Polygon completes)
    yahoo_result = await yahoo_daily_ingestion()
    
    # Step 3: Calculate indicators (after data loads complete)
    indicator_result = await calculate_daily_indicators()
    
    # Step 4: Validate data quality
    validation_result = await validate_data_quality()
    
    return {
        "polygon": polygon_result,
        "yahoo": yahoo_result,
        "indicators": indicator_result,
        "validation": validation_result
    }
```

#### Migration Strategy

##### Script to Flow Migration Steps

1. **Extract Core Logic**
   - Identify reusable functions in scripts
   - Extract to task functions
   - Maintain existing business logic

2. **Create Flow Wrapper**
   - Wrap script logic in Prefect flow
   - Add retry logic and error handling
   - Add logging and monitoring

3. **Add Scheduling**
   - Define appropriate schedules
   - Configure work pools
   - Set up dependencies

4. **Deploy**
   - Deploy flows to Prefect server
   - Test in staging environment
   - Monitor initial runs

5. **Deprecate Scripts**
   - Keep scripts for manual runs (on-demand)
   - Update documentation
   - Add deprecation notices

##### Backward Compatibility

- Keep scripts functional for on-demand manual runs
- Scripts can be used for ad-hoc operations
- Flows become the primary execution method
- Migration guide for users

#### Testing Strategy

##### Unit Tests

- Test individual tasks in isolation
- Mock external dependencies (API calls, database)
- Test error handling and retry logic
- Test data transformation logic

##### Integration Tests

- Test complete flows end-to-end
- Use test database and API mocks
- Test scheduling and triggers
- Test work pool execution

#### Deployment Guide

##### Prefect Server Setup

1. **Database Setup**
   ```bash
   # Create Prefect database
   createdb -U postgres prefect
   
   # Set connection string
   prefect config set PREFECT_API_DATABASE_CONNECTION_URL="postgresql+asyncpg://postgres:password@localhost:5432/prefect"
   
   # Initialize database
   prefect database upgrade
   ```

2. **Start Prefect Server**
   ```bash
   # Using script
   python scripts/prefect/start_prefect_server.py
   
   # Or manually
   prefect server start --host 0.0.0.0 --port 4200
   ```

3. **Access Prefect UI**
   - Open browser to `http://localhost:4200`

##### Worker Setup

1. **Start Worker**
   ```bash
   # Using script
   python scripts/prefect/start_prefect_worker.py --pool default-agent-pool
   
   # Or manually
   prefect worker start --pool default-agent-pool --limit 10
   ```

2. **Verify Worker**
   - Check Prefect UI for worker status
   - Verify work pool has available workers

##### Flow Deployment

1. **Deploy Flows**
   ```bash
   # Using script
   python scripts/prefect/deploy_flows.py
   
   # Or manually for individual flows
   prefect deployment build src/shared/prefect/flows/data_ingestion/polygon_flows.py:polygon_daily_ingestion
   prefect deployment apply polygon_daily_ingestion-deployment.yaml
   ```

2. **Verify Deployments**
   - Check Prefect UI for deployments
   - Verify schedules are active
   - Monitor initial flow runs

#### Success Criteria

##### Phase 1 Success

- âœ… Prefect server running and accessible
- âœ… Database connection established
- âœ… Configuration working correctly
- âœ… Basic utilities functional

##### Phase 2-4 Success

- âœ… All data ingestion flows deployed
- âœ… Flows executing on schedule
- âœ… Data quality maintained
- âœ… No regression in data completeness

##### Phase 5-7 Success

- âœ… All flows deployed and operational
- âœ… Monitoring and alerting working
- âœ… Documentation complete
- âœ… Team trained on Prefect usage

##### Overall Success Metrics

- **Reliability**: >95% flow run success rate
- **Performance**: Flows complete within expected timeframes
- **Observability**: All flows visible in Prefect UI
- **Maintainability**: Clear documentation and code organization

#### Timeline Summary

| Phase | Duration | Key Deliverables |
|-------|----------|------------------|
| Phase 1: Foundation | Week 1 | Configuration, structure, utilities |
| Phase 2: Polygon Flows | Week 1-2 | Polygon.io data ingestion flows |
| Phase 3: Yahoo Flows | Week 2-3 | Yahoo Finance data ingestion flows |
| Phase 4: Analytics Flows | Week 3 | Technical indicators flows |
| Phase 5: Validation Flows | Week 3-4 | Data quality validation flows |
| Phase 6: Maintenance Flows | Week 4 | Cleanup and archival flows |
| Phase 7: Deployment | Week 4-5 | Deployment scripts, monitoring |

**Total Estimated Time: 4-5 weeks**

## Communication Patterns

### Service Communication
- **Synchronous**: REST APIs for real-time requests
- **Asynchronous**: Redis pub/sub for events
- **Batch Processing**: Prefect flows for scheduled tasks
- **Data Synchronization**: Event-driven updates between services

### Message Flow
```
Data Ingestion â†’ Strategy Engine â†’ Risk Management â†’ Execution
     â†“                â†“                â†“              â†“
Analytics Service â† Notification Service â† Redis â† PostgreSQL
```

### Prefect Flow Orchestration
```
Market Data Flow â†’ Strategy Flow â†’ Risk Flow â†’ Execution Flow
       â†“               â†“            â†“           â†“
   Analytics Flow â† Notification Flow â† Monitoring Flow
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

---

**See Also**:
- [Architecture Overview](architecture-overview.md) - System overview and communication patterns
- [Services Architecture](architecture-services.md) - Service-specific flow details
- [Database Architecture](architecture-database.md) - Prefect database configuration
- [Deployment Architecture](architecture-deployment.md) - Prefect deployment strategy
- [Prefect Deployment Operations](prefect-deployment-operations.md) - Deployment runbook
