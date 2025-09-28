# Trading System

A production-grade algorithmic trading system designed for local deployment, focusing on equities trading through Alpaca with paper trading capabilities.

## 🏗️ Architecture

This system uses a **microservices architecture** with **Prefect orchestration**, providing:

- **6 Microservices**: Data Ingestion, Strategy Engine, Execution, Risk Management, Analytics, and Notification
- **Modern Tech Stack**: Python + FastAPI + PostgreSQL + Redis + Polars
- **Professional Frontend**: HTMX + Plotly + Tailwind CSS
- **Workflow Orchestration**: Prefect for automated trading workflows
- **Comprehensive Monitoring**: Loguru logging with structured data

## 🚀 Quick Start

### Prerequisites

- **Python 3.11+**
- **Anaconda** (recommended)
- **PostgreSQL 15+**
- **Redis 7+**
- **Alpaca API Account** (paper trading)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/nishantnayar/trading-system.git
   cd trading-system
   ```

2. **Create conda environment**
   ```bash
   conda env create -f deployment/environment.yml
   conda activate trading-system
   ```

3. **Install additional dependencies**
   ```bash
   pip install -r deployment/requirements.txt
   ```

4. **Setup environment variables**
   ```bash
   cp deployment/env.example .env
   # Edit .env with your actual values
   ```

5. **Initialize database**
   ```bash
   python deployment/scripts/setup_database.py
   ```

6. **Start services**
   ```bash
   python deployment/scripts/start_services.py
   ```

7. **Access the dashboard**
   - Open http://localhost:8000 in your browser
   - Default login: admin/admin

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

### Trading Capabilities
- **Paper Trading**: Safe testing environment
- **Live Trading**: Production-ready execution
- **Multiple Strategies**: Plugin-based strategy framework
- **Risk Management**: Built-in position sizing and limits
- **Backtesting**: Historical strategy validation

### Data Processing
- **Real-time Data**: Alpaca market data integration
- **Historical Data**: Efficient storage with Polars
- **Technical Indicators**: Comprehensive analysis tools
- **Performance Metrics**: Detailed analytics and reporting

### Monitoring & Alerts
- **Real-time Dashboard**: Live portfolio monitoring
- **Performance Tracking**: Strategy performance metrics
- **Risk Monitoring**: Continuous risk assessment
- **Email Alerts**: Critical event notifications

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

- **Documentation**: [ARCHITECTURE.md](ARCHITECTURE.md)
- **Issues**: [GitHub Issues](https://github.com/yourusername/trading-system/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/trading-system/discussions)

## 🔄 Version History

- **v1.0.0** - Initial release with paper trading support
- **v1.1.0** - Live trading capabilities (planned)
- **v1.2.0** - Advanced analytics and ML integration (planned)

---

**Happy Trading! 📈**
