# Trading System

<div align="center">

![Trading System](https://img.shields.io/badge/Trading-System-blue?style=for-the-badge&logo=python)
![Python](https://img.shields.io/badge/Python-3.11+-green?style=flat-square&logo=python)
![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-red?style=flat-square&logo=fastapi)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-blue?style=flat-square&logo=postgresql)
![Redis](https://img.shields.io/badge/Redis-7+-red?style=flat-square&logo=redis)

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

## 🏗️ Architecture

This system uses a **microservices architecture** with **Prefect orchestration**, providing:

- **6 Microservices**: Data Ingestion, Strategy Engine, Execution, Risk Management, Analytics, and Notification
- **Modern Tech Stack**: Python + FastAPI + PostgreSQL + Redis + Polars
- **Professional Frontend**: HTMX + Plotly + Tailwind CSS
- **Workflow Orchestration**: Prefect for automated trading workflows
- **Comprehensive Monitoring**: Loguru logging with structured data

### Key Features

| Feature | Description |
|---------|-------------|
| 🚀 **Paper Trading** | Safe testing environment with Alpaca paper trading API |
| 📊 **Real-time Data** | Live market data ingestion and processing |
| 🧠 **Strategy Engine** | Plugin-based framework for custom trading strategies |
| ⚡ **Risk Management** | Built-in position sizing and risk controls |
| 📈 **Analytics** | Comprehensive performance tracking and reporting |
| 🔄 **Backtesting** | Historical strategy validation framework |
| 📱 **Web Dashboard** | Modern, responsive trading interface |
| 🔧 **Microservices** | Scalable, maintainable service architecture |

## 🚀 Quick Start

### Prerequisites

| Requirement | Version | Purpose |
|-------------|---------|---------|
| **Python** | 3.11+ | Core runtime |
| **Anaconda** | Latest | Package management |
| **PostgreSQL** | 15+ | Primary database |
| **Redis** | 7+ | Caching and messaging |
| **Alpaca API** | - | Trading and market data |

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
```

#### 3. Alpaca API Features Available

- **Real-time Portfolio Data** - Live account balance and P&L
- **Live Positions** - Current holdings with real-time P&L
- **Order Management** - View and cancel open orders
- **Market Status** - Real-time market open/closed status
- **Trading Interface** - Place new orders (coming soon)

#### 4. API Endpoints

The following API endpoints are available:

- `GET /api/alpaca/account` - Get account information
- `GET /api/alpaca/positions` - Get all positions
- `GET /api/alpaca/orders` - Get orders
- `GET /api/alpaca/clock` - Get market clock
- `POST /api/alpaca/positions/{symbol}/close` - Close a position
- `DELETE /api/alpaca/orders/{order_id}` - Cancel an order

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
- Test your credentials by accessing the dashboard at `http://localhost:8002/dashboard`

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

# Edit .env with your Alpaca API credentials
# Get your API keys from: https://app.alpaca.markets/paper/dashboard/overview
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
- **URL**: http://localhost:8000
- **Default Login**: admin/admin
- **API Docs**: http://localhost:8000/docs

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
│   └── web/                     # Web interface
├── tests/                       # Test suite
├── docs/                        # Documentation
├── deployment/                  # Setup & environment files
├── config/                      # Application configuration
├── tools/                       # Development tools
└── logs/                        # Log files
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
- **Real-time Data**: Live market data ingestion from Alpaca
- **Historical Data**: Efficient storage and processing with Polars
- **Technical Indicators**: Comprehensive technical analysis tools
- **Performance Metrics**: Detailed analytics and reporting

### 🔔 Monitoring & Alerts
- **Real-time Dashboard**: Live portfolio monitoring and control
- **Performance Tracking**: Strategy performance metrics and analytics
- **Risk Monitoring**: Continuous risk assessment and alerts
- **Email Notifications**: Critical event notifications and reports

### 🛠️ Development Features
- **Microservices Architecture**: Scalable, maintainable service design
- **Prefect Orchestration**: Automated workflow management
- **Modern Frontend**: HTMX + Plotly + Tailwind CSS interface
- **Comprehensive Logging**: Structured logging with Loguru
- **Code Quality**: Black, Flake8, mypy, and pre-commit hooks
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

1. **Start all services**:
   ```bash
   python deployment/scripts/start_services.py
   ```

2. **Access web dashboard**: http://localhost:8000

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
| 📋 **Logging** | Comprehensive logging design | [docs/development/logging.md](docs/development/logging.md) |
| 🧪 **Testing** | Testing strategy and guidelines | [docs/development/testing.md](docs/development/testing.md) |
| 📖 **User Documentation** | Complete user and developer docs | [MkDocs](https://nishantnayar.github.io/Trading-System/) |
| 🐛 **Issues** | Report bugs and request features | [GitHub Issues](https://github.com/nishantnayar/trading-system/issues) |
| 💬 **Discussions** | Community discussions and Q&A | [GitHub Discussions](https://github.com/nishantnayar/trading-system/discussions) |
| 📧 **Contact** | Direct contact for support | nishant.nayar@hotmail.com |

## 🔄 Version History

| Version | Status | Features |
|---------|--------|----------|
| **v1.0.0** | ✅ Released | Paper trading, basic strategies, web dashboard |
| **v1.1.0** | 🚧 Planned | Live trading, advanced risk management |
| **v1.2.0** | 📋 Roadmap | ML integration, multi-asset support |
| **v1.3.0** | 📋 Roadmap | Cloud deployment, mobile app |

## 🏆 Acknowledgments

- **Alpaca Markets** for providing excellent trading APIs
- **FastAPI** team for the amazing web framework
- **Prefect** for workflow orchestration
- **Polars** for high-performance data processing
- **Python Community** for the incredible ecosystem

---

<div align="center">

**Happy Trading! 📈**

Developed by [Nishant Nayar](https://github.com/nishantnayar)

[![GitHub](https://img.shields.io/badge/GitHub-nishantnayar-black?style=flat-square&logo=github)](https://github.com/nishantnayar)
[![Email](https://img.shields.io/badge/Email-nishant.nayar@hotmail.com-blue?style=flat-square&logo=mail)](mailto:nishant.nayar@hotmail.com)

</div>
