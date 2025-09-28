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
# Create conda environment
conda env create -f deployment/environment.yml
conda activate trading-system

# Install additional dependencies
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

The project uses modern Python development tools:

- **Black** - Code formatting
- **Flake8** - Linting
- **isort** - Import sorting
- **mypy** - Type checking
- **pre-commit** - Git hooks

Setup development environment:
```bash
# Install pre-commit hooks
pre-commit install

# Format code
black src/ tests/

# Sort imports
isort src/ tests/

# Lint code
flake8 src/ tests/

# Type check
mypy src/
```

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

# Technical documentation (Sphinx)
cd docs/sphinx
sphinx-build -b html . _build/html
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
| 📋 **Logging Architecture** | Comprehensive logging design | [LOGGING_ARCHITECTURE.md](docs/LOGGING_ARCHITECTURE.md) |
| 📖 **Documentation** | Complete user and developer docs | [MkDocs](https://nishantnayar.github.io/trading-system) |
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

Made with ❤️ by [Nishant Nayar](https://github.com/nishantnayar)

[![GitHub](https://img.shields.io/badge/GitHub-nishantnayar-black?style=flat-square&logo=github)](https://github.com/nishantnayar)
[![Email](https://img.shields.io/badge/Email-nishant.nayar@hotmail.com-blue?style=flat-square&logo=mail)](mailto:nishant.nayar@hotmail.com)

</div>
