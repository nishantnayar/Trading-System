# Prefect Flow Deployment Guide

This guide explains how to deploy the Yahoo Finance data ingestion flows (including automatic technical indicators calculation).

## Prerequisites

1. **Prefect Server Running**: The Prefect server must be running
2. **Work Pool Created**: A work pool must exist (default: `data-ingestion-pool`)
3. **Worker Running**: A worker must be running for the work pool
4. **Environment Variables**: Prefect configuration must be set

## Step-by-Step Deployment

### Step 1: Start Prefect Server

In a terminal, start the Prefect server:

```bash
prefect server start --host 0.0.0.0 --port 4200
```

The server will be available at:
- **UI**: http://localhost:4200
- **API**: http://localhost:4200/api

**Note**: Keep this terminal open - the server must remain running.

### Step 2: Create Work Pool (One-time setup)

In a new terminal, create the work pool if it doesn't exist:

```bash
# Check if work pool exists
prefect work-pool ls

# If it doesn't exist, create it
prefect work-pool create data-ingestion-pool --type process
```

The default work pool name is `data-ingestion-pool`. You can change this by setting the `PREFECT_WORK_POOL_DATA_INGESTION` environment variable.

### Step 3: Start Worker

In another terminal, start a worker for the work pool:

```bash
prefect worker start --pool data-ingestion-pool
```

**Note**: Keep this terminal open - the worker must remain running to execute flow runs.

### Step 4: Verify Configuration

Make sure your environment variables are set (or use defaults):

```bash
# Check Prefect API URL
echo $env:PREFECT_API_URL  # Windows PowerShell
# Should be: http://localhost:4200/api

# If not set, set it:
$env:PREFECT_API_URL = "http://localhost:4200/api"  # Windows PowerShell
```

Or set it in your `.env` file:
```bash
PREFECT_API_URL=http://localhost:4200/api
PREFECT_WORK_POOL_DATA_INGESTION=data-ingestion-pool
```

### Step 5: Deploy the Flows

Run the deployment script:

```bash
# From the project root directory
python src/shared/prefect/flows/data_ingestion/yahoo_flows.py
```

Or use Python directly:

```bash
python -m src.shared.prefect.flows.data_ingestion.yahoo_flows
```

This will deploy all Yahoo Finance flows:
- **Daily Market Data Update** - Runs daily at 22:15 UTC (after market close)
  - Automatically triggers technical indicators calculation after data ingestion
- **Daily Technical Indicators Calculation** - Runs daily at 22:30 UTC (standalone deployment)
  - Can run independently if automatic calculation fails
- **Weekly Company Information Update** - Runs weekly on Sundays at 2 AM UTC
- **Weekly Key Statistics Update** - Runs weekly on Sundays at 3 AM UTC
- **Weekly Company Data Update** - Combined flow running weekly on Sundays at 2 AM UTC

### Step 6: Verify Deployments

Check that deployments were created:

```bash
# List all deployments
prefect deployment ls

# View specific deployment
prefect deployment inspect "Daily Market Data Update/Daily Market Data Update"
```

You can also view deployments in the Prefect UI at http://localhost:4200

### Step 7: Test the Flow (Optional)

Manually trigger a flow run to test:

```bash
# Run the daily market data flow manually
prefect deployment run "Daily Market Data Update/Daily Market Data Update"

# Or with parameters
prefect deployment run "Daily Market Data Update/Daily Market Data Update" --param days_back=7 --param interval=1h
```

## What Gets Deployed

### Daily Market Data Update Flow

- **Schedule**: `15 22 * * 1-5` (22:15 UTC, Monday-Friday)
- **Description**: Daily end-of-day market data ingestion from Yahoo Finance
- **Parameters**:
  - `days_back`: 7 (looks back 7 days to ensure weekday data)
  - `interval`: "1h" (hourly bars)
- **Automatic Actions**:
  1. Loads market data for all active symbols (fetches 7 days from Yahoo Finance API)
  2. **Automatically triggers technical indicators calculation** for successfully loaded symbols
     - Uses `days_back=300` to fetch sufficient historical data from database
     - This ensures indicators like SMA_200 (needs 200 days), RSI_14 (needs 14 days), etc. can be calculated
  3. Returns combined results

### Weekly Flows

- **Company Information Update**: Sundays at 2 AM UTC
- **Key Statistics Update**: Sundays at 3 AM UTC
- **Company Data Update**: Combined flow on Sundays at 2 AM UTC

## Monitoring

### View Flow Runs

1. Open Prefect UI: http://localhost:4200
2. Navigate to "Deployments" or "Flow Runs"
3. Click on a deployment to see:
   - Schedule information
   - Recent flow runs
   - Logs and results
   - Success/failure status

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

# Pause a deployment
prefect deployment pause "Daily Market Data Update/Daily Market Data Update"

# Resume a deployment
prefect deployment resume "Daily Market Data Update/Daily Market Data Update"
```

## Troubleshooting

### Issue: "Work pool not found"

**Solution**: Create the work pool first:
```bash
prefect work-pool create data-ingestion-pool --type process
```

### Issue: "Cannot connect to Prefect API"

**Solution**: 
1. Make sure Prefect server is running
2. Check `PREFECT_API_URL` is set correctly:
   ```bash
   $env:PREFECT_API_URL = "http://localhost:4200/api"
   ```

### Issue: "No worker available"

**Solution**: Start a worker:
```bash
prefect worker start --pool data-ingestion-pool
```

### Issue: Deployment succeeds but flows don't run

**Solution**: 
1. Check that the deployment is active (not paused)
2. Verify the schedule is correct
3. Check worker is running and connected
4. Check Prefect UI for error messages

## Updating Deployments

If you modify the flow code, you need to redeploy:

```bash
# Redeploy all flows
python src/shared/prefect/flows/data_ingestion/yahoo_flows.py
```

The deployment will update existing deployments with the new code.

## Architecture

```
┌─────────────────┐
│ Prefect Server  │  ← Manages deployments and schedules
└────────┬────────┘
         │
         ├───> Deployment: Daily Market Data Update
         │     └───> Schedule: 22:15 UTC Mon-Fri
         │
         ├───> Deployment: Weekly Company Info
         │     └───> Schedule: 2 AM UTC Sunday
         │
         └───> Deployment: Weekly Key Statistics
               └───> Schedule: 3 AM UTC Sunday

┌─────────────────┐
│  Work Pool      │  ← Queues flow runs
│ (data-ingestion)│
└────────┬────────┘
         │
         └───> Worker Process  ← Executes flow runs
```

## Flow Execution Flow

1. **Scheduled Trigger**: Prefect server triggers flow based on schedule
2. **Queue**: Flow run is queued in the work pool
3. **Worker Picks Up**: Worker picks up the flow run
4. **Execute**: Worker executes the flow:
   - Loads market data for all symbols (fetches 7 days from Yahoo Finance API)
   - **Automatically calculates technical indicators** for successful symbols
     - Fetches 300 days of historical data from database (needed for SMA_200, RSI_14, etc.)
     - Calculates all technical indicators
     - Stores results in `analytics.technical_indicators` table
   - Returns combined results
5. **Store Results**: Results stored in Prefect database
6. **View in UI**: View logs and results in Prefect UI

## Understanding days_back Parameter

The `days_back` parameter has different meanings depending on context:

### For Data Ingestion (`yahoo_market_data_flow`)
- **Purpose**: How many days of NEW data to fetch from Yahoo Finance API
- **Value**: `7` days (ensures we get weekday data even if run on weekends)
- **Why**: Efficient - only fetches recent data that might be missing

### For Indicator Calculation (`calculate_daily_indicators`)
- **Purpose**: How many days of HISTORICAL data to fetch from the database
- **Value**: `300` days (default)
- **Why**: Required for indicator calculations:
  - SMA_200 needs 200 days of history
  - SMA_50 needs 50 days
  - RSI_14 needs 14 days
  - MACD needs 26 days
  - Bollinger Bands need 20 days
- **Note**: This fetches from the database (not API), so it's efficient even with 300 days

### Key Point
Even if you only ingest 2-7 days of new data, the indicator calculation still needs 300 days of historical data from the database to calculate all indicators correctly.

## Next Steps

After deployment:
1. Monitor the first few runs in Prefect UI
2. Check logs for any errors
3. Verify data is being loaded correctly
4. Verify technical indicators are being calculated and stored:
   ```sql
   SELECT * FROM analytics.technical_indicators 
   WHERE symbol = 'AAPL' 
   ORDER BY date DESC 
   LIMIT 10;
   ```
5. Adjust schedules if needed via Prefect UI

