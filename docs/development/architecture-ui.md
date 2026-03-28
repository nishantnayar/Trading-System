# Trading System UI Architecture

> **Status**: ✅ Fully Implemented (v1.1.0)

## Design Philosophy

### Core Principles
1. **Trader-First Workflow**: Page order mirrors how a professional uses the system — Dashboard → Portfolio → Analysis → Screener → Pairs Trading → Backtest Review → Settings
2. **Real Data Only**: No hardcoded values, simulated data, or placeholder content anywhere in the UI. Every metric is sourced from the live Alpaca paper trading account or the PostgreSQL database.
3. **Consistent Design System**: All pages share the same paper/ink aesthetic — fonts, colors, chart styling, and component patterns are defined centrally in `css_config.py` and `styles.css`.
4. **Reactive Updates**: Streamlit's reactive framework provides live updates; each page fetches fresh data on load with `@st.cache_data(ttl=...)` for performance.

### Design System

| Token | Value | Usage |
|-------|-------|-------|
| `--color-ink` | `#1a1a1a` | Primary text, headings |
| `--color-paper` | `#FAFAF8` | Page background, sidebar background |
| `--color-paper-warm` | `#F5F4F0` | Hover states, table alternating rows |
| `--color-profit` | `#2A7A4B` | Positive P&L, market open |
| `--color-loss` | `#C0392B` | Negative P&L, market closed, errors |
| `--color-warn` | `#D97706` | Warnings, pre/post market |
| `--font-display` | Playfair Display | h1, h2 headings |
| `--font-body` | DM Sans | Body text, labels, UI controls |
| `--font-mono` | DM Mono | All prices, metrics, table values |

### Technology Stack
- **Backend**: FastAPI (Python) on port 8001
- **Frontend**: Streamlit multipage application on port 8501
- **Charts**: Plotly with transparent backgrounds (`template="none"`, `paper_bgcolor="rgba(0,0,0,0)"`)
- **Styling**: `styles.css` + CSS variables from `css_config.py`
- **Database**: PostgreSQL (strategy data, market data, backtests)
- **AI Integration**: Ollama LLM for natural language stock screening (optional)

---

## Page Architecture

Pages are numbered to enforce sidebar order. Streamlit strips numeric prefixes from the display name.

### Dashboard (Home) — `streamlit_app.py`
Always the first item in the sidebar. Provides the account-at-a-glance view:
- Time-aware greeting (Good morning/afternoon/evening, Nishant)
- Market clock banner (MARKET OPEN / MARKET CLOSED with next event time)
- 4-metric row: Portfolio Value, Today's P&L, Buying Power, Open Positions
- Positions table (symbol, side, qty, avg entry, current price, market value, unrealized P&L, today %)
- Open orders panel (last 8, with side color coding)
- Sidebar: equity, day P&L, buying power, cash, open position count

### 1. Portfolio — `pages/1_Portfolio.py`
Full account management view:
- Account summary: Equity, Cash, Buying Power, Long Market Value, Today's P&L
- Positions table with close-position buttons (single-click confirmation pattern)
- Allocation pie chart from live position market values
- Tabs: Open Orders (with cancel), Recent Trades, Place Order form

### 2. Analysis — `pages/2_Analysis.py`
Market analysis with database-sourced OHLC data:
- Symbol selection with session state persistence (`selected_symbol`)
- Timeframe selection (1D, 1W, 1M, 3M, 6M, 1Y) with persistence (`selected_timeframe`)
- Candlestick chart with volume subplot
- Technical indicators overlay: SMA, EMA, RSI, MACD, Bollinger Bands
- No simulated data fallback — requires the data ingestion pipeline to have run

### 3. Screener — `pages/3_Screener.py`
Stock screening with two modes:
- **AI mode**: Natural language queries via Ollama (`phi3` model)
- **Filter mode**: Sector, price range, volume, RSI, market cap filters
- Results table with technical indicators, sortable, CSV export
- Requires Ollama for AI mode; filter mode works standalone

### 4. Pairs Trading — `pages/4_Pairs_Trading.py`
Live strategy monitoring:
- Strategy status metrics (active/inactive, total pairs, active pairs, total P&L)
- Start / Stop / Emergency Stop controls
- Active pairs table with z-score color coding (red > 2.0σ, orange > 1.5σ)
- Z-score chart with entry/exit threshold lines and configurable history window
- Performance summary (Sharpe, max drawdown, win rate, average hold time)
- Per-pair details expander (hedge ratio, half-life, cointegration p-value, open trade, last signal)

### 5. Backtest Review — `pages/5_Backtest_Review.py`
Backtest execution and analysis:
- Pair selector with rank scores
- Run backtest in-process with pass/fail gates (Sharpe > 0.5, drawdown < 15%, win rate > 45%)
- Equity curve chart (Plotly, transparent background)
- Metrics table and trade log
- Run history comparison
- Stock Analysis expander: Risk Flags (7 checks), Fundamentals, Price Chart (normalised + z-score overlay), Correlation (rolling Pearson with stability verdict)

### 6. Settings — `pages/6_Settings.py`
System configuration — no fake data, no hardcoded values:
- **Connection Status**: Live checks of API server health, Alpaca account number, market open/closed
- **Analysis Preferences**: Default symbol and timeframe (written to session state for use by Analysis page)
- **System Info**: API base URL, session start time, Streamlit version, Python version

### 7. About — `pages/7_About.py`
Project and author information:
- Author bio (Nishant Nayar, VP – Lead Solution Analyst, Greater Chicago Area)
- Project features and technology stack
- Contact links (LinkedIn, GitHub, Medium, Portfolio)

---

## Backend API Architecture

The FastAPI backend (`src/web/main.py`) runs on port 8001. All routers are registered without a global prefix.

### Alpaca / Trading Endpoints (`src/web/api/alpaca_routes.py`)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/account` | Alpaca account info (equity, buying power, cash) |
| `GET` | `/positions` | All open positions |
| `GET` | `/orders` | Orders (filterable by status, limit) |
| `GET` | `/trades` | Recent trade history |
| `GET` | `/clock` | Market open/closed status with next open/close times |
| `POST` | `/positions/{symbol}/close` | Close a position |
| `DELETE` | `/orders/{order_id}` | Cancel an order |
| `POST` | `/orders` | Place a new order |

### Market Data Endpoints (`src/web/api/market_data.py`)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/market-data/stats` | Market data statistics |
| `GET` | `/api/market-data/symbols` | Available symbols |
| `GET` | `/api/market-data/data/{symbol}` | Historical OHLC data |
| `GET` | `/api/market-data/data/{symbol}/latest` | Latest data point |

### Pairs Trading Endpoints (`src/web/api/pairs_trading.py`)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/strategies/pairs/status` | Strategy status and aggregate metrics |
| `GET` | `/api/strategies/pairs/active` | Active pairs with live z-scores |
| `GET` | `/api/strategies/pairs/performance` | Sharpe, win rate, drawdown aggregates |
| `GET` | `/api/strategies/pairs/{pair_id}/history` | Spread/z-score time series |
| `GET` | `/api/strategies/pairs/{pair_id}/details` | Registry stats, open trade, last signal |
| `POST` | `/api/strategies/pairs/start` | Start strategy |
| `POST` | `/api/strategies/pairs/stop` | Stop strategy |
| `POST` | `/api/strategies/pairs/emergency-stop` | Emergency stop (closes all trades) |
| `POST` | `/api/strategies/pairs/backtest` | Trigger backtest engine |
| `GET` | `/api/strategies/pairs/backtest/history` | Past backtest run records |

See [API Reference](../api/index.md) for complete endpoint documentation.

---

**See Also**:
- [Stock Screener Architecture](stock-screener-architecture.md) — Detailed screener implementation
- [Architecture Overview](architecture-overview.md) — System overview
- [Services Architecture](architecture-services.md) — Backend services
- [Strategy Engine API](../api/strategy-engine.md) — Pairs trading and backtesting API reference
