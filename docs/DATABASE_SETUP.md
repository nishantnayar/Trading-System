# Database Setup Guide

This guide walks you through setting up the database architecture for the Trading System, following the separate database strategy for Prefect 3.4.14 compatibility.

## Overview

The system uses two separate PostgreSQL databases:
- **trading_system**: Contains all trading data and service-specific schemas
- **prefect**: Dedicated database for Prefect orchestration

## Prerequisites

- PostgreSQL 12+ installed and running
- Python 3.11+ with required dependencies
- Prefect 3.4.14+ installed
- Redis server (optional, for caching)

## Step 1: Environment Configuration

1. Copy the environment template:
```bash
cp deployment/env.example .env
```

2. Edit `.env` with your database credentials:
```env
# Database Configuration - Trading System
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password_here
TRADING_DB_NAME=trading_system

# Database Configuration - Prefect
PREFECT_DB_NAME=prefect
PREFECT_API_DATABASE_CONNECTION_URL=postgresql+asyncpg://postgres:password@localhost:5432/prefect

# Redis Configuration
REDIS_URL=redis://localhost:6379/0
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

## Step 2: Database Setup

Run the database setup script:

```bash
python scripts/setup_databases.py
```

This script will:
- Create the `Prefect` database
- Create service-specific schemas in `trading_system`
- Configure Prefect to use PostgreSQL
- Note: Prefect will automatically initialize its tables when the server starts

## Step 3: Verify Setup

Test the database connections:

```bash
python scripts/test_database_connections.py
```

This will verify:
- Trading system database connectivity
- Prefect database connectivity
- Service schema accessibility
- Connection pool configuration

## Step 4: Start Prefect Server

Once the databases are set up, start the Prefect server:

```bash
prefect server start
```

The Prefect UI will be available at `http://localhost:4200`.

## Database Architecture

### Trading System Database

The `trading_system` database contains the following schemas:

- **data_ingestion**: Market data, data quality logs
- **strategy_engine**: Strategies, signals, performance metrics
- **execution**: Orders, trades, positions, execution logs
- **risk_management**: Risk limits, events, position limits
- **analytics**: Performance calculations, reports
- **notification**: Alert configurations, notification logs
- **logging**: Centralized system logs
- **shared**: Shared utilities and common tables

### Prefect Database

The `prefect` database contains Prefect's internal tables:
- flow_runs
- task_runs
- deployments
- work_pools
- blocks
- (other Prefect tables)

## Connection Management

The system uses SQLAlchemy with connection pooling:

```python
from src.config.database import get_engine, get_service_engine

# Get trading database engine
trading_engine = get_engine("trading")

# Get service-specific engine
data_engine = get_service_engine("data_ingestion")

# Get Prefect engine
prefect_engine = get_engine("prefect")
```

## Troubleshooting

### Common Issues

1. **Connection Refused**
   - Ensure PostgreSQL is running
   - Check host and port configuration
   - Verify user credentials

2. **Database Not Found**
   - Run the setup script again
   - Check database names in configuration

3. **Schema Not Found**
   - Verify the setup script completed successfully
   - Check schema names in the schemas mapping

4. **Prefect Connection Issues**
   - Ensure Prefect is installed: `pip install prefect`
   - Check the Prefect database URL format
   - Verify asyncpg driver is installed: `pip install asyncpg`

### Logs

Check the application logs for detailed error messages:
```bash
tail -f logs/trading.log
```

## Next Steps

After successful database setup:

1. **Phase 2**: Implement core trading tables and schemas
2. **Phase 3**: Set up connection management and pooling
3. **Phase 4**: Implement data synchronization
4. **Phase 5**: Add monitoring and maintenance

## Security Considerations

- Use strong passwords for database users
- Consider using SSL connections for production
- Implement proper user permissions
- Regular security updates

## Backup Strategy

- Regular database backups
- Test restore procedures
- Monitor disk space
- Document recovery procedures

---

For detailed architecture information, see [DATABASE_ARCHITECTURE_DETAILED.md](DATABASE_ARCHITECTURE_DETAILED.md).
