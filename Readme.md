# Trading System

<div align="center">

![Trading System](https://img.shields.io/badge/Trading-System-blue?style=for-the-badge&logo=python)
![Python](https://img.shields.io/badge/Python-3.11+-green?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-red?style=flat-square&logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue?style=flat-square&logo=postgresql)
![Redis](https://img.shields.io/badge/Redis-7+-red?style=flat-square&logo=redis)
![Prefect](https://img.shields.io/badge/Prefect-3.4+-purple?style=flat-square&logo=prefect)

**A production-grade algorithmic trading system for equities trading**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation](https://img.shields.io/badge/Documentation-MkDocs-blue.svg)](https://nishantnayar.github.io/trading-system)
[![CI/CD Pipeline](https://github.com/nishantnayar/trading-system/workflows/Continuous%20Integration/badge.svg)](https://github.com/nishantnayar/trading-system/actions)
[![Security Scan](https://github.com/nishantnayar/trading-system/workflows/Security%20Scan/badge.svg)](https://github.com/nishantnayar/trading-system/actions)
[![GitHub Issues](https://img.shields.io/github/issues/nishantnayar/trading-system)](https://github.com/nishantnayar/trading-system/issues)
[![GitHub Stars](https://img.shields.io/github/stars/nishantnayar/trading-system)](https://github.com/nishantnayar/trading-system/stargazers)

</div>

---

A production-grade algorithmic trading system designed for local deployment, focusing on equities trading through Alpaca with paper trading capabilities. Built with modern Python technologies and microservices architecture for scalability and maintainability.

## 🎯 Overview

A comprehensive algorithmic trading platform built for modern financial markets, featuring real-time data processing, advanced analytics, and professional-grade risk management capabilities.

## 🏗️ Architecture

This system uses a **modular monolithic architecture** with clear service boundaries, providing:

- **Service-Oriented Modules**: Data Ingestion, Strategy Engine, Execution, Risk Management, Analytics, and Notification
- **Modern Tech Stack**: Python + FastAPI + PostgreSQL + Redis + pandas
- **Workflow Orchestration**: Prefect 3.4+ for automated data ingestion and scheduled tasks
- **Professional Frontend**: Streamlit + Plotly Charts + Custom CSS
- **Scalable Design**: Prepared for future microservices migration
- **Comprehensive Monitoring**: Database-first logging with Loguru (PostgreSQL + file fallback)

### Key Features

| Feature | Description |
|---------|-------------|
| 🚀 **Paper Trading** | Safe testing environment with Alpaca paper trading API |
| 📊 **Market Data** | Historical data from Polygon.io, Yahoo Finance, and Alpaca with comprehensive analytics |
| 🤖 **AI-Powered Screener** | Natural language stock screening with local LLM (Ollama) integration |
| 🧠 **Strategy Engine** | Plugin-based framework for custom trading strategies |
| ⚡ **Risk Management** | Built-in position sizing and risk controls |
| 📈 **Analytics** | Interactive charts and performance tracking with Plotly |
| 🔄 **Backtesting** | Historical strategy validation framework |
| 📱 **Web Dashboard** | Modern Streamlit multipage interface with session state |
| 🔧 **Modular Design** | Scalable, maintainable service-oriented architecture |
| 🗄️ **Database** | PostgreSQL with comprehensive schema design |
| 📊 **Data Quality** | Automated data validation and quality monitoring |
| 🌍 **Timezone Support** | UTC storage with Central Time display for all data |
| ⚙️ **Workflow Orchestration** | Prefect-powered automated data ingestion with scheduled flows |

## 🚀 Quick Start

### Streamlit UI

The trading system now features a modern **Streamlit multipage interface** with:

- **Portfolio Management**: Real-time portfolio tracking and performance metrics
- **Market Analysis**: Interactive charts with technical indicators using Plotly
- **Stock Screener**: AI-powered stock screening with natural language queries (Ollama integration)
- **System Information**: Team details and system architecture
- **Settings**: User preferences and session state management
- **Session State**: Persistent data sharing across all pages

**Access the UI**: http://localhost:8501

### Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| **Python** | 3.11+ | Core runtime |
| **Anaconda** | Latest | Package management |
| **PostgreSQL** | 15+ | Primary database |
| **Redis** | 7+ | Caching and messaging (optional) |
| **Alpaca API** | - | Trading and market data |
| **Prefect** | 3.4+ | Workflow orchestration (optional, for automated data ingestion) |
| **Ollama** | Latest | Local LLM for AI-powered features (optional) |

> **Note**: Alpaca paper trading account is free and recommended for testing

### Alpaca API Setup

#### 1. Get Alpaca Paper Trading Credentials

1. Go to [Alpaca Paper Trading Dashboard](https://app.alpaca.markets/paper/dashboard/overview)
2. Sign up for a free account if you don't have one
3. Go to **API Keys** section
4. Generate new API keys for paper trading
5. Copy your **API Key** and **Secret Key**

#### 2. Set Up Environment Variables

Create a `.env` file in the project root with your credentials:

```bash
# Alpaca Trading API (Paper Trading)
ALPACA_API_KEY=your_actual_api_key_here
ALPACA_SECRET_KEY=your_actual_secret_key_here
ALPACA_BASE_URL=https://paper-api.alpaca.markets
ALPACA_DATA_URL=https://data.alpaca.markets

# Database Configuration (if using database features)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password_here
TRADING_DB_NAME=trading_system

# Redis Configuration (if using Redis features)
REDIS_URL=redis://localhost:6379/0

# Application Configuration
DEBUG=true
LOG_LEVEL=INFO

# Prefect Configuration (optional, for workflow orchestration)
PREFECT_API_URL=http://localhost:4200/api
PREFECT_LOGGING_LEVEL=INFO
PREFECT_WORK_POOL_NAME=default-agent-pool
```

#### 3. Alpaca API Features Available

- **Real-time Portfolio Data** - Live account balance and P&L
- **Live Positions** - Current holdings with real-time P&L
- **Order Management** - View and cancel open orders
- **Market Status** - Real-time market open/closed status
- **Trading Interface** - Place new orders (coming soon)

#### 4. API Endpoints

The following API endpoints are available:

**Trading & Account Management:**
- `GET /api/alpaca/account` - Get account information
- `GET /api/alpaca/positions` - Get all positions
- `GET /api/alpaca/orders` - Get orders
- `GET /api/alpaca/clock` - Get market clock
- `POST /api/alpaca/positions/{symbol}/close` - Close a position
- `DELETE /api/alpaca/orders/{order_id}` - Cancel an order
- `POST /api/alpaca/orders` - Place new orders

**Market Data & Analytics:**
- `GET /api/market-data/stats` - Get market data statistics
- `GET /api/market-data/symbols` - Get available symbols
- `GET /api/market-data/data/{symbol}` - Get historical data
- `GET /api/market-data/data/{symbol}/latest` - Get latest data
- `GET /api/market-data/data/{symbol}/ohlc` - Get OHLC summary

#### 5. Security Notes

- Never commit your `.env` file to version control
- Use paper trading credentials for testing
- The system is configured for paper trading by default
- All trades are simulated and use virtual money

#### 6. Troubleshooting

**Common Issues:**

1. **"Alpaca credentials not found"**
   - Make sure your `.env` file exists and has the correct variable names
   - Check that the credentials are valid

2. **"Connection failed"**
   - Verify your API keys are correct
   - Check your internet connection
   - Ensure you're using paper trading credentials

3. **"API Error"**
   - Check if your account is active
   - Verify the API keys have the correct permissions

**Getting Help:**
- Check the console logs for detailed error messages
- Verify your Alpaca account status in the dashboard
- Test your credentials by accessing the Streamlit UI at `http://localhost:8501`

### Installation

<details>
<summary><strong>Step-by-step installation guide</strong></summary>

#### 1. Clone Repository
```bash
git clone https://github.com/nishantnayar/trading-system.git
cd trading-system
```

#### 2. Setup Environment
```bash
# Activate your existing conda environment
conda activate your-environment-name

# Install dependencies
pip install -r deployment/requirements.txt
```

#### 3. Configure Environment
```bash
# Copy environment template
cp deployment/env.example .env

# Edit .env with your API credentials:
# - Alpaca API keys: https://app.alpaca.markets/paper/dashboard/overview
# - Polygon.io API key (optional, for historical data)
# - Database credentials
# - Redis URL (optional)
```

#### 4. Initialize Database
```bash
# Start PostgreSQL and Redis services
# Then initialize the database
python deployment/scripts/setup_database.py
```

#### 5. Start Services
```bash
# Start all microservices
python deployment/scripts/start_services.py
```

#### 6. Access Dashboard
- **Streamlit UI**: http://localhost:8501
- **API Docs**: http://localhost:8001/docs

</details>

## 📁 Project Structure

```
trading-system/
├── README.md                    # This file
├── ARCHITECTURE.md              # Detailed system architecture
├── src/                         # Source code
│   ├── config/                  # Configuration management
│   ├── services/                # Microservices
│   │   ├── data_ingestion/      # Market data collection
│   │   ├── strategy_engine/     # Trading strategies
│   │   ├── execution/           # Order management
│   │   ├── risk_management/     # Risk controls
│   │   ├── analytics/           # Performance analysis
│   │   └── notification/        # Alerts & notifications
│   ├── shared/                  # Shared utilities
│   │   └── prefect/             # Prefect workflow orchestration
│   │       ├── flows/           # Prefect flows (data ingestion, analytics)
│   │       ├── tasks/           # Reusable Prefect tasks
│   │       └── config.py        # Prefect configuration
│   └── web/                     # Web interface
├── tests/                       # Test suite
├── docs/                        # Documentation
├── deployment/                  # Setup & environment files
├── config/                      # Application configuration
├── tools/                       # Development tools
└── logs/                        # Log files (fallback only - primary logging in PostgreSQL)
```

## 🛠️ Development

### Code Quality

The project uses modern Python development tools with pre-configured settings:

- **Black** - Code formatting (88 character line length)
- **isort** - Import sorting (Black-compatible profile)
- **Flake8** - Linting and style checks
- **mypy** - Type checking and static analysis
- **pre-commit** - Git hooks for automated checks

**Configuration Files:**
- `.isort.cfg` - Import sorting configuration (Black-compatible)
- `pytest.ini` - Test configuration with markers
- All tools work together seamlessly

Setup development environment:
```bash
# Install pre-commit hooks
pre-commit install

# Format code (Black)
black .

# Sort imports (isort)
isort .

# Lint code (Flake8)
flake8 .

# Type check (mypy)
mypy src/
```

**Automated in CI/CD:**
All code quality checks run automatically on every push and pull request.

### Testing

Run the test suite:
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test types
pytest tests/unit/
pytest tests/integration/
```

### Documentation

Build documentation:
```bash
# User documentation (MkDocs)
mkdocs serve

# Technical documentation (MkDocs)
mkdocs build
```

## 📊 Features

### 🚀 Trading Capabilities
- **Paper Trading**: Safe testing environment with Alpaca paper API
- **Live Trading**: Production-ready execution for real money
- **Multiple Strategies**: Plugin-based framework for custom strategies
- **Risk Management**: Built-in position sizing and risk controls
- **Backtesting**: Historical strategy validation and optimization

### 📈 Data Processing
- **Historical Data**: Polygon.io and Yahoo Finance integration for backtesting and analysis
- **Automated Data Ingestion**: Prefect-powered scheduled flows for daily market data and weekly company information updates
- **Market Data Analytics**: Comprehensive data processing with pandas
- **Technical Indicators**: Automatic hourly-to-daily resampling for accurate indicator calculations (SMA, EMA, RSI, MACD, Bollinger Bands)
- **Data Quality Monitoring**: Automated validation and quality checks
- **Performance Metrics**: Detailed analytics and reporting
- **Interactive Charts**: Plotly integration for financial visualizations
- **Timezone Handling**: All data stored in UTC, displayed in Central Time

### 🔔 Monitoring & Alerts
- **Real-time Dashboard**: Live portfolio monitoring and control
- **Performance Tracking**: Strategy performance metrics and analytics
- **Risk Monitoring**: Continuous risk assessment and alerts
- **Database Logging**: Queryable logs stored in PostgreSQL for analysis and debugging
- **Email Notifications**: Critical event notifications and reports

### 🛠️ Development Features
- **Modular Architecture**: Service-oriented design ready for scaling
- **Modern Frontend**: Streamlit + Plotly Charts + Custom CSS interface
- **Workflow Orchestration**: Prefect 3.4+ integration for automated data ingestion workflows
- **AI Integration**: Local LLM support via Ollama for natural language processing
- **Comprehensive Logging**: Database-first logging system with PostgreSQL storage and file fallback
- **Code Quality**: Black, Flake8, mypy, and pre-commit hooks
- **Testing Suite**: Comprehensive test coverage across all components
- **Type Safety**: Complete mypy compliance with proper type annotations
- **Database Testing**: Schema validation and fixture management
- **CI/CD Pipeline**: Automated testing, security scanning, and deployment

## 🔧 Configuration

### Strategy Configuration
Edit `config/strategies.yaml` to configure trading strategies:

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
Configure risk limits in `config/risk_limits.yaml`:

```yaml
risk_management:
  portfolio:
    max_total_exposure: 0.8
    max_drawdown: 0.10
    max_daily_loss: 0.05
```

## 📈 Usage

### Starting the System

1. **Start the application**:
   ```bash
   python main.py
   ```

2. **Access Streamlit UI**: http://localhost:8501

3. **Monitor logs**: Check `logs/` directory for system logs

### Strategy Development

1. **Create new strategy**:
   ```python
   # src/services/strategy_engine/strategies/my_strategy.py
   from .strategy_base import BaseStrategy
   
   class MyStrategy(BaseStrategy):
       def generate_signals(self, data):
           # Your strategy logic here
           pass
   ```

2. **Configure strategy** in `config/strategies.yaml`

3. **Backtest strategy**:
   ```python
   # Use Jupyter notebooks in docs/notebooks/backtesting/
   ```

### AI-Powered Stock Screener

The system includes an AI-powered stock screener with natural language query support:

1. **Install Ollama** (optional but recommended):
   ```bash
   # Download from https://ollama.ai
   # Install a model:
   ollama pull phi3
   ```

2. **Access the Screener**:
   - Navigate to the Screener page in the Streamlit UI
   - Use natural language queries like "Find tech stocks with RSI below 30"
   - Or use traditional filters for precise screening

3. **Test Ollama Connection**:
   ```bash
   python scripts/test_ollama.py
   ```

See [Stock Screener Guide](docs/user-guide/stock-screener.md) for detailed documentation.

### Prefect Workflow Orchestration

The system includes Prefect-powered workflow orchestration for automated data ingestion:

#### Available Flows

1. **Daily Market Data Update**
   - Scheduled: Daily at 22:15 UTC (Mon-Fri) - after US market close
   - Fetches hourly market data from Yahoo Finance
   - Automatically processes all active symbols

2. **Weekly Company Information Update**
   - Scheduled: Weekly on Sunday at 2:00 AM UTC
   - Updates company information and metadata

3. **Weekly Key Statistics Update**
   - Scheduled: Weekly on Sunday at 3:00 AM UTC
   - Updates key financial statistics

4. **Weekly Company Data Update** (Combined)
   - Scheduled: Weekly on Sunday at 2:00 AM UTC
   - Runs company info and key statistics updates sequentially

#### Setting Up Prefect

1. **Install Prefect** (if not already installed):
   ```bash
   pip install prefect>=3.4.0
   ```

2. **Start Prefect Server**:
   ```bash
   prefect server start
   ```
   Access Prefect UI at: http://localhost:4200

3. **Deploy Flows**:
   ```bash
   # Deploy all Yahoo Finance flows
   python src/shared/prefect/flows/data_ingestion/yahoo_flows.py
   ```

4. **Start Prefect Worker** (in a separate terminal):
   ```bash
   prefect worker start --pool default-agent-pool
   ```

#### Prefect UI

- **Access**: http://localhost:4200
- **Features**:
  - Monitor flow runs in real-time
  - View execution logs and history
  - Manage schedules and deployments
  - Track flow performance and failures

#### Manual Flow Execution

You can also run flows manually for testing:

```python
from src.shared.prefect.flows.data_ingestion.yahoo_flows import (
    yahoo_market_data_flow,
    yahoo_company_info_flow,
    yahoo_key_statistics_flow,
)

# Run market data flow for specific symbols
await yahoo_market_data_flow(
    symbols=["AAPL", "GOOGL"],
    days_back=7,
    interval="1h"
)
```

See [Prefect Deployment Plan](docs/development/prefect-deployment-plan.md) for detailed documentation.

## 🚨 Risk Disclaimer

**This software is for educational and research purposes only. Trading involves substantial risk of loss and is not suitable for all investors. Past performance is not indicative of future results.**

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📞 Support

| Resource | Description | Link |
|----------|-------------|------|
| 📚 **Architecture** | Detailed system architecture | [ARCHITECTURE.md](ARCHITECTURE.md) |
| 🗄️ **Database** | Database architecture & session management | [docs/development/database.md](docs/development/database.md) |
| 📋 **Logging** | Database-first logging with PostgreSQL | [docs/development/logging.md](docs/development/logging.md) |
| ⚙️ **Prefect** | Workflow orchestration and deployment | [docs/development/prefect-deployment-plan.md](docs/development/prefect-deployment-plan.md) |
| 🧪 **Testing** | Testing strategy and guidelines | [docs/development/testing.md](docs/development/testing.md) |
| 📖 **User Documentation** | Complete user and developer docs | [MkDocs](https://nishantnayar.github.io/Trading-System/) |
| 🐛 **Issues** | Report bugs and request features | [GitHub Issues](https://github.com/nishantnayar/trading-system/issues) |
| 💬 **Discussions** | Community discussions and Q&A | [GitHub Discussions](https://github.com/nishantnayar/trading-system/discussions) |
| 📧 **Contact** | Direct contact for support | nishant.nayar@hotmail.com |

## 🔄 Roadmap

| Version | Status | Features |
|---------|--------|----------|
| **v1.0.0** | Current | Paper trading, market data integration, web dashboard, AI-powered stock screener, Prefect orchestration |
| **v1.1.0** | Planned | Strategy engine implementation, backtesting, risk management |
| **v1.2.0** | Roadmap | Advanced Prefect workflows, analytics flows, data validation |
| **v1.3.0** | Roadmap | Microservices architecture, cloud deployment |

## 🏆 Acknowledgments

- **Alpaca Markets** for providing excellent trading APIs
- **FastAPI** team for the amazing web framework
- **Polygon.io** for historical market data
- **Prefect** team for workflow orchestration platform
- **Python Community** for the incredible ecosystem

---

<div align="center">

**Happy Trading! 📈**

Developed by [Nishant Nayar](https://github.com/nishantnayar)

[![GitHub](https://img.shields.io/badge/GitHub-nishantnayar-black?style=flat-square&logo=github)](https://github.com/nishantnayar)
[![Email](https://img.shields.io/badge/Email-nishant.nayar@hotmail.com-blue?style=flat-square&logo=mail)](mailto:nishant.nayar@hotmail.com)

</div>
