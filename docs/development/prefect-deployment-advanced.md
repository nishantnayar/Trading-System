# Prefect Deployment Advanced Topics

> **📋 Implementation Status**: 🚧 In Progress  
> **Prefect Version**: 3.4.14

This document covers advanced topics including design decisions, the `days_back` parameter, and migration strategy.

## Key Design Decisions

### Why `serve()` API?

Prefect 3.x introduces the `serve()` API which is simpler than the older deployment building approach. Flows can be deployed by calling `.serve()` on the flow object.

**Benefits:**
- Simpler API than previous deployment builders
- Python-based configuration (easier to version control)
- Dynamic deployment logic
- Better integration with code

### Why Separate Work Pools?

- **Resource Isolation**: Different pools can have different resource limits
- **Parallelism Control**: Limit concurrent executions per pool
- **Environment Separation**: Different pools can use different environments

**Example:**
- `data-ingestion-pool`: For data ingestion flows (Polygon, Yahoo)
- `analytics-pool`: For analytics flows (indicator calculations)
- `maintenance-pool`: For maintenance flows (cleanup, archiving)

### Why YAML + Python?

- **YAML**: For static configuration (work pools, schedules)
- **Python**: For dynamic deployment logic and code reuse

**Best Practice:**
- Use YAML for initial setup and static configurations
- Use Python `serve()` API for actual deployments (more flexible)

### Task Granularity

**Coarse-grained tasks**: One task per symbol (better for parallelization)
- Example: `load_polygon_symbol_data_task(symbol)` processes entire symbol
- Better for: Large-scale parallel processing
- Trade-off: Less granular observability

**Fine-grained tasks**: Separate tasks for fetch/validate/store (better for observability)
- Example: `fetch_data_task()`, `validate_data_task()`, `store_data_task()`
- Better for: Detailed monitoring and debugging
- Trade-off: More overhead, less parallelization

**Recommendation**: Start coarse-grained, refine as needed.

## Understanding days_back Parameter

### Different Meanings for Different Contexts

The `days_back` parameter has different meanings depending on whether it's used for data ingestion or indicator calculation:

### For Data Ingestion Flows

- **Purpose**: How many days of NEW data to fetch from external API (Yahoo Finance, Polygon)
- **Typical Value**: `7` days (for hourly data) or `30` days (for daily data)
- **Why**: Efficient - only fetches recent data that might be missing or updated
- **Example**: `yahoo_market_data_flow` uses `days_back=7` to fetch 7 days of hourly data

**Use Case:**
```python
# Fetch last 7 days of hourly data from Yahoo Finance API
yahoo_market_data_flow(days_back=7, interval="1h")
```

### For Indicator Calculation Flows

- **Purpose**: How many days of HISTORICAL data to fetch from the database
- **Typical Value**: `300` days (default)
- **Why**: Required for accurate indicator calculations:
  - **SMA_200**: Needs 200 days of history
  - **SMA_50**: Needs 50 days
  - **SMA_20**: Needs 20 days
  - **RSI_14**: Needs 14 days
  - **MACD**: Needs 26 days (slow EMA)
  - **Bollinger Bands**: Needs 20 days
  - **Volatility_20**: Needs 20 days
- **Note**: This fetches from the database (not API), so fetching 300 days is efficient
- **Example**: `calculate_daily_indicators` uses `days_back=300` to fetch historical data from DB

**Use Case:**
```python
# Fetch 300 days of historical data from database to calculate indicators
calculate_daily_indicators(days_back=300)
```

### Key Point

Even if you only ingest 2-7 days of new data from the API, the indicator calculation still needs 300 days of historical data from the database to calculate all indicators correctly.

**Flow:**
1. Data ingestion: `days_back=7` → Fetches 7 days from API → Stores in database
2. Indicator calculation: `days_back=300` → Fetches 300 days from database → Calculates indicators

### Automatic Indicator Calculation

The `yahoo_market_data_flow` automatically triggers indicator calculation after successful data ingestion:
- Data ingestion uses `days_back=7` (fetches 7 days from API)
- Indicator calculation uses `days_back=300` (fetches 300 days from database)
- Both values are correct for their respective purposes

## Migration Strategy

### Phase 1: Parallel Run

- Keep existing scripts working
- Deploy Prefect flows alongside
- Compare results
- Monitor both systems

**Duration**: 1-2 weeks

### Phase 2: Validation

- Run both systems for 1-2 weeks
- Verify data consistency
- Monitor Prefect flows
- Document any discrepancies

**Duration**: 1-2 weeks

### Phase 3: Cutover

- Make Prefect flows primary
- Keep scripts as fallback
- Document deprecation
- Update documentation

**Duration**: Ongoing

### Phase 4: Cleanup

- Remove old scripts (optional)
- Update documentation
- Train team on Prefect UI
- Archive old deployment methods

**Duration**: As needed

## Best Practices

### 1. Incremental Development

- Start with one flow
- Test thoroughly
- Add flows incrementally
- Don't try to migrate everything at once

### 2. Error Handling

- Use retries for transient failures
- Log all errors with context
- Set appropriate timeouts
- Handle partial failures gracefully

### 3. Monitoring

- Use Prefect UI for real-time monitoring
- Set up alerts for critical flows
- Track flow run success rates
- Monitor resource usage

### 4. Testing

- Write unit tests for tasks
- Write integration tests for flows
- Test with limited data first
- Verify data consistency

### 5. Documentation

- Document all flows and their purposes
- Keep configuration examples up to date
- Document migration steps
- Maintain troubleshooting guides

## Related Documentation

- [Prefect Deployment Overview](prefect-deployment-overview.md) - Overview and project structure
- [Prefect Configuration](prefect-deployment-configuration.md) - YAML configs, environment variables, settings
- [Code Patterns](prefect-deployment-code-patterns.md) - Task patterns, flow patterns, deployment definitions
- [Deployment Workflow](prefect-deployment-workflow.md) - Deployment scripts, workflow steps, monitoring, testing

---

**Last Updated**: December 2025  
**Status**: 🚧 In Progress

