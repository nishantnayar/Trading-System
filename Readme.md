<div align="center">

# Trading System

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15+-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Redis](https://img.shields.io/badge/Redis-7+-DC382D?style=for-the-badge&logo=redis&logoColor=white)](https://redis.io)
[![Prefect](https://img.shields.io/badge/Prefect-3.4+-1D4ED8?style=for-the-badge&logo=prefect&logoColor=white)](https://prefect.io)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.52+-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=flat-square)](https://opensource.org/licenses/MIT)
[![CI/CD Pipeline](https://github.com/nishantnayar/trading-system/workflows/Continuous%20Integration/badge.svg)](https://github.com/nishantnayar/trading-system/actions)
[![Documentation](https://img.shields.io/badge/Docs-MkDocs-blue.svg?style=flat-square)](https://nishantnayar.github.io/trading-system)

**Production-grade algorithmic pairs trading platform for equities.**  
Paper trading via Alpaca. Statistical arbitrage with cointegration-based pair discovery, Kelly criterion sizing, and Gartley harmonic pattern detection.

[Features](#features) - [Architecture](#architecture) - [Quick Start](#quick-start) - [UI Pages](#ui-pages) - [API](#api-endpoints) - [Roadmap](#roadmap)

</div>

---

## Overview

A modular algorithmic trading system built around **statistical pairs trading** and **harmonic pattern detection**. The system ingests market data from Yahoo Finance, stores it in PostgreSQL, runs strategy logic through Prefect-orchestrated workflows, and surfaces everything through a Streamlit dashboard and FastAPI backend.

All trading runs in **paper mode** via Alpaca Markets. No real capital is at risk.

---

## Features

### Trading & Strategy

| Feature | Description |
|---------|-------------|
| **Pairs Trading** | Cointegration-based pair discovery, log-spread z-score signals, two-legged Alpaca execution |
| **Signal Generation** | LONG_SPREAD / SHORT_SPREAD / EXIT / STOP_LOSS / EXPIRE with max hold-period enforcement |
| **Position Sizing** | Kelly criterion - bootstrap 2% fixed (first 20 trades), then Half-Kelly; hard 10% cap per leg |
| **Gartley Patterns** | Harmonic pattern detection for entry timing across individual equities |
| **Backtesting Engine** | Look-ahead-bias-free replay; Sharpe, max drawdown, win rate, profit factor metrics |
| **Slippage Modeling** | Configurable bps slippage + commission per trade applied to all backtest fills |
| **Risk Controls** | Portfolio drawdown circuit breaker, cross-pair correlation guard, per-pair allocation caps |
| **Paper Trading** | Full Alpaca paper account integration - account, positions, orders, trade history |

### Data & Analytics

| Feature | Description |
|---------|-------------|
| **Yahoo Finance** | Primary data source - EOD adjusted bars, intraday 1h bars, fundamentals, financials, ESG |
| **10 Data Types** | Market data, company info, key stats, dividends, splits, institutional holders, financials, officers, analyst recommendations, ESG |
| **Technical Indicators** | SMA, EMA, RSI, MACD, Bollinger Bands pre-calculated and stored in PostgreSQL |
| **Automated Ingestion** | Prefect flows for daily market data, weekly company data, and intraday price refresh |
| **Data Quality** | Completeness checks, gap detection, automated validation |
| **Redis Caching** | Debug metadata per cycle (bar counts, z-scores, signals) with 48h TTL; no-op if Redis is down |

### Platform

| Feature | Description |
|---------|-------------|
| **Streamlit Dashboard** | 7-page professional web UI with paper/ink design system |
| **FastAPI Backend** | 60+ REST endpoints across trading, analytics, strategy, and market data |
| **AI Stock Screener** | Natural language queries via local Ollama LLM with multi-turn chat |
| **Prefect Orchestration** | 8 scheduled flows for data, analytics, strategy, and database maintenance |
| **Database Logging** | Queryable structured logs stored in PostgreSQL via Loguru |
| **Email Notifications** | Trade opened/closed, stop-loss, flow errors - ASCII subject lines, no-op when unconfigured |

---

## Architecture

```
                      +------------------+
                      |   Streamlit UI   |   localhost:8501
                      |   (7 pages)      |
                      +--------+---------+
                               |
                      +--------v---------+
                      |   FastAPI API    |   localhost:8001
                      |   (60+ routes)   |
                      +--------+---------+
                               |
           +-------------------+-------------------+
           |                   |                   |
  +--------v--------+ +--------v--------+ +--------v--------+
  | Strategy Engine | | Data Ingestion  | | Risk Management |
  | Pairs / Gartley | | Yahoo Finance   | | Circuit Breaker |
  +--------+--------+ +--------+--------+ +--------+--------+
           |                   |                   |
           +-------------------+-------------------+
                               |
                      +--------v---------+
                      |   PostgreSQL     |   Primary store
                      |   + Redis        |   Debug cache
                      +------------------+
                               |
                      +--------v---------+
                      |   Prefect        |   Workflow orchestration
                      |   (8 flows)      |   localhost:4200
                      +------------------+
                               |
                      +--------v---------+
                      |   Alpaca API     |   Order execution only
                      |   (paper mode)   |
                      +------------------+
```

> **Data flow**: Yahoo Finance -> PostgreSQL -> Strategy Engine -> Alpaca (orders only)
> Alpaca is **not** used for price data. All price data comes from Yahoo Finance.

### Technology Stack

| Layer | Technology | Notes |
|-------|-----------|-------|
| Language | Python 3.11+ | Full type annotations, mypy-clean |
| API | FastAPI 0.100+ | Async, OpenAPI docs at `/docs` |
| Database | PostgreSQL 15+ | Primary store; `data_ingestion`, `analytics`, `strategy_engine` schemas |
| Cache | Redis 7+ | Optional; graceful no-op when unavailable |
| Orchestration | Prefect 3.4+ | Optional; 8 flows, separate `prefect` DB |
| Frontend | Streamlit 1.52+ | Paper/ink design, Playfair Display / DM Sans / DM Mono |
| Visualization | Plotly | Candlestick, equity curves, z-score overlays |
| Data | pandas 2.0+, NumPy | All market data processing |
| Market Data | yfinance 0.2.40+ | Yahoo Finance (primary); Polygon.io (supplemental) |
| Execution | alpaca-trade-api | Orders and account only |
| Indicators | pandas-ta-classic | SMA, EMA, RSI, MACD, BB |
| AI | Ollama | Local LLM for stock screener (optional) |
| Statistics | statsmodels, scipy | Cointegration, OLS, half-life |

---

## Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL 15+
- Git

Optional: Redis 7+, Prefect 3.4+, Ollama (for AI screener)

### 1. Clone and Install

```bash
git clone https://github.com/nishantnayar/trading-system.git
cd trading-system
pip install -r requirements.txt
```

### 2. Configure Environment

Create `.env` in the project root:

```bash
# --- Alpaca (Paper Trading) ---
ALPACA_API_KEY=your_api_key
ALPACA_SECRET_KEY=your_secret_key
ALPACA_BASE_URL=https://paper-api.alpaca.markets
ALPACA_DATA_URL=https://data.alpaca.markets
IS_PAPER_TRADING=True

# --- Database ---
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password
TRADING_DB_NAME=trading_system

# --- Redis (optional) ---
REDIS_URL=redis://localhost:6379/0

# --- App ---
DEBUG=false
LOG_LEVEL=INFO

# --- Prefect (optional) ---
PREFECT_API_URL=http://localhost:4200/api
PREFECT_API_DATABASE_CONNECTION_URL=postgresql+asyncpg://postgres:password@localhost:5432/prefect
PREFECT_WORK_POOL_NAME=default-agent-pool

# --- Email Notifications (optional) ---
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
NOTIFICATION_FROM=your_email@gmail.com
NOTIFICATION_TO=your_email@gmail.com

# --- Ollama AI Screener (optional) ---
OLLAMA_BASE_URL=http://localhost:11434
```

> Get a free Alpaca paper trading account at [alpaca.markets](https://alpaca.markets).

### 3. Initialize Database

```bash
python scripts/setup_databases.py

# Verify connections
python scripts/test_database_connections.py
```

### 4. Start the Application

```bash
# Start both FastAPI and Streamlit together
python main.py
```

Or start them separately:

```bash
# Terminal 1 - API server
python -m src.web.main

# Terminal 2 - Streamlit dashboard
streamlit run streamlit_ui/streamlit_app.py
```

### 5. Access the Interfaces

| Interface | URL | Description |
|-----------|-----|-------------|
| Streamlit Dashboard | http://localhost:8501 | Main trading UI |
| API Documentation | http://localhost:8001/docs | Swagger / OpenAPI |
| Prefect UI | http://localhost:4200 | Workflow monitoring |

---

## UI Pages

The Streamlit dashboard is organized into 7 pages matching the trader workflow:

| Page | Description |
|------|-------------|
| **1 - Portfolio** | Account balance, buying power, open positions, order history, place market/limit orders |
| **2 - Analysis** | Candlestick charts, technical indicators (SMA, EMA, RSI, MACD, BB), symbol lookup |
| **3 - Screener** | AI-powered natural language screener + traditional filters (MACD, BB, SMA crossover, RSI, volatility) with multi-turn chat |
| **4 - Strategy Monitor** | Live pairs trading status, z-score chart, active pair details, basket strategy monitoring |
| **5 - P&L Report** | Closed trade P&L, per-pair breakdown, cumulative equity chart |
| **6 - Pair Lab** | Pair Scanner (backtest all pairs, rank by Sharpe) + Backtest tab (run individual backtests, equity curve, trade log) |
| **7 - Ops** | System connections status, data quality checks, scanner/analysis preferences |

---

## Workflow Orchestration

Prefect 3.4+ manages all scheduled work. Flows run automatically once deployed.

### Scheduled Flows

| Flow | Schedule (UTC) | Purpose |
|------|---------------|---------|
| Daily Market Data | 22:15 Mon-Fri | Fetch Yahoo Finance hourly bars, trigger indicator sub-flow |
| Weekly Company Info | Fri 23:00 | Company metadata, officer info |
| Weekly Company Data | Sat 01:30 | Combined company info + key statistics |
| Weekly Pair Discovery | Sat 03:30 | Cointegration scan, update `pair_registry` |
| Weekly Database Backup | Sat 05:00 | pg_dump `data_ingestion` + `analytics` to `backups/` |
| Intraday Pairs Trading | 14:00-21:00 hourly Mon-Fri | Refresh prices, run strategy cycle, execute signals |

### Prefect Setup

```bash
# Start Prefect server
prefect server start

# Deploy Yahoo Finance flows
python src/shared/prefect/flows/data_ingestion/yahoo_flows.py

# Deploy pairs trading flow
python src/shared/prefect/flows/strategy_engine/pairs_flow.py --deploy

# Start worker (separate terminal)
prefect worker start --pool default-agent-pool
```

See [Prefect Deployment](docs/development/prefect-deployment.md) and [Operations Runbook](docs/development/prefect-deployment-operations.md) for full details.

---

## Pairs Trading

The pairs trading strategy uses statistical arbitrage on cointegrated equity pairs.

### How It Works

1. **Pair Discovery** - Weekly scan uses Engle-Granger cointegration test, Pearson correlation, and OLS hedge ratio to rank candidate pairs by `rank_score = (1 - coint_pvalue) x |correlation| x z_score_abs_mean`
2. **Signal Generation** - Hourly intraday cycle computes log-spread z-score; signals fire at entry threshold (default 2.0 sigma), exit at 0.5 sigma, stop-loss at 3.0 sigma
3. **Position Sizing** - Kelly criterion bootstrap (2% fixed) for first 20 trades, then Half-Kelly; hard 10% cap per leg; 5% max allocation per pair
4. **Execution** - Two-legged Alpaca paper orders (long one leg, short the other)

### Active Pairs (as of 2026-04-01)

| Pair | Sector | Hedge Ratio | Allocation Cap |
|------|--------|-------------|---------------|
| EWBC / FNB | Banking | - | 5% per leg |
| COLB / FNB | Banking | - | 5% per leg |

> FNB appears in both pairs - a deliberate concentration to monitor. Do not activate additional FNB pairs without reducing caps.

### Backtest Parameters

```
Entry threshold:  2.0 sigma
Exit threshold:   0.5 sigma
Stop-loss:        3.0 sigma
Max hold period:  3x half-life (hours)
Z-score window:   capped at 60 bars
Default lookback: 180 days
Slippage:         5 bps (configurable)
```

### Pass/Fail Gate

Backtests must clear all three gates before a pair is activated:

| Metric | Threshold |
|--------|-----------|
| Sharpe Ratio | > 0.5 |
| Max Drawdown | < 15% |
| Win Rate | > 45% |

---

## API Endpoints

### Trading & Account

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/account` | Alpaca account info, buying power, portfolio value |
| `GET` | `/positions` | Open positions with unrealized P&L |
| `GET` | `/orders` | Orders (filterable by status) |
| `GET` | `/trades` | Closed trade history |
| `GET` | `/clock` | Market open/closed status |
| `POST` | `/orders` | Place market or limit order |
| `POST` | `/positions/{symbol}/close` | Close a position |
| `DELETE` | `/orders/{order_id}` | Cancel an order |

### Pairs Strategy

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/strategies/pairs/status` | Active pair count, total P&L |
| `GET` | `/api/strategies/pairs/active` | Live pair list with z-scores |
| `GET` | `/api/strategies/pairs/performance` | Sharpe, win rate, drawdown aggregate |
| `GET` | `/api/strategies/pairs/{pair_id}/details` | Registry stats + open trade + last signal |
| `GET` | `/api/strategies/pairs/{pair_id}/history` | Spread time-series |
| `POST` | `/api/strategies/pairs/backtest` | Run backtest, return results |
| `GET` | `/api/strategies/pairs/backtest/history` | Past backtest runs |
| `POST` | `/api/strategies/pairs/{pair_id}/close` | Manually close open trade |
| `GET` | `/api/strategies/pairs/risk` | Circuit breaker state and thresholds |

### Market Data

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/market-data/symbols` | Available symbols |
| `GET` | `/api/market-data/data/{symbol}` | Historical OHLCV |
| `GET` | `/api/market-data/data/{symbol}/latest` | Latest data point |
| `GET` | `/api/market-data/data/{symbol}/ohlc` | OHLC summary |
| `GET` | `/api/market-data/stats` | Ingestion statistics |

Full API reference: http://localhost:8001/docs

---

## Project Structure

```
trading-system/
|-- main.py                          # Entry point (starts FastAPI + Streamlit)
|-- src/
|   |-- config/                      # Settings (all env vars), database config
|   |-- services/
|   |   |-- alpaca/                  # Alpaca client (execution only)
|   |   |-- analytics/               # Indicator calculator, service, storage
|   |   |-- data_ingestion/          # Historical loader, symbol management
|   |   |-- notification/            # Email notifier (no-op when unconfigured)
|   |   |-- polygon/                 # Polygon.io client (supplemental data)
|   |   |-- risk_management/         # Portfolio risk manager
|   |   |-- strategy_engine/
|   |   |   |-- backtesting/         # Engine, metrics, report
|   |   |   |-- baskets/             # Basket strategy
|   |   |   |-- harmonic/            # Gartley pattern detector + executor
|   |   |   `-- pairs/               # Signal generator, position sizer, executor, strategy
|   |   `-- yahoo/                   # Yahoo Finance client, loader, models
|   |-- shared/
|   |   |-- database/                # ORM models (16 tables), base, mixins
|   |   |-- logging/                 # Loguru config, DB sink, formatters
|   |   |-- prefect/
|   |   |   |-- flows/               # Data ingestion, analytics, strategy, maintenance flows
|   |   |   `-- tasks/               # Reusable Prefect tasks
|   |   |-- redis/                   # Redis client with set_json/get_json helpers
|   |   |-- utils/                   # Timezone utilities (UTC/Central)
|   |   `-- market_data.py           # get_price_series() - reads yahoo_adjusted_1h
|   `-- web/
|       |-- main.py                  # FastAPI app (register new routers here)
|       `-- api/                     # 60+ route files
|-- streamlit_ui/
|   |-- streamlit_app.py             # Dashboard home (market clock, account metrics)
|   |-- pages/
|   |   |-- 1_Portfolio.py
|   |   |-- 2_Analysis.py
|   |   |-- 3_Screener.py
|   |   |-- 4_Strategy_Monitor.py
|   |   |-- 5_PnL_Report.py
|   |   |-- 6_Pair_Lab.py
|   |   `-- 7_Ops.py
|   |-- api_client.py                # FastAPI wrapper for Streamlit pages
|   |-- css_config.py                # Design tokens (paper/ink theme)
|   `-- utils.py                     # Shared Streamlit helpers
|-- tests/
|   |-- unit/                        # No DB/network; mock everything
|   `-- integration/                 # Requires trading_system_test DB
|-- scripts/                         # Setup, backfill, backup, migration scripts
|-- docs/                            # MkDocs documentation (60+ pages)
|-- config/                          # scanner_prefs.json, analysis_prefs.json (gitignored)
`-- deployment/                      # Docker and deployment configurations
```

---

## Development

### Code Quality

All checks run automatically on every CI commit. Run locally before pushing:

```bash
# Check (CI mode)
black --check .
isort --check-only .
mypy src/ --ignore-missing-imports

# Auto-fix formatting
black . && isort .
```

### Testing

```bash
# Unit tests only (no DB required)
pytest -m "unit and trading" -v

# Full suite (requires trading_system_test DB)
python scripts/run_tests.py all

# With coverage
pytest --cov=src --cov-report=html
```

Test rules:
- Unit tests live in `tests/unit/`, integration tests in `tests/integration/`
- Never use real DB or network in unit tests - mock everything
- `asyncio_mode = auto` is set - do not add `@pytest.mark.asyncio` to individual methods
- Never test against a DB whose name does not end in `_test`

### Database Safety

- Test DB is `trading_system_test` (set via `TRADING_DB_NAME` env var)
- `conftest.py` enforces the `_test` suffix - do not bypass it
- Never drop tables if `market_data` has > 1000 rows (production guard)

---

## Data Source Architecture

**Alpaca is used for order execution only.** All price data comes from Yahoo Finance.

### `market_data.data_source` Values

| Value | Written by | Used by |
|-------|-----------|---------|
| `yahoo_adjusted` | Daily Prefect flow, backpopulate scripts | Backtesting, indicators, pair discovery |
| `yahoo_adjusted_1h` | `refresh_pair_prices_task` in `pairs_flow.py` | `get_price_series()` in strategy |
| `yahoo` | Daily Prefect flow | General market data |

### Intraday Price Flow

```
pairs_flow.py
    -> refresh_pair_prices_task()
        -> yfinance (interval='1h', 2 days)
            -> market_data (data_source='yahoo_adjusted_1h')
                -> get_price_series(symbol, limit)
                    -> strategy cycle
```

### Redis Debug Keys

```bash
# Check bar counts for a symbol
redis-cli get pairs:bars:EWBC

# Check last cycle result for a pair
redis-cli get pairs:cycle:EWBC_FNB
```

---

## Configuration

### Pairs Signal Thresholds

Configurable via `POST /api/strategies/pairs/config` or directly in the DB:

```
entry_threshold:  2.0 sigma  (default)
exit_threshold:   0.5 sigma
stop_threshold:   3.0 sigma
expire_hours:     3x half-life
z_score_window:   60 bars (capped)
```

### Backtesting Defaults

```
lookback_days:    180
slippage_bps:     5
commission:       $0.00
```

---

## Documentation

| Resource | Link |
|----------|------|
| Getting Started | [docs/getting-started.md](docs/getting-started.md) |
| Architecture | [ARCHITECTURE.md](ARCHITECTURE.md) |
| API Reference | [docs/api/](docs/api/) |
| Database Schema | [docs/development/database.md](docs/development/database.md) |
| Prefect Deployment | [docs/development/prefect-deployment.md](docs/development/prefect-deployment.md) |
| Data Sources | [docs/data-ingestion/data-sources.md](docs/data-ingestion/data-sources.md) |
| Testing Guide | [docs/development/testing.md](docs/development/testing.md) |
| Troubleshooting | [docs/troubleshooting.md](docs/troubleshooting.md) |
| Changelog | [CHANGELOG.md](CHANGELOG.md) |
| Contributing | [CONTRIBUTING.md](CONTRIBUTING.md) |

```bash
# Serve docs locally
mkdocs serve
```

---

## Roadmap

| Version | Status | Highlights |
|---------|--------|-----------|
| v1.0.0 | Released | Paper trading, Yahoo Finance ingestion, Streamlit dashboard, Prefect orchestration, technical indicators |
| v1.1.0 | Released 2026-03-28 | Pairs trading engine, backtesting, slippage modeling, professional UI redesign, order placement |
| v1.2.0 | In Progress | Gartley harmonic patterns, 7-page UI consolidation, AI screener multi-turn chat, persistent UI prefs |
| v1.3.0 | Planned | Risk management service, advanced analytics flows, data quality monitoring, email notifications |
| v2.0.0 | Future | Microservices, cloud deployment, distributed execution, multi-asset strategies |

---

## Security

- Never commit `.env` to version control
- All trading defaults to paper mode (`IS_PAPER_TRADING=True`)
- Use paper trading credentials for all development and testing
- Alpaca paper accounts use simulated virtual funds only

---

## Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Follow the code quality standards: `black . && isort . && mypy src/`
4. Add tests for new functionality
5. Open a Pull Request against `main`

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Risk Disclaimer

> **This software is for educational and research purposes only.**
> Trading involves substantial risk of loss. Past performance is not indicative of future results.
> The system defaults to paper trading with simulated funds. Use at your own risk.

---

<div align="center">

Developed by [Nishant Nayar](https://github.com/nishantnayar)

[![GitHub](https://img.shields.io/badge/GitHub-nishantnayar-181717?style=flat-square&logo=github)](https://github.com/nishantnayar)
[![Email](https://img.shields.io/badge/Email-nishant.nayar@hotmail.com-0078D4?style=flat-square&logo=microsoftoutlook)](mailto:nishant.nayar@hotmail.com)

*Built with FastAPI, Streamlit, PostgreSQL, Prefect, and Alpaca Markets*

</div>
