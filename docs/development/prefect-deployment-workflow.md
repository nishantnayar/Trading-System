# Prefect Deployment Workflow

> **📋 Implementation Status**: 🚧 In Progress  
> **Prefect Version**: 3.4.14

This document covers deployment scripts, workflow steps, monitoring, and testing for Prefect 3.4.14.

## Deployment Scripts (Phase 7)

**Note:** These scripts are created after flows are implemented and tested.

### Main Deployment Script

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
        logger.info("✅ All flows deployed successfully")
        return 0
    except Exception as e:
        logger.error(f"❌ Deployment failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
```

### Server Startup Script

**Create: `scripts/prefect/start_server.py`** (After flows are ready)

```python
#!/usr/bin/env python3
"""
Start Prefect server

Usage:
    python scripts/prefect/start_server.py
"""
import sys
import subprocess
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger
from src.config.settings import settings


def main():
    """Start Prefect server"""
    
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

### Worker Startup Script

**Create: `scripts/prefect/start_worker.py`** (After flows are ready)

```python
#!/usr/bin/env python3
"""
Start Prefect worker for a specific work pool

Usage:
    python scripts/prefect/start_worker.py --pool data-ingestion-pool
"""
import sys
import subprocess
import argparse
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from loguru import logger


def main():
    """Start Prefect worker"""
    parser = argparse.ArgumentParser(description="Start Prefect worker")
    parser.add_argument(
        "--pool",
        required=True,
        help="Work pool name (e.g., data-ingestion-pool)"
    )
    
    args = parser.parse_args()
    
    logger.info(f"🚀 Starting Prefect worker for pool: {args.pool}")
    
    try:
        subprocess.run(
            ["prefect", "worker", "start", "--pool", args.pool],
            check=True
        )
    except KeyboardInterrupt:
        logger.info("Worker stopped by user")
    except Exception as e:
        logger.error(f"Failed to start worker: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
```

## Deployment Workflow

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

## Monitoring & Operations

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

## Testing Approach

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

## Related Documentation

- [Prefect Deployment Overview](prefect-deployment-overview.md) - Overview and project structure
- [Prefect Configuration](prefect-deployment-configuration.md) - YAML configs, environment variables, settings
- [Code Patterns](prefect-deployment-code-patterns.md) - Task patterns, flow patterns, deployment definitions
- [Advanced Topics](prefect-deployment-advanced.md) - Design decisions, days_back parameter, migration strategy

---

**Last Updated**: December 2025  
**Status**: 🚧 In Progress

