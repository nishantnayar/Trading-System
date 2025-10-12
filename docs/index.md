# Trading System Documentation



## **A Production-Grade Algorithmic Trading System**

*Built with Python, PostgreSQL, Redis, and Modern Web Technologies*

### **Technology Stack**

![Python](https://img.shields.io/badge/Python-3.11+-green?style=for-the-badge&logo=python)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue?style=for-the-badge&logo=postgresql)
![Redis](https://img.shields.io/badge/Redis-Cache-red?style=for-the-badge&logo=redis)
![FastAPI](https://img.shields.io/badge/FastAPI-Web%20Framework-009688?style=for-the-badge&logo=fastapi)
![pandas](https://img.shields.io/badge/pandas-Data%20Processing-150458?style=for-the-badge&logo=pandas)

---




---

## 🚀 **Quick Start**

Get your trading system up and running in minutes:

```bash
# Clone and setup
git clone https://github.com/nishantnayar/trading-system.git
cd trading-system

# Activate your existing conda environment
conda activate your-environment-name

# Install dependencies
pip install -r requirements.txt

# Configure and run
cp deployment/env.example .env
python scripts/setup_databases.py
python main.py
```

**Access your dashboard**: http://localhost:8002

---

## 📋 **What You'll Find Here**

### **Getting Started**
- [Getting Started Guide](getting-started.md) - Complete setup and configuration guide

### **User Guide**
- [Dashboard Overview](user-guide/dashboard.md) - Navigate the interface
- [Trading Operations](user-guide/trading.md) - Execute trades
- [Strategy Management](user-guide/strategies.md) - Create and manage strategies
- [Risk Management](user-guide/risk-management.md) - Control your exposure

### **API Reference**
- [Data Ingestion](api/data-ingestion.md) - Market data processing
- [Strategy Engine](api/strategy-engine.md) - Algorithm execution
- [Execution Engine](api/execution.md) - Order management
- [Risk Management](api/risk-management.md) - Risk controls
- [Analytics](api/analytics.md) - Performance metrics

### **Development**
- [System Architecture](development/architecture.md) - Complete system design
- [Database Architecture](development/database.md) - Database design and implementation
- [Database Setup](development/database.md) - Step-by-step database setup guide
- [Logging Architecture](development/logging.md) - Detailed logging strategy
- [Testing Strategy](development/testing.md) - Comprehensive testing approach
- [CI/CD Pipeline](development/ci-cd.md) - Continuous integration and deployment

---

## 🏗️ **System Architecture**

<div align="center">

```mermaid
graph TB
    A[Data Ingestion] --> B[Strategy Engine]
    B --> C[Risk Management]
    C --> D[Execution Engine]
    D --> E[Analytics]
    
    F[PostgreSQL] --> A
    F --> B
    F --> C
    F --> D
    F --> E
    
    G[Redis] --> A
    G --> B
    G --> C
    G --> D
    G --> E
    
```

</div>

### **Core Components**

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Data Ingestion** | Python + pandas | Market data processing |
| **Strategy Engine** | Python + Pydantic | Algorithm execution (v1.1.0) |
| **Risk Management** | Python + PostgreSQL | Risk controls (v1.1.0) |
| **Execution Engine** | Python + Alpaca API | Order management |
| **Analytics** | Python + Lightweight Charts | Performance tracking |
| **Database** | PostgreSQL | Data persistence |
| **Cache** | Redis | High-speed access |

---

## 🎯 **Key Features**

### **Trading Capabilities**
- ✅ **Paper Trading** - Start with Alpaca paper trading
- ✅ **Historical Data** - Polygon.io integration for backtesting
- ✅ **Strategy Backtesting** - Test before live deployment
- ✅ **Risk Controls** - Built-in risk management
- ✅ **Performance Analytics** - Interactive charts and metrics
- ✅ **Order Management** - Complete order lifecycle management

### **Technical Features**
- ✅ **Modular Architecture** - Service-oriented design ready for scaling
- ✅ **Type Safety** - Pydantic for data validation
- ✅ **Data Processing** - pandas for analytics and manipulation
- ✅ **Modern UI** - FastAPI + HTMX + Lightweight Charts + Tailwind CSS
- ✅ **Professional Charts** - Multi-pane trading charts with technical indicators
- ✅ **Theme Support** - Light/Dark chart themes with persistence
- ✅ **Comprehensive Logging** - Structured logging with Loguru
- ✅ **Database Design** - PostgreSQL with comprehensive schema
- ✅ **Data Quality** - Automated validation and monitoring

### **Development Features**
- ✅ **Code Quality** - Flake8, Black, isort, mypy
- ✅ **Documentation** - MkDocs
- ✅ **Testing** - Comprehensive test coverage
- ✅ **CI/CD** - Automated quality checks

---

## 📊 **Dashboard Preview**

Your trading dashboard provides:

- **Professional Trading Charts** - Multi-pane charts with candlesticks, volume, MACD, and RSI
- **Real-time Market Data** - Live price feeds and synchronized chart updates
- **Technical Analysis** - Professional-grade indicators with theme customization
- **Strategy Performance** - P&L tracking and analytics
- **Risk Metrics** - Position sizing and exposure
- **Order Management** - Trade execution and monitoring
- **System Health** - Service status and logs

---

## 🔧 **Configuration**

### **Environment Variables**
```bash
# Database
POSTGRES_URL=postgresql://user:pass@localhost:5432/trading
REDIS_URL=redis://localhost:6379/0

# Alpaca API
ALPACA_API_KEY=your_api_key
ALPACA_SECRET_KEY=your_secret_key
ALPACA_BASE_URL=https://paper-api.alpaca.markets

# Logging
LOG_LEVEL=INFO
LOG_RETENTION_DAYS=30
```

### **Service Ports**
- **Dashboard**: http://localhost:8002
- **API Docs**: http://localhost:8002/docs
- **PostgreSQL**: localhost:5432
- **Redis**: localhost:6379

---

## 🚨 **Important Notes**

### **Paper Trading First**
- Start with Alpaca paper trading
- Test your strategies thoroughly
- Understand risk management
- Only move to live trading when ready

### **Risk Management**
- Set appropriate position sizes
- Use stop-losses and take-profits
- Monitor your exposure
- Never risk more than you can afford to lose

### **Development**
- Follow the coding standards
- Write comprehensive tests
- Document your changes
- Use the logging system effectively

---

## 📞 **Support**

### **Documentation**
- [User Documentation](https://nishantnayar.github.io/trading-system) (MkDocs)
- [System Architecture](development/architecture.md)
- [Database Architecture](development/database.md)
- [Database Setup](development/database.md)
- [Logging Architecture](development/logging.md)
- [Testing Strategy](development/testing.md)
- [CI/CD Pipeline](development/ci-cd.md)
- [API Reference](api/data-ingestion.md)
- [Troubleshooting](troubleshooting.md)

### **Getting Help**
- Check the [Troubleshooting Guide](troubleshooting.md)
- Join the [Discussions](https://github.com/nishantnayar/trading-system/discussions)
- Create an issue on GitHub
- Contact: nishant.nayar@hotmail.com

---

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](https://github.com/nishantnayar/trading-system/blob/main/LICENSE) file for details.

---



**Built by [Nishant Nayar](https://github.com/nishantnayar)**

[![GitHub](https://img.shields.io/badge/GitHub-Repository-black?style=for-the-badge&logo=github)](https://github.com/nishantnayar/trading-system)
[![Documentation](https://img.shields.io/badge/Documentation-Online-blue?style=for-the-badge&logo=book)](https://nishantnayar.github.io/trading-system)
[![Issues](https://img.shields.io/badge/Issues-Report-green?style=for-the-badge&logo=github)](https://github.com/nishantnayar/trading-system/issues)


