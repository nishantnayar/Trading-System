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

**Access your Streamlit UI**: http://localhost:8501

---

## 📋 **What You'll Find Here**

### **Getting Started**
- [Getting Started Guide](getting-started.md) - Complete setup and configuration guide

### **User Guide**
- [Dashboard Overview](user-guide/dashboard.md) - Navigate the interface
- [Stock Screener](user-guide/stock-screener.md) - AI-powered stock screening
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
- [Stock Screener Architecture](development/stock-screener-architecture.md) - Screener technical documentation
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
    subgraph "Data Sources"
        Polygon["Polygon.io<br/>Historical Data"]
        Yahoo["Yahoo Finance<br/>Fundamentals"]
        AlpacaExt["Alpaca API<br/>Trading Data"]
    end
    
    subgraph "Data Ingestion"
        DataIngestion["Data Ingestion Service"]
    end
    
    subgraph "Core Services"
        Strategy["Strategy Engine<br/>v1.1.0"]
        Risk["Risk Management<br/>v1.1.0"]
        Execution["Execution Service<br/>v1.0.0"]
        Analytics["Analytics Service<br/>v1.0.0"]
    end
    
    subgraph "Storage"
        PostgreSQL[("PostgreSQL<br/>Data and Logs")]
        Redis[("Redis<br/>Cache")]
    end
    
    subgraph "Orchestration"
        Prefect["Prefect<br/>Workflows"]
    end
    
    subgraph "Frontend"
        Streamlit["Streamlit UI"]
        FastAPI["FastAPI API"]
    end
    
    Polygon --> DataIngestion
    Yahoo --> DataIngestion
    AlpacaExt --> DataIngestion
    
    DataIngestion --> PostgreSQL
    DataIngestion --> Redis
    DataIngestion --> Prefect
    
    DataIngestion --> Strategy
    Strategy --> Risk
    Risk --> Execution
    Execution --> Analytics
    
    Strategy --> PostgreSQL
    Risk --> PostgreSQL
    Execution --> PostgreSQL
    Analytics --> PostgreSQL
    
    Execution --> AlpacaExt
    Analytics --> Streamlit
    FastAPI --> Execution
    FastAPI --> Analytics
    
    Prefect --> DataIngestion
    Prefect --> Analytics
    
    style DataIngestion fill:#00A86B
    style Execution fill:#00A86B
    style Analytics fill:#00A86B
    style Strategy fill:#FFA500
    style Risk fill:#FFA500
```

</div>

### **Core Components**

| Component | Technology | Status | Purpose |
|-----------|------------|--------|---------|
| **Data Ingestion** | Python + pandas | ✅ v1.0.0 | Market data processing (Polygon.io, Yahoo Finance, Alpaca) |
| **Strategy Engine** | Python + Pydantic | 🚧 v1.1.0 | Algorithm execution (planned) |
| **Risk Management** | Python + PostgreSQL | 🚧 v1.1.0 | Risk controls (planned) |
| **Execution Engine** | Python + Alpaca API | ✅ v1.0.0 | Order management (account, positions, orders) |
| **Analytics** | Python + Plotly | ✅ v1.0.0 | Performance tracking and visualization |
| **AI Services** | Python + Ollama | ✅ v1.0.0 | Natural language processing for stock screener |
| **Database** | PostgreSQL | ✅ v1.0.0 | Data persistence |
| **Cache** | Redis | ✅ v1.0.0 | High-speed access (optional) |

---

## 🎯 **Key Features**

### **Trading Capabilities**
- ✅ **Paper Trading** - Start with Alpaca paper trading (v1.0.0)
- ✅ **Historical Data** - Polygon.io and Yahoo Finance integration for backtesting (v1.0.0)
- ✅ **AI-Powered Screener** - Natural language stock screening with Ollama LLM (v1.0.0)
- 🚧 **Strategy Backtesting** - Test before live deployment (v1.1.0)
- 🚧 **Risk Controls** - Built-in risk management (v1.1.0)
- ✅ **Performance Analytics** - Interactive charts and metrics with Plotly (v1.0.0)
- ✅ **Order Management** - Account, position, and order viewing/cancellation (v1.0.0)
- 🚧 **Order Placement** - Place new orders via UI (v1.1.0)

### **Technical Features**
- ✅ **Modular Architecture** - Service-oriented design ready for scaling
- ✅ **Type Safety** - Pydantic for data validation
- ✅ **Data Processing** - pandas for analytics and manipulation
- ✅ **Modern UI** - Streamlit + Plotly Charts + Custom CSS
- ✅ **Professional Charts** - Interactive financial visualizations with Plotly
- ✅ **AI Integration** - Local LLM support via Ollama for natural language queries
- ✅ **Session State** - Persistent data sharing across pages
- ✅ **Comprehensive Logging** - Database-first logging with PostgreSQL storage and file fallback
- ✅ **Database Design** - PostgreSQL with comprehensive schema
- ✅ **Data Quality** - Automated validation and monitoring
- ✅ **Timezone Support** - UTC storage with Central Time display

### **Development Features**
- ✅ **Code Quality** - Flake8, Black, isort, mypy
- ✅ **Documentation** - MkDocs
- ✅ **Testing** - Comprehensive test coverage
- ✅ **CI/CD** - Automated quality checks

---

## 📊 **Dashboard Preview**

Your Streamlit trading interface provides:

- **Portfolio Management** - Real-time portfolio tracking and performance metrics
- **Market Analysis** - Interactive charts with technical indicators using Plotly
- **Stock Screener** - AI-powered stock screening with natural language queries (Ollama integration)
- **System Information** - Team details and system architecture
- **Settings** - User preferences and session state management
- **Session State** - Persistent data sharing across all pages
- **Modern UI** - Clean, professional Streamlit interface
- **Timezone Support** - All data displayed in Central Time (stored in UTC)

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

# Ollama (Optional, for AI features)
OLLAMA_BASE_URL=http://localhost:11434

# Logging (Database-first with file fallback)
LOG_LEVEL=INFO
# Logs are stored in PostgreSQL logging schema by default
# See config/logging.yaml for detailed configuration
```

### **Service Ports**
- **Streamlit UI**: http://localhost:8501
- **API Docs**: http://localhost:8001/docs
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


