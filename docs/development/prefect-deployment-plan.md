# Prefect 3.4.14 Deployment Plan

## Overview

This document outlines the proper deployment approach for Prefect 3.4.14 in the Trading System, including code structure, YAML configurations, and deployment patterns.

---

## 1. Project Structure (Incremental Build)

**Note:** This shows the final structure. Files and folders will be created incrementally as we implement each phase, not all at once.

**Phase-by-Phase Creation:**
- **Phase 1 (Foundation)**: Only `config.py` and basic structure
- **Phase 2 (Polygon Flows)**: Add `polygon_flows.py` and related tasks
- **Phase 3 (Yahoo Flows)**: Add `yahoo_flows.py`
- **Phase 4+**: Continue adding files as needed

```
src/
├── shared/
│   └── prefect/
│       ├── __init__.py                  # Phase 1
│       ├── config.py                    # Phase 1: Prefect configuration
│       ├── flows/
│       │   ├── __init__.py              # Phase 1
│       │   ├── data_ingestion/
│       │   │   ├── __init__.py          # Phase 2
│       │   │   ├── polygon_flows.py     # Phase 2: Polygon.io flows
│       │   │   ├── yahoo_flows.py       # Phase 3: Yahoo Finance flows
│       │   │   └── validation_flows.py  # Phase 5: Data validation
│       │   ├── analytics/
│       │   │   ├── __init__.py          # Phase 4
│       │   │   └── indicator_flows.py   # Phase 4: Technical indicators
│       │   └── maintenance/
│       │       ├── __init__.py          # Phase 6
│       │       └── cleanup_flows.py     # Phase 6: Data cleanup
│       ├── tasks/
│       │   ├── __init__.py              # Phase 2
│       │   ├── data_ingestion_tasks.py  # Phase 2: Reusable tasks
│       │   └── validation_tasks.py      # Phase 5: Validation tasks
│       └── deployments/
│           ├── __init__.py              # Phase 7
│           └── deployments.py           # Phase 7: Deployment definitions
│
deployment/
└── prefect/                             # Phase 7: YAML configs (optional)
    ├── prefect.yaml
    ├── deployments/
    └── work-pools/

scripts/
└── prefect/                             # Phase 7: Deployment scripts
    ├── deploy_all.py
    ├── start_server.py
    └── start_worker.py
```

---

## 2. Prefect Configuration (`prefect.yaml`)

### Sample: `deployment/prefect/prefect.yaml`

```yaml
# Prefect 3.4.14 Configuration
name: trading-system-prefect

prefect:
  version: 3.4.14
  
  # Work Pools Configuration
  work_pools:
    - name: data-ingestion-pool
      type: process
      base_job_template:
        job_configuration:
          command: >
            python -m prefect.engine
          env:
            PREFECT_API_URL: "${PREFECT_API_URL}"
            POSTGRES_HOST: "${POSTGRES_HOST}"
            POSTGRES_PORT: "${POSTGRES_PORT}"
            POSTGRES_USER: "${POSTGRES_USER}"
            POSTGRES_PASSWORD: "${POSTGRES_PASSWORD}"
            TRADING_DB_NAME: "${TRADING_DB_NAME}"
          
    - name: analytics-pool
      type: process
      base_job_template:
        job_configuration:
          command: >
            python -m prefect.engine
          env:
            PREFECT_API_URL: "${PREFECT_API_URL}"
            # ... other env vars

  # Deployments
  deployments:
    - name: polygon-daily-ingestion
      flow_name: polygon-daily-ingestion
      entrypoint: src/shared/prefect/flows/data_ingestion/polygon_flows.py:polygon_daily_ingestion
      work_pool_name: data-ingestion-pool
      schedule:
        cron: "0 20 * * 1-5"  # 8 PM CT weekdays
        timezone: "America/Chicago"
      parameters:
        days_back: 1
        incremental: true
      tags:
        - data-ingestion
        - polygon
        - scheduled
      
    - name: yahoo-market-data-hourly
      flow_name: yahoo-market-data-hourly
      entrypoint: src/shared/prefect/flows/data_ingestion/yahoo_flows.py:yahoo_market_data_flow
      work_pool_name: data-ingestion-pool
      schedule:
        cron: "0 * * * 1-5"  # Every hour weekdays
        timezone: "America/Chicago"
      parameters: {}
      tags:
        - data-ingestion
        - yahoo
        - scheduled
      
    - name: indicators-daily-calculation
      flow_name: indicators-daily-calculation
      entrypoint: src/shared/prefect/flows/analytics/indicator_flows.py:calculate_daily_indicators
      work_pool_name: analytics-pool
      schedule:
        cron: "0 21 * * 1-5"  # 9 PM CT weekdays (after data ingestion)
        timezone: "America/Chicago"
      parameters:
        days_back: 1
      tags:
        - analytics
        - indicators
        - scheduled
```

---

## 3. Code Structure & Patterns

**Implementation Note:** Each section below will be implemented incrementally. Start with Phase 1 (Configuration), then build flows as needed.

### 3.1 Configuration Module (Phase 1)

**Create: `src/shared/prefect/config.py`** (First file to create)

```python
"""
Prefect Configuration for Trading System
"""
import os
from typing import Optional
from prefect.settings import PREFECT_API_URL
from src.config.settings import Settings

settings = Settings()


class PrefectConfig:
    """Prefect configuration management"""
    
    @staticmethod
    def get_api_url() -> str:
        """Get Prefect API URL from environment or settings"""
        return os.environ.get(
            "PREFECT_API_URL",
            settings.prefect_api_url if hasattr(settings, "prefect_api_url") 
            else "http://localhost:4200/api"
        )
    
    @staticmethod
    def get_work_pool_config(pool_name: str) -> dict:
        """Get work pool configuration"""
        # Return work pool specific config
        pass
    
    @staticmethod
    def validate_config() -> bool:
        """Validate Prefect configuration"""
        # Check API URL, database, etc.
        pass
```

---

### 3.2 Task Patterns (Phase 2+)

**Create: `src/shared/prefect/tasks/data_ingestion_tasks.py`** (Created when implementing flows)

```python
"""
Reusable Prefect Tasks for Data Ingestion
"""
from datetime import date
from typing import Optional
from prefect import task
from loguru import logger
from src.services.data_ingestion.historical_loader import HistoricalDataLoader
from src.services.yahoo.loader import YahooDataLoader


@task(
    name="load-polygon-symbol-data",
    retries=3,
    retry_delay_seconds=60,
    log_prints=True,
    tags=["data-ingestion", "polygon"]
)
async def load_polygon_symbol_data_task(
    symbol: str,
    days_back: int = 1,
    incremental: bool = True
) -> int:
    """
    Load historical data for a single symbol from Polygon.io
    
    Args:
        symbol: Stock symbol
        days_back: Number of days to look back
        incremental: Whether to use incremental loading
        
    Returns:
        Number of records loaded
    """
    logger.info(f"Loading Polygon data for {symbol} (days_back={days_back})")
    
    loader = HistoricalDataLoader(
        batch_size=100,
        requests_per_minute=2,
        detect_delisted=True
    )
    
    try:
        records_count = await loader.load_symbol_data(
            symbol=symbol,
            days_back=days_back,
            incremental=incremental
        )
        logger.info(f"✅ Loaded {records_count} records for {symbol}")
        return records_count
    except Exception as e:
        logger.error(f"❌ Failed to load {symbol}: {e}")
        raise


@task(
    name="load-yahoo-market-data",
    retries=2,
    retry_delay_seconds=30,
    log_prints=True,
    tags=["data-ingestion", "yahoo"]
)
async def load_yahoo_market_data_task(
    symbol: str,
    days_back: int = 1,
    interval: str = "1h"
) -> dict:
    """
    Load market data for a single symbol from Yahoo Finance
    
    Args:
        symbol: Stock symbol
        days_back: Number of days to look back
        interval: Data interval (1h, 1d, etc.)
        
    Returns:
        Dictionary with load results
    """
    logger.info(f"Loading Yahoo market data for {symbol}")
    
    loader = YahooDataLoader(batch_size=100, delay_between_requests=0.5)
    
    try:
        # Use existing loader methods
        from_date = date.today() - timedelta(days=days_back)
        to_date = date.today()
        
        # Call loader's load_all_data or appropriate method
        results = await loader.load_all_data(
            symbol=symbol,
            start_date=from_date,
            end_date=to_date,
            include_fundamentals=False,
            include_key_statistics=False
        )
        
        logger.info(f"✅ Loaded Yahoo data for {symbol}: {results}")
        return results
    except Exception as e:
        logger.error(f"❌ Failed to load Yahoo data for {symbol}: {e}")
        raise


@task(
    name="update-load-runs-tracking",
    log_prints=True,
    tags=["data-ingestion", "tracking"]
)
async def update_load_runs_tracking_task(
    symbol: str,
    data_source: str,
    records_count: int,
    status: str = "success"
) -> None:
    """
    Update load_runs table with ingestion results
    
    Args:
        symbol: Stock symbol
        data_source: Data source identifier
        records_count: Number of records loaded
        status: Load status (success, failed, partial)
    """
    # Update load_runs table using existing LoadRun model
    pass
```

---

### 3.3 Flow Patterns (Phase 2+)

**Create: `src/shared/prefect/flows/data_ingestion/polygon_flows.py`** (Created when implementing Polygon flows)

```python
"""
Polygon.io Data Ingestion Flows
"""
from datetime import date, timedelta
from typing import List, Optional
from prefect import flow, task
from prefect.tasks import task_input_hash
from loguru import logger
from src.shared.prefect.tasks.data_ingestion_tasks import (
    load_polygon_symbol_data_task,
    update_load_runs_tracking_task
)
from src.services.data_ingestion.symbols import SymbolService


@flow(
    name="polygon-daily-ingestion",
    log_prints=True,
    retries=1,
    retry_delay_seconds=300,  # 5 minutes
    timeout_seconds=3600,  # 1 hour
    tags=["data-ingestion", "polygon", "scheduled"]
)
async def polygon_daily_ingestion(
    days_back: int = 1,
    symbols: Optional[List[str]] = None,
    incremental: bool = True,
    max_symbols: Optional[int] = None
) -> dict:
    """
    Daily end-of-day data ingestion from Polygon.io
    
    This flow:
    1. Gets active symbols
    2. Loads data for each symbol
    3. Updates load_runs tracking
    4. Returns summary statistics
    
    Args:
        days_back: Number of days to look back (default: 1 for daily updates)
        symbols: Optional list of specific symbols (None = all active)
        incremental: Whether to use incremental loading
        max_symbols: Maximum number of symbols to process (for testing)
        
    Returns:
        Dictionary with ingestion statistics
    """
    logger.info("=" * 60)
    logger.info("Starting Polygon Daily Ingestion Flow")
    logger.info(f"Days back: {days_back}, Incremental: {incremental}")
    logger.info("=" * 60)
    
    # Get symbols to process
    if symbols is None:
        symbol_service = SymbolService()
        symbols_list = await symbol_service.get_active_symbol_strings()
        logger.info(f"Found {len(symbols_list)} active symbols")
    else:
        symbols_list = [s.upper() for s in symbols]
        logger.info(f"Processing {len(symbols_list)} specified symbols")
    
    if max_symbols:
        symbols_list = symbols_list[:max_symbols]
        logger.info(f"Limited to {max_symbols} symbols for testing")
    
    # Statistics
    successful = []
    failed = []
    total_records = 0
    
    # Process each symbol
    for symbol in symbols_list:
        try:
            logger.info(f"Processing {symbol}...")
            
            # Load data for symbol
            records_count = await load_polygon_symbol_data_task(
                symbol=symbol,
                days_back=days_back,
                incremental=incremental
            )
            
            # Update tracking
            await update_load_runs_tracking_task(
                symbol=symbol,
                data_source="polygon",
                records_count=records_count,
                status="success"
            )
            
            successful.append(symbol)
            total_records += records_count
            
        except Exception as e:
            logger.error(f"Failed to process {symbol}: {e}")
            failed.append({"symbol": symbol, "error": str(e)})
            
            # Update tracking with failure
            await update_load_runs_tracking_task(
                symbol=symbol,
                data_source="polygon",
                records_count=0,
                status="failed"
            )
    
    # Summary
    result = {
        "total_symbols": len(symbols_list),
        "successful": len(successful),
        "failed": len(failed),
        "total_records": total_records,
        "successful_symbols": successful,
        "failed_symbols": failed
    }
    
    logger.info("=" * 60)
    logger.info("Polygon Daily Ingestion Completed")
    logger.info(f"Successful: {result['successful']}/{result['total_symbols']}")
    logger.info(f"Failed: {result['failed']}")
    logger.info(f"Total records: {result['total_records']}")
    logger.info("=" * 60)
    
    return result


@flow(
    name="polygon-historical-backfill",
    log_prints=True,
    timeout_seconds=7200,  # 2 hours for backfills
    tags=["data-ingestion", "polygon", "on-demand"]
)
async def polygon_historical_backfill(
    start_date: date,
    end_date: date,
    symbols: Optional[List[str]] = None,
    max_symbols: Optional[int] = None
) -> dict:
    """
    Historical data backfill from Polygon.io
    
    Used for:
    - Initial data population
    - Backfilling missing data
    - Testing
    
    Args:
        start_date: Start date for backfill
        end_date: End date for backfill
        symbols: Optional list of symbols
        max_symbols: Maximum symbols to process
        
    Returns:
        Dictionary with backfill statistics
    """
    # Similar structure to daily ingestion but with date range
    pass
```

---

**Sample: `src/shared/prefect/flows/analytics/indicator_flows.py`**

```python
"""
Technical Indicators Calculation Flows
"""
from datetime import date
from typing import List, Optional
from prefect import flow, task
from loguru import logger
from src.services.analytics import IndicatorService
from src.services.data_ingestion.symbols import SymbolService


@flow(
    name="indicators-daily-calculation",
    log_prints=True,
    retries=1,
    timeout_seconds=3600,
    tags=["analytics", "indicators", "scheduled"]
)
async def calculate_daily_indicators(
    days_back: int = 1,
    symbols: Optional[List[str]] = None,
    calculation_date: Optional[date] = None
) -> dict:
    """
    Calculate technical indicators for all symbols
    
    Runs after data ingestion flows complete.
    
    Args:
        days_back: Days of history to fetch for calculations
        symbols: Optional list of specific symbols
        calculation_date: Date to calculate for (default: today)
        
    Returns:
        Dictionary with calculation statistics
    """
    logger.info("=" * 60)
    logger.info("Starting Daily Indicators Calculation")
    logger.info("=" * 60)
    
    if calculation_date is None:
        calculation_date = date.today()
    
    # Get symbols
    if symbols is None:
        symbol_service = SymbolService()
        symbols_list = await symbol_service.get_active_symbol_strings()
    else:
        symbols_list = [s.upper() for s in symbols]
    
    # Initialize indicator service
    indicator_service = IndicatorService(data_source="yahoo")
    
    successful = []
    failed = []
    
    for symbol in symbols_list:
        try:
            logger.info(f"Calculating indicators for {symbol}...")
            
            # Use existing IndicatorService methods
            await indicator_service.calculate_and_store_indicators(
                symbol=symbol,
                calculation_date=calculation_date,
                days_back=days_back
            )
            
            successful.append(symbol)
            
        except Exception as e:
            logger.error(f"Failed to calculate indicators for {symbol}: {e}")
            failed.append({"symbol": symbol, "error": str(e)})
    
    result = {
        "calculation_date": calculation_date.isoformat(),
        "total_symbols": len(symbols_list),
        "successful": len(successful),
        "failed": len(failed),
        "successful_symbols": successful,
        "failed_symbols": failed
    }
    
    logger.info("=" * 60)
    logger.info(f"Indicators calculation completed: {result['successful']}/{result['total_symbols']} successful")
    logger.info("=" * 60)
    
    return result
```

---

### 3.4 Deployment Definitions (Phase 7)

**Create: `src/shared/prefect/deployments/deployments.py`** (Created after flows are working)

```python
"""
Prefect Deployment Definitions
"""
from prefect import serve
from prefect.server.schemas.schedules import CronSchedule
from src.shared.prefect.flows.data_ingestion.polygon_flows import (
    polygon_daily_ingestion,
    polygon_historical_backfill
)
from src.shared.prefect.flows.data_ingestion.yahoo_flows import (
    yahoo_market_data_flow
)
from src.shared.prefect.flows.analytics.indicator_flows import (
    calculate_daily_indicators
)


def create_deployments():
    """
    Create all Prefect deployments
    
    This function defines deployments using Prefect's serve() API
    """
    
    # Polygon Daily Ingestion
    polygon_daily_ingestion.serve(
        name="polygon-daily-ingestion",
        work_pool_name="data-ingestion-pool",
        schedule=CronSchedule(
            cron="0 20 * * 1-5",  # 8 PM CT weekdays
            timezone="America/Chicago"
        ),
        parameters={
            "days_back": 1,
            "incremental": True
        },
        tags=["data-ingestion", "polygon", "scheduled"],
        description="Daily end-of-day data ingestion from Polygon.io"
    )
    
    # Yahoo Market Data Hourly
    yahoo_market_data_flow.serve(
        name="yahoo-market-data-hourly",
        work_pool_name="data-ingestion-pool",
        schedule=CronSchedule(
            cron="0 * * * 1-5",  # Every hour weekdays
            timezone="America/Chicago"
        ),
        tags=["data-ingestion", "yahoo", "scheduled"],
        description="Hourly market data ingestion from Yahoo Finance"
    )
    
    # Indicators Daily Calculation
    calculate_daily_indicators.serve(
        name="indicators-daily-calculation",
        work_pool_name="analytics-pool",
        schedule=CronSchedule(
            cron="0 21 * * 1-5",  # 9 PM CT weekdays (after data ingestion)
            timezone="America/Chicago"
        ),
        parameters={
            "days_back": 300  # Need more history for indicators
        },
        tags=["analytics", "indicators", "scheduled"],
        description="Daily technical indicators calculation"
    )
    
    # Historical backfill (on-demand, no schedule)
    polygon_historical_backfill.serve(
        name="polygon-historical-backfill",
        work_pool_name="data-ingestion-pool",
        # No schedule - manual trigger only
        tags=["data-ingestion", "polygon", "on-demand"],
        description="Historical data backfill (manual trigger)"
    )


if __name__ == "__main__":
    # Run this script to deploy all flows
    create_deployments()
```

---

## 4. Deployment Scripts (Phase 7)

**Note:** These scripts are created after flows are implemented and tested.

### 4.1 Main Deployment Script

**Create: `scripts/prefect/deploy_all.py`** (After flows are ready)

```python
#!/usr/bin/env python3
"""
Deploy all Prefect flows to the server

Usage:
    python scripts/prefect/deploy_all.py
    python scripts/prefect/deploy_all.py --flow polygon-daily  # Deploy specific flow
"""
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from src.shared.prefect.deployments.deployments import create_deployments


def main():
    """Deploy all Prefect flows"""
    logger.info("🚀 Deploying Prefect flows...")
    
    try:
        create_deployments()
        logger.info("✅ All flows deployed successfully!")
        logger.info("   View deployments: prefect deployment ls")
        logger.info("   View Prefect UI: http://localhost:4200")
    except Exception as e:
        logger.error(f"❌ Deployment failed: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
```

---

### 4.2 Server Startup Script

**Create: `scripts/prefect/start_server.py`** (Optional - can use command line initially)

```python
#!/usr/bin/env python3
"""
Start Prefect server

Usage:
    python scripts/prefect/start_server.py
"""
import subprocess
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from src.config.settings import Settings


def main():
    """Start Prefect server"""
    settings = Settings()
    
    logger.info("🚀 Starting Prefect server...")
    
    # Check if database exists
    # ... database check logic ...
    
    # Set environment variables
    import os
    os.environ["PREFECT_API_DATABASE_CONNECTION_URL"] = (
        f"postgresql+asyncpg://{settings.postgres_user}:{settings.postgres_password}"
        f"@{settings.postgres_host}:{settings.postgres_port}/prefect"
    )
    
    # Start server
    try:
        subprocess.run(
            ["prefect", "server", "start", "--host", "0.0.0.0", "--port", "4200"],
            check=True
        )
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
```

---

## 5. Work Pool Configuration (Phase 7 - Optional)

**Note:** YAML configs are optional. Can use Python `serve()` API instead. Create these only if using YAML-based deployments.

### Sample YAML: `deployment/prefect/work-pools/data-ingestion-pool.yaml`

```yaml
name: data-ingestion-pool
type: process
description: Work pool for data ingestion flows (Polygon, Yahoo)

base_job_template:
  job_configuration:
    command: >
      python -m prefect.engine
    env:
      # Prefect
      PREFECT_API_URL: "http://localhost:4200/api"
      
      # Database
      POSTGRES_HOST: "${POSTGRES_HOST}"
      POSTGRES_PORT: "${POSTGRES_PORT}"
      POSTGRES_USER: "${POSTGRES_USER}"
      POSTGRES_PASSWORD: "${POSTGRES_PASSWORD}"
      TRADING_DB_NAME: "${TRADING_DB_NAME}"
      
      # API Keys (from environment)
      POLYGON_API_KEY: "${POLYGON_API_KEY}"
      
    # Resource limits
    cpu: 2
    memory: "4Gi"
    
  variables:
    batch_size:
      type: int
      default: 100
    requests_per_minute:
      type: int
      default: 2
```

---

## 6. Configuration Changes Required

### 6.1 Environment Variables (`deployment/env.example`)

Add these new sections to `deployment/env.example`:

```bash
# ============================================
# Prefect 3.4.14 Configuration
# ============================================

# Prefect Server Configuration
PREFECT_API_URL=http://localhost:4200/api
PREFECT_API_DATABASE_CONNECTION_URL=postgresql+asyncpg://postgres:password@localhost:5432/prefect
PREFECT_LOGGING_LEVEL=INFO
PREFECT_LOGGING_TO_API_ENABLED=true
PREFECT_SERVER_API_HOST=0.0.0.0
PREFECT_UI_URL=http://localhost:4200

# Prefect Work Pool Names
PREFECT_WORK_POOL_DATA_INGESTION=data-ingestion-pool
PREFECT_WORK_POOL_ANALYTICS=analytics-pool
PREFECT_WORK_POOL_MAINTENANCE=maintenance-pool

# Prefect Flow Configuration
PREFECT_FLOW_RETRY_ATTEMPTS=3
PREFECT_FLOW_RETRY_DELAY_SECONDS=60
PREFECT_FLOW_TIMEOUT_SECONDS=3600

# Prefect Database Name
PREFECT_DB_NAME=prefect
```

### 6.2 Settings Class (`src/config/settings.py`)

Add these fields to the `Settings` class:

```python
class Settings(BaseSettings):
    # ... existing fields ...
    
    # ============================================
    # Prefect Configuration
    # ============================================
    
    # Prefect Server Configuration
    prefect_api_url: str = Field(
        default="http://localhost:4200/api",
        alias="PREFECT_API_URL"
    )
    
    prefect_db_connection_url: str = Field(
        default="postgresql+asyncpg://postgres:password@localhost:5432/prefect",
        alias="PREFECT_API_DATABASE_CONNECTION_URL"
    )
    
    prefect_logging_level: str = Field(
        default="INFO",
        alias="PREFECT_LOGGING_LEVEL"
    )
    
    prefect_logging_to_api_enabled: bool = Field(
        default=True,
        alias="PREFECT_LOGGING_TO_API_ENABLED"
    )
    
    prefect_server_api_host: str = Field(
        default="0.0.0.0",
        alias="PREFECT_SERVER_API_HOST"
    )
    
    prefect_ui_url: str = Field(
        default="http://localhost:4200",
        alias="PREFECT_UI_URL"
    )
    
    # Prefect Work Pool Names
    prefect_work_pool_data_ingestion: str = Field(
        default="data-ingestion-pool",
        alias="PREFECT_WORK_POOL_DATA_INGESTION"
    )
    
    prefect_work_pool_analytics: str = Field(
        default="analytics-pool",
        alias="PREFECT_WORK_POOL_ANALYTICS"
    )
    
    prefect_work_pool_maintenance: str = Field(
        default="maintenance-pool",
        alias="PREFECT_WORK_POOL_MAINTENANCE"
    )
    
    # Prefect Flow Defaults
    prefect_flow_retry_attempts: int = Field(
        default=3,
        alias="PREFECT_FLOW_RETRY_ATTEMPTS"
    )
    
    prefect_flow_retry_delay_seconds: int = Field(
        default=60,
        alias="PREFECT_FLOW_RETRY_DELAY_SECONDS"
    )
    
    prefect_flow_timeout_seconds: int = Field(
        default=3600,
        alias="PREFECT_FLOW_TIMEOUT_SECONDS"
    )
```

### 6.3 Database Configuration (`src/config/database.py`)

✅ **No changes needed** - The database configuration already supports Prefect:
- `prefect_db_name` field exists
- `prefect_db_url` property exists
- Support for `database="prefect"` in `get_engine()`

### 6.4 Configuration Summary

**Files to Modify:**
- `deployment/env.example` - Add 11 new environment variables
- `src/config/settings.py` - Add 11 new Prefect configuration fields

**Files to Create:**
- `src/shared/prefect/config.py` - Prefect configuration module (see section 3.1)

**Configuration Notes:**
- Database connection URL must use `postgresql+asyncpg://` format (Prefect 3.x requires asyncpg)
- API URL must include `/api` suffix: `http://localhost:4200/api`
- All new fields have defaults for backward compatibility

---

## 7. Deployment Workflow

### Step 1: Start Prefect Server

```bash
# Option A: Using script
python scripts/prefect/start_server.py

# Option B: Direct command
prefect server start --host 0.0.0.0 --port 4200
```

### Step 2: Create Work Pools (one-time setup)

```bash
# Create work pools from YAML
prefect work-pool create --file deployment/prefect/work-pools/data-ingestion-pool.yaml
prefect work-pool create --file deployment/prefect/work-pools/analytics-pool.yaml
```

### Step 3: Start Workers

```bash
# Start worker for data ingestion pool
prefect worker start --pool data-ingestion-pool

# Start worker for analytics pool (in another terminal)
prefect worker start --pool analytics-pool
```

### Step 4: Deploy Flows

```bash
# Deploy all flows
python scripts/prefect/deploy_all.py

# Or deploy individually using serve()
python src/shared/prefect/deployments/deployments.py
```

### Step 5: Verify Deployments

```bash
# List deployments
prefect deployment ls

# View specific deployment
prefect deployment inspect polygon-daily-ingestion/polygon-daily-ingestion

# Run deployment manually
prefect deployment run polygon-daily-ingestion/polygon-daily-ingestion
```

---

## 8. Monitoring & Operations

### View Flows in UI

1. Open browser: `http://localhost:4200`
2. Navigate to "Deployments"
3. View flow runs, logs, and metrics

### Common Commands

```bash
# List all deployments
prefect deployment ls

# List all flow runs
prefect flow-run ls

# View specific flow run
prefect flow-run inspect <flow-run-id>

# View logs
prefect flow-run logs <flow-run-id>

# Pause/resume deployment
prefect deployment pause polygon-daily-ingestion/polygon-daily-ingestion
prefect deployment resume polygon-daily-ingestion/polygon-daily-ingestion
```

---

## 9. Testing Approach

### Unit Tests

```python
# tests/unit/test_prefect_tasks.py
import pytest
from src.shared.prefect.tasks.data_ingestion_tasks import load_polygon_symbol_data_task

@pytest.mark.asyncio
async def test_load_polygon_symbol_data_task():
    """Test Polygon data loading task"""
    # Mock dependencies
    # Test task execution
    pass
```

### Integration Tests

```python
# tests/integration/test_prefect_flows.py
import pytest
from src.shared.prefect.flows.data_ingestion.polygon_flows import polygon_daily_ingestion

@pytest.mark.asyncio
async def test_polygon_daily_ingestion_flow():
    """Test Polygon daily ingestion flow end-to-end"""
    # Use test database
    # Run flow with limited symbols
    # Verify results
    pass
```

---

## 10. Key Design Decisions

### Why `serve()` API?

Prefect 3.x introduces the `serve()` API which is simpler than the older deployment building approach. Flows can be deployed by calling `.serve()` on the flow object.

### Why Separate Work Pools?

- **Resource Isolation**: Different pools can have different resource limits
- **Parallelism Control**: Limit concurrent executions per pool
- **Environment Separation**: Different pools can use different environments

### Why YAML + Python?

- **YAML**: For static configuration (work pools, schedules)
- **Python**: For dynamic deployment logic and code reuse

### Task Granularity

- **Coarse-grained tasks**: One task per symbol (better for parallelization)
- **Fine-grained tasks**: Separate tasks for fetch/validate/store (better for observability)

Choose based on your needs. Start coarse-grained, refine as needed.

---

## 11. Migration Strategy

### Phase 1: Parallel Run
- Keep existing scripts working
- Deploy Prefect flows alongside
- Compare results

### Phase 2: Validation
- Run both systems for 1-2 weeks
- Verify data consistency
- Monitor Prefect flows

### Phase 3: Cutover
- Make Prefect flows primary
- Keep scripts as fallback
- Document deprecation

### Phase 4: Cleanup
- Remove old scripts (optional)
- Update documentation
- Train team on Prefect UI

---

## 12. Implementation Approach

### Incremental Development Strategy

**Key Principle:** Build incrementally, not all at once.

1. **Start Small**: Begin with Phase 1 (configuration only)
2. **Build One Flow**: Implement one flow at a time (e.g., Polygon daily ingestion)
3. **Test Thoroughly**: Test each flow before moving to the next
4. **Add Files As Needed**: Only create files when you're ready to implement them

### Recommended Order:

1. ✅ **Phase 1**: Configuration (`config.py` + settings updates) - **COMPLETE**
2. ⏳ **Phase 2**: One simple flow (Polygon daily ingestion) + tasks - **NEXT**
3. ⏳ **Test & Validate**: Run the flow, verify it works
4. ⏳ **Phase 3**: Add another flow (Yahoo market data)
5. ⏳ **Continue incrementally**: Add flows one at a time
6. ⏳ **Phase 7**: Deployment scripts and YAML (after flows work)

### What to Create First:

**Phase 1 - COMPLETE ✅:**
- ✅ `src/shared/prefect/__init__.py`
- ✅ `src/shared/prefect/config.py`
- ✅ Update `src/config/settings.py` (add Prefect fields)
- ✅ Update `deployment/env.example` (add Prefect variables)
- ✅ Integration tests (`tests/integration/test_prefect_config.py`)

**Phase 2 - NEXT ⏳:**
- First flow file (e.g., `polygon_flows.py`)
- Tasks file for that flow
- Test it works
- Then add next flow...

---

This plan provides a complete structure for deploying Prefect 3.4.14 with proper YAML configurations, code patterns, and deployment workflows. **Implement incrementally, creating files only when ready to code them.**

