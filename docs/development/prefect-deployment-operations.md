# Prefect Deployment Operations

> **📋 Implementation Status**: 🚧 In Progress  
> **Prefect Version**: 3.4.14

This document is the runbook for running and operating Prefect: server, worker, deploy, verify, monitor, troubleshoot, migration, and best practices.

## Prerequisites

1. **Prefect server** running
2. **Work pool** created (default: `data-ingestion-pool`)
3. **Worker** running for that pool
4. **Environment variables** set (see [Configuration](prefect-deployment-configuration.md))

## Step-by-Step Deployment

### Step 1: Start Prefect Server

```bash
prefect server start --host 0.0.0.0 --port 4200
```

- **UI**: http://localhost:4200  
- **API**: http://localhost:4200/api  

Keep this terminal open.

**Alternative (when script exists):** `python scripts/prefect/start_server.py`

### Step 2: Create Work Pool (one-time)

```bash
prefect work-pool ls
prefect work-pool create data-ingestion-pool --type process
```

Or from YAML: `prefect work-pool create --file deployment/prefect/work-pools/data-ingestion-pool.yaml`

### Step 3: Start Worker

```bash
prefect worker start --pool data-ingestion-pool
```

Keep this terminal open.

**Alternative:** `python scripts/prefect/start_worker.py --pool data-ingestion-pool`

### Step 4: Verify Configuration

```bash
# PowerShell
echo $env:PREFECT_API_URL
$env:PREFECT_API_URL = "http://localhost:4200/api"
```

Or in `.env`:

```bash
PREFECT_API_URL=http://localhost:4200/api
PREFECT_WORK_POOL_DATA_INGESTION=data-ingestion-pool
```

### Step 5: Deploy Flows

```bash
# Yahoo flows (current)
python src/shared/prefect/flows/data_ingestion/yahoo_flows.py
# or
python -m src.shared.prefect.flows.data_ingestion.yahoo_flows
```

When available: `python scripts/prefect/deploy_all.py`

### Step 6: Verify Deployments

```bash
prefect deployment ls
prefect deployment inspect "Daily Market Data Update/Daily Market Data Update"
```

Also check the Prefect UI at http://localhost:4200.

### Step 7: Test a Flow (optional)

```bash
prefect deployment run "Daily Market Data Update/Daily Market Data Update"
prefect deployment run "Daily Market Data Update/Daily Market Data Update" --param days_back=7 --param interval=1h
```

## What Gets Deployed (Yahoo)

- **Daily Market Data Update** — 22:15 UTC Mon–Fri; fetches 7 days of **unadjusted and adjusted** hourly data from Yahoo (`data_source='yahoo'` and `data_source='yahoo_adjusted'`), then triggers indicator calculation (`days_back=300` from DB). Task returns `records_count` and `records_count_adjusted`.
- **Daily Technical Indicators** — 22:30 UTC (standalone).
- **Weekly Company Information** — 2 AM UTC Sunday.
- **Weekly Key Statistics** — 3 AM UTC Sunday.
- **Weekly Company Data Update** — Combined, 2 AM UTC Sunday.

## Deployment Scripts (Phase 7)

These are created after flows are implemented and tested.

### deploy_all.py

```python
#!/usr/bin/env python3
"""Deploy all Prefect flows. Usage: python scripts/prefect/deploy_all.py"""
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))
from loguru import logger
from src.shared.prefect.deployments.deployments import create_deployments

def main():
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

### start_server.py

Sets `PREFECT_API_DATABASE_CONNECTION_URL` from settings, then runs:

`prefect server start --host 0.0.0.0 --port 4200`

### start_worker.py

Accepts `--pool` and runs: `prefect worker start --pool <pool>`

## Monitoring & Commands

- **UI**: http://localhost:4200 → Deployments / Flow Runs
- **CLI**:

```bash
prefect deployment ls
prefect flow-run ls
prefect flow-run inspect <flow-run-id>
prefect flow-run logs <flow-run-id>
prefect deployment pause "Daily Market Data Update/Daily Market Data Update"
prefect deployment resume "Daily Market Data Update/Daily Market Data Update"
```

## Troubleshooting

| Issue | Action |
|-------|--------|
| Work pool not found | `prefect work-pool create data-ingestion-pool --type process` |
| Cannot connect to Prefect API | Ensure server is running; set `PREFECT_API_URL=http://localhost:4200/api` |
| No worker available | `prefect worker start --pool data-ingestion-pool` |
| Deployments exist but flows don’t run | Check deployment not paused, schedule correct, worker running; check UI for errors |

## Updating Deployments

After changing flow code, redeploy:

```bash
python src/shared/prefect/flows/data_ingestion/yahoo_flows.py
# or
python scripts/prefect/deploy_all.py
```

## Understanding days_back

`days_back` has different meanings by context.

### Data ingestion (e.g. yahoo_market_data_flow)

- **Meaning**: How many days of **new** data to fetch from the API.
- **Typical**: `7` (hourly) or `30` (daily).
- **Example**: `yahoo_market_data_flow(days_back=7, interval="1h")` fetches 7 days from Yahoo.

### Indicator calculation (e.g. calculate_daily_indicators)

- **Meaning**: How many days of **historical** data to read from the **database**.
- **Typical**: `300` (needed for SMA_200, RSI_14, MACD, etc.).
- **Example**: `calculate_daily_indicators(days_back=300)` reads 300 days from DB.
- **Note**: Reads from DB, not API, so 300 days is acceptable.

**Summary**: Ingest might use `days_back=7` from the API; indicator calculation still uses `days_back=300` from the DB so all indicators have enough history.

## Architecture (high level)

```
Prefect Server → Deployments (schedules) → Work Pool → Worker (executes flows)
```

Flow run: schedule → queue → worker runs flow (e.g. load data → calculate indicators) → results in Prefect DB and UI.

## Migration Strategy

1. **Parallel run**: Keep existing scripts; run Prefect alongside; compare results (1–2 weeks).
2. **Validation**: Run both; verify consistency; document discrepancies (1–2 weeks).
3. **Cutover**: Make Prefect primary; keep scripts as fallback; document deprecation.
4. **Cleanup**: Optionally remove old scripts; update docs; train on Prefect UI.

## Best Practices

- **Incremental**: One flow at a time; test before adding more.
- **Errors**: Use retries, structured logging, timeouts, and graceful partial failure handling.
- **Monitoring**: Use Prefect UI and alerts for critical flows; track success rates and resources.
- **Testing**: Unit tests for tasks; integration tests for flows; test with limited data first.
- **Docs**: Document flow purpose, keep config examples current, maintain troubleshooting notes.

## Testing

- **Unit**: e.g. `tests/unit/test_prefect_tasks.py` for task behavior (mocked deps).
- **Integration**: e.g. `tests/integration/test_prefect_flows.py` for flows against test DB with limited symbols.

## Related Documentation

- [Prefect Deployment](prefect-deployment.md) — Overview and index
- [Configuration](prefect-deployment-configuration.md) — YAML, env, settings
- [Code Patterns](prefect-deployment-code-patterns.md) — Tasks, flows, deployments
- [Advanced Topics](prefect-deployment-advanced.md) — Design decisions

---

**Last Updated**: December 2025  
**Status**: 🚧 In Progress
