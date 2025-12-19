# Trading System

<div align="center">

![Python](https://img.shields.io/badge/Python-3.11+-green?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-red?style=flat-square&logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue?style=flat-square&logo=postgresql)
![Redis](https://img.shields.io/badge/Redis-7+-red?style=flat-square&logo=redis)
![Prefect](https://img.shields.io/badge/Prefect-3.4+-purple?style=flat-square&logo=prefect)

**Production-Grade Algorithmic Trading System**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation](https://img.shields.io/badge/Documentation-MkDocs-blue.svg)](https://nishantnayar.github.io/trading-system)
[![CI/CD Pipeline](https://github.com/nishantnayar/trading-system/workflows/Continuous%20Integration/badge.svg)](https://github.com/nishantnayar/trading-system/actions)
[![Security Scan](https://github.com/nishantnayar/trading-system/workflows/Security%20Scan/badge.svg)](https://github.com/nishantnayar/trading-system/actions)

</div>

---

## Overview

A production-grade algorithmic trading platform designed for equities trading with comprehensive market data integration, automated workflow orchestration, and enterprise-level risk management capabilities. The system supports paper trading through Alpaca Markets API and is built on a modular architecture optimized for scalability and maintainability.

## Key Features

### Trading & Execution
- **Paper Trading Integration**: Safe testing environment via Alpaca paper trading API
- **Live Trading Support**: Production-ready execution infrastructure
- **Strategy Framework**: Plugin-based architecture for custom trading strategies
- **Risk Management**: Built-in position sizing, drawdown limits, and risk controls
- **Backtesting Engine**: Historical strategy validation and performance analysis

### Data Management
- **Multi-Source Data Integration**: Polygon.io, Yahoo Finance, and Alpaca market data
- **Automated Data Ingestion**: Prefect-powered scheduled workflows for daily and weekly data updates
- **Data Quality Assurance**: Automated validation, completeness checks, and quality monitoring
- **Technical Indicators**: Automated calculation of SMA, EMA, RSI, MACD, Bollinger Bands with proper time-series resampling
- **Timezone Management**: UTC storage with configurable display timezone (default: Central Time)

### Analytics & Monitoring
- **Real-Time Dashboard**: Streamlit-based web interface with interactive Plotly visualizations
- **Performance Analytics**: Comprehensive strategy performance metrics and reporting
- **Database-First Logging**: Queryable logs stored in PostgreSQL for operational analysis
- **Workflow Monitoring**: Prefect UI integration for flow execution tracking

### Architecture & Development
- **Modular Monolithic Design**: Service-oriented architecture with clear boundaries
- **Type Safety**: Full mypy compliance with comprehensive type annotations
- **Code Quality**: Automated formatting (Black), linting (Flake8), and static analysis
- **Testing Infrastructure**: Comprehensive test suite with pytest and coverage reporting
- **CI/CD Pipeline**: Automated testing, security scanning, and deployment workflows

## System Architecture

The system employs a **modular monolithic architecture** with the following service boundaries:

- **Data Ingestion Service**: Market data collection, validation, and storage
- **Strategy Engine**: Trading strategy execution and signal generation
- **Execution Service**: Order management and trade execution
- **Risk Management Service**: Position sizing, risk limits, and compliance checks
- **Analytics Service**: Performance analysis and reporting
- **Notification Service**: Alerting and event notifications

### Technology Stack

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Runtime** | Python 3.11+ | Core application runtime |
| **API Framework** | FastAPI 0.100+ | RESTful API services |
| **Database** | PostgreSQL 15+ | Primary data storage and logging |
| **Cache** | Redis 7+ | Caching and message queuing (optional) |
| **Orchestration** | Prefect 3.4+ | Workflow automation and scheduling |
| **Frontend** | Streamlit | Web dashboard and user interface |
| **Data Processing** | pandas, NumPy | Market data analysis and manipulation |
| **Visualization** | Plotly | Interactive charts and analytics |

## Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Python | 3.11+ | Core runtime environment |
| PostgreSQL | 15+ | Primary database |
| Redis | 7+ | Caching layer (optional) |
| Alpaca API | - | Trading and market data access |
| Prefect | 3.4+ | Workflow orchestration (optional) |
| Ollama | Latest | Local LLM for AI features (optional) |

> **Note**: Alpaca paper trading accounts are free and recommended for initial testing and development.

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/nishantnayar/trading-system.git
cd trading-system
```

### 2. Environment Setup

```bash
# Activate conda environment
conda activate your-environment-name

# Install dependencies
pip install -r requirements.txt
```

### 3. Configuration

Create a `.env` file in the project root:

```bash
# Alpaca Trading API (Paper Trading)
ALPACA_API_KEY=your_api_key_here
ALPACA_SECRET_KEY=your_secret_key_here
ALPACA_BASE_URL=https://paper-api.alpaca.markets
ALPACA_DATA_URL=https://data.alpaca.markets

# Database Configuration
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
TRADING_DB_NAME=trading_system

# Redis Configuration (optional)
REDIS_URL=redis://localhost:6379/0

# Application Configuration
DEBUG=false
LOG_LEVEL=INFO

# Prefect Configuration (optional)
PREFECT_API_URL=http://localhost:4200/api
PREFECT_LOGGING_LEVEL=INFO
PREFECT_WORK_POOL_NAME=default-agent-pool
```

### 4. Database Initialization

```bash
# Initialize database schema
python scripts/setup_databases.py
```

### 5. Start Services

```bash
# Start application
python main.py
```

### 6. Access Interfaces

- **Web Dashboard**: http://localhost:8501
- **API Documentation**: http://localhost:8001/docs
- **Prefect UI** (if enabled): http://localhost:4200

## Project Structure

```
trading-system/
├── README.md                          # Project documentation
├── ARCHITECTURE.md                    # System architecture details
├── src/                               # Source code
│   ├── config/                        # Configuration management
│   ├── services/                      # Service modules
│   │   ├── data_ingestion/            # Market data collection
│   │   ├── strategy_engine/           # Trading strategies
│   │   ├── execution/                 # Order management
│   │   ├── risk_management/           # Risk controls
│   │   ├── analytics/                 # Performance analysis
│   │   └── notification/              # Alerts & notifications
│   ├── shared/                        # Shared utilities
│   │   ├── prefect/                   # Workflow orchestration
│   │   │   ├── flows/                 # Prefect flow definitions
│   │   │   ├── tasks/                 # Reusable tasks
│   │   │   └── config.py              # Prefect configuration
│   │   └── logging/                   # Logging utilities
│   └── web/                           # Web interface
│       └── api/                       # REST API endpoints
├── tests/                             # Test suite
├── docs/                              # Documentation
├── deployment/                        # Deployment configurations
├── config/                            # Application configuration
└── scripts/                           # Utility scripts
```

## API Endpoints

### Trading & Account Management

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/alpaca/account` | Retrieve account information |
| `GET` | `/api/alpaca/positions` | List all positions |
| `GET` | `/api/alpaca/orders` | List orders |
| `GET` | `/api/alpaca/clock` | Get market clock status |
| `POST` | `/api/alpaca/positions/{symbol}/close` | Close a position |
| `DELETE` | `/api/alpaca/orders/{order_id}` | Cancel an order |
| `POST` | `/api/alpaca/orders` | Place new order |

### Market Data & Analytics

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/market-data/stats` | Market data statistics |
| `GET` | `/api/market-data/symbols` | Available symbols |
| `GET` | `/api/market-data/data/{symbol}` | Historical data |
| `GET` | `/api/market-data/data/{symbol}/latest` | Latest data point |
| `GET` | `/api/market-data/data/{symbol}/ohlc` | OHLC summary |

## Workflow Orchestration

The system includes Prefect-powered workflow orchestration for automated data ingestion and scheduled tasks.

### Available Flows

1. **Daily Market Data Update**
   - Schedule: Daily at 22:15 UTC (Mon-Fri)
   - Function: Fetches hourly market data from Yahoo Finance
   - Scope: All active symbols

2. **Weekly Company Information Update**
   - Schedule: Sunday at 02:00 UTC
   - Function: Updates company metadata and information

3. **Weekly Key Statistics Update**
   - Schedule: Sunday at 03:00 UTC
   - Function: Updates financial statistics

4. **Weekly Company Data Update** (Combined)
   - Schedule: Sunday at 02:00 UTC
   - Function: Sequential execution of company info and key statistics updates

### Prefect Setup

1. **Install Prefect**:
   ```bash
   pip install prefect>=3.4.0
   ```

2. **Start Prefect Server**:
   ```bash
   prefect server start
   ```
   Access UI at: http://localhost:4200

3. **Deploy Flows**:
   ```bash
   python src/shared/prefect/flows/data_ingestion/yahoo_flows.py
   ```

4. **Start Worker**:
   ```bash
   prefect worker start --pool default-agent-pool
   ```

For detailed deployment instructions, see [Prefect Deployment Plan](docs/development/prefect-deployment-plan.md).

## Development

### Code Quality Standards

The project enforces code quality through automated tooling:

- **Black**: Code formatting (88 character line length)
- **isort**: Import sorting (Black-compatible)
- **Flake8**: Linting and style enforcement
- **mypy**: Static type checking
- **pre-commit**: Git hooks for automated checks

### Setup Development Environment

```bash
# Install pre-commit hooks
pre-commit install

# Format code
black .

# Sort imports
isort .

# Lint code
flake8 .

# Type check
mypy src/
```

All quality checks run automatically via CI/CD on every commit.

### Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test suites
pytest tests/unit/
pytest tests/integration/
```

### Documentation

```bash
# Serve documentation locally
mkdocs serve

# Build documentation
mkdocs build
```

## Configuration

### Strategy Configuration

Edit `config/strategies.yaml`:

```yaml
strategies:
  - name: "momentum_strategy"
    enabled: true
    parameters:
      lookback_period: 20
      momentum_threshold: 0.02
      max_position_size: 0.1
    risk_limits:
      max_drawdown: 0.05
      max_daily_loss: 0.02
```

### Risk Management

Configure in `config/risk_limits.yaml`:

```yaml
risk_management:
  portfolio:
    max_total_exposure: 0.8
    max_drawdown: 0.10
    max_daily_loss: 0.05
```

## Security

- Never commit `.env` files to version control
- Use paper trading credentials for development and testing
- System defaults to paper trading mode
- All trades in paper mode are simulated with virtual funds

## Documentation

| Resource | Description | Link |
|----------|-------------|------|
| Architecture | Detailed system architecture | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Database | Database schema and management | [docs/development/database.md](docs/development/database.md) |
| Logging | Logging architecture and configuration | [docs/development/logging.md](docs/development/logging.md) |
| Prefect | Workflow orchestration guide | [docs/development/prefect-deployment-plan.md](docs/development/prefect-deployment-plan.md) |
| Testing | Testing strategy and guidelines | [docs/development/testing.md](docs/development/testing.md) |
| User Guide | Complete user documentation | [MkDocs](https://nishantnayar.github.io/Trading-System/) |

## Roadmap

| Version | Status | Key Features |
|---------|--------|--------------|
| v1.0.0 | Current | Paper trading, market data integration, web dashboard, Prefect orchestration |
| v1.1.0 | Planned | Strategy engine implementation, backtesting framework, risk management |
| v1.2.0 | Planned | Advanced Prefect workflows, analytics flows, data validation |
| v1.3.0 | Future | Microservices architecture, cloud deployment, distributed execution |

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/feature-name`)
3. Commit changes (`git commit -m 'Add feature'`)
4. Push to branch (`git push origin feature/feature-name`)
5. Open a Pull Request

## Support

- **Issues**: [GitHub Issues](https://github.com/nishantnayar/trading-system/issues)
- **Discussions**: [GitHub Discussions](https://github.com/nishantnayar/trading-system/discussions)
- **Email**: nishant.nayar@hotmail.com

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Risk Disclaimer

**This software is for educational and research purposes only. Trading involves substantial risk of loss and is not suitable for all investors. Past performance is not indicative of future results. Use at your own risk.**

## Acknowledgments

- **Alpaca Markets** - Trading API infrastructure
- **FastAPI** - Modern web framework
- **Polygon.io** - Market data services
- **Prefect** - Workflow orchestration platform
- **Python Community** - Open-source ecosystem

---

<div align="center">

Developed by [Nishant Nayar](https://github.com/nishantnayar)

[![GitHub](https://img.shields.io/badge/GitHub-nishantnayar-black?style=flat-square&logo=github)](https://github.com/nishantnayar)
[![Email](https://img.shields.io/badge/Email-nishant.nayar@hotmail.com-blue?style=flat-square&logo=mail)](mailto:nishant.nayar@hotmail.com)

</div>
