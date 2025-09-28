# Getting Started

This comprehensive guide will help you install, configure, and run the Trading System for the first time.

## Prerequisites

### System Requirements

- **Operating System**: Windows 10+ (recommended for local deployment)
- **Python**: 3.11+ (required)
- **Database**: PostgreSQL 15+ (required)
- **Cache**: Redis 7+ (optional but recommended)
- **Memory**: 8GB+ RAM (recommended)
- **Storage**: 10GB+ free space

### Required Software

1. **Python 3.11+**
   - Download from [python.org](https://www.python.org/downloads/)
   - Or use Anaconda: [anaconda.com](https://www.anaconda.com/download)

2. **PostgreSQL 15+**
   - Download from [postgresql.org](https://www.postgresql.org/download/)
   - Or use package manager:
     ```bash
     # Windows (Chocolatey)
     choco install postgresql
     
     # macOS (Homebrew)
     brew install postgresql
     
     # Ubuntu/Debian
     sudo apt-get install postgresql postgresql-contrib
     ```

3. **Redis 7+** (Optional)
   - Download from [redis.io](https://redis.io/download)
   - Or use package manager:
     ```bash
     # Windows (Chocolatey)
     choco install redis
     
     # macOS (Homebrew)
     brew install redis
     
     # Ubuntu/Debian
     sudo apt-get install redis-server
     ```

## Installation

### Step 1: Clone the Repository

```bash
# Clone the repository
git clone https://github.com/nishantnayar/trading-system.git
cd trading-system
```

### Step 2: Create Python Environment

**Using Anaconda (Recommended)**:
```bash
# Create conda environment
conda create -n trading-system python=3.11
conda activate trading-system
```

**Using venv**:
```bash
# Create virtual environment
python -m venv trading-system-env

# Activate environment
# Windows
trading-system-env\Scripts\activate
# macOS/Linux
source trading-system-env/bin/activate
```

### Step 3: Install Dependencies

```bash
# Install core dependencies
pip install -r requirements.txt

# Install test dependencies (optional)
pip install -r requirements-test.txt
```

### Step 4: Verify Installation

```bash
# Check Python version
python --version

# Check installed packages
pip list

# Verify core dependencies
python -c "import sqlalchemy, redis, fastapi; print('Core dependencies installed successfully')"
```

## Configuration

### Step 1: Environment Configuration

1. **Copy the environment template**:
   ```bash
   cp deployment/env.example .env
   ```

2. **Edit the `.env` file** with your settings:
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
   
   # Alpaca API Configuration
   ALPACA_API_KEY=your_api_key_here
   ALPACA_SECRET_KEY=your_secret_key_here
   ALPACA_BASE_URL=https://paper-api.alpaca.markets
   
   # Application Configuration
   APP_NAME=Trading System
   APP_VERSION=1.0.0
   DEBUG=false
   LOG_LEVEL=INFO
   ```

### Step 2: Database Setup

1. **Start PostgreSQL**:
   ```bash
   # Windows
   net start postgresql-x64-15
   
   # Linux/macOS
   sudo systemctl start postgresql
   # or
   sudo service postgresql start
   ```

2. **Run database setup script**:
   ```bash
   python scripts/setup_databases.py
   ```

   This script will:
   - Create the `trading_system` database
   - Create the `prefect` database
   - Create service-specific schemas
   - Configure Prefect database connection

### Step 3: Verify Database Setup

```bash
# Test database connections
python scripts/test_database_connections.py
```

Expected output:
```
Database Connection Verification
==================================================
Quick verification of database connections and basic functionality.
For comprehensive testing, use: python scripts/run_tests.py unit
==================================================

--- Trading Database ---
trading_system database connection successful

--- Prefect Database ---
Prefect database connection successful

--- Service Schemas ---
Schema 'data_ingestion' for service 'data_ingestion' is accessible
Schema 'strategy_engine' for service 'strategy_engine' is accessible
Schema 'execution' for service 'execution' is accessible
Schema 'risk_management' for service 'risk_management' is accessible
Schema 'analytics' for service 'analytics' is accessible
Schema 'notification' for service 'notification' is accessible
Schema 'logging' for service 'logging' is accessible
Schema 'shared' for service 'shared' is accessible

--- Connection Pools ---
Trading database pool: size=10, checked_out=0
Prefect database pool: size=10, checked_out=0

Verification Results: 4/4 checks passed
SUCCESS: All database connections verified!
Database is ready for use.
```

### Step 4: Alpaca API Setup (Optional)

1. **Sign up for Alpaca**:
   - Go to [Alpaca Markets](https://alpaca.markets/)
   - Create an account
   - Verify your identity

2. **Generate API Keys**:
   - Go to your dashboard
   - Navigate to API Keys section
   - Generate new API keys
   - Copy the API key and secret key

3. **Update `.env` file**:
   ```env
   ALPACA_API_KEY=your_actual_api_key
   ALPACA_SECRET_KEY=your_actual_secret_key
   ALPACA_BASE_URL=https://paper-api.alpaca.markets
   ```

## First Run

### Step 1: Start Redis (Optional)

```bash
# Start Redis server
redis-server

# Or start as service
# Windows
net start redis
# Linux/macOS
sudo systemctl start redis
```

### Step 2: Start Prefect Server

```bash
# Start Prefect server
prefect server start
```

The Prefect UI will be available at `http://localhost:4200`.

### Step 3: Run the Application

```bash
# Start the trading system
python scripts/run.py
```

Or start individual components:

```bash
# Start web server
python -m src.web.main

# Start specific services
python -m src.services.data_ingestion.main
python -m src.services.strategy_engine.main
python -m src.services.execution.main
```

### Step 4: Access the Dashboard

1. **Open your browser** and go to `http://localhost:8000`
2. **Check the dashboard** for system status
3. **Verify all services** are running correctly

## Verification

### Step 1: Run Tests

```bash
# Run quick verification
python scripts/test_database_connections.py

# Run unit tests
python scripts/run_tests.py unit

# Run all tests
python scripts/run_tests.py all
```

### Step 2: Check Service Health

```bash
# Check if all services are running
curl http://localhost:8000/health

# Check individual services
curl http://localhost:8001/health  # Data Ingestion
curl http://localhost:8002/health  # Strategy Engine
curl http://localhost:8003/health  # Execution
```

### Step 3: Verify Database

```bash
# Connect to PostgreSQL
psql -h localhost -U postgres -d trading_system

# Check schemas
\dn

# Check tables
\dt

# Exit
\q
```

### Step 4: Check Logs

```bash
# View system logs
tail -f logs/trading.log

# View specific service logs
tail -f logs/data_ingestion.log
tail -f logs/strategy_engine.log
```

## Next Steps

### 1. Explore the System

- **Dashboard**: Navigate through the web interface
- **Prefect UI**: Check workflow management at `http://localhost:4200`
- **API Documentation**: Visit `http://localhost:8000/docs`

### 2. Configure Trading

- **Set up strategies**: Configure your trading strategies
- **Risk management**: Set appropriate risk limits
- **Paper trading**: Start with paper trading to test strategies

### 3. Development

- **Read documentation**: Check the comprehensive documentation
- **Run tests**: Ensure all tests pass
- **Code quality**: Use the built-in code quality tools

### 4. Production Deployment

- **Security**: Review security settings
- **Monitoring**: Set up monitoring and alerting
- **Backup**: Implement backup strategies

## Troubleshooting

If you encounter issues during setup:

1. **Check the logs**: Review error messages in log files
2. **Verify prerequisites**: Ensure all required software is installed
3. **Check configuration**: Verify your `.env` file settings
4. **Run diagnostics**: Use the built-in diagnostic scripts
5. **Review documentation**: Check the troubleshooting guide

For detailed troubleshooting information, see [Troubleshooting Guide](troubleshooting.md).

## Support

- **Documentation**: [Complete Documentation](https://nishantnayar.github.io/trading-system)
- **GitHub Issues**: [Report Issues](https://github.com/nishantnayar/trading-system/issues)
- **Discussions**: [GitHub Discussions](https://github.com/nishantnayar/trading-system/discussions)
- **Email**: nishant.nayar@hotmail.com

---

**Congratulations!** You've successfully set up the Trading System. You're now ready to start developing and trading!
