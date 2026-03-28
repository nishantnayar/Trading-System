# Streamlit UI Overview

This guide covers the Streamlit multipage trading dashboard. All data is sourced live from the Alpaca paper trading API and the PostgreSQL database — no simulated or placeholder values.

## Prerequisites

- FastAPI backend running on port 8001: `python -m src.web.main`
- Streamlit running on port 8501: `python streamlit_ui/run_streamlit.py`

## Navigation

The sidebar lists all pages in workflow order. Streamlit's automatic navigation uses the filename numeric prefix to control ordering.

```
Trading System
├── Dashboard          ← streamlit_app.py (home)
├── Portfolio          ← pages/1_Portfolio.py
├── Analysis           ← pages/2_Analysis.py
├── Screener           ← pages/3_Screener.py
├── Pairs Trading      ← pages/4_Pairs_Trading.py
├── Backtest Review    ← pages/5_Backtest_Review.py
├── Settings           ← pages/6_Settings.py
└── About              ← pages/7_About.py
```

---

## Dashboard (Home)

The home page provides an account-at-a-glance view on every load.

- **Greeting**: Time-aware (Good morning / Good afternoon / Good evening)
- **Market Clock Banner**: MARKET OPEN (green) or MARKET CLOSED (red) with the next open/close time
- **Account Metrics**: Portfolio Value, Today's P&L (with % delta), Buying Power, Open Positions
- **Positions Table**: Symbol, Side, Qty, Avg Entry, Current Price, Market Value, Unrealized P&L, Today %
- **Open Orders Panel**: Up to 8 open orders with side color coding (green = BUY, red = SELL)
- **Sidebar**: Equity, day P&L, buying power, cash, open position count

---

## Portfolio

Full account management — the primary page for day-to-day trading operations.

- **Account Summary**: Equity, Cash, Buying Power, Long Market Value, Today's P&L
- **Positions**: Table with close-position controls (requires one confirmation click)
- **Allocation Chart**: Pie chart of position market values (Plotly)
- **Open Orders tab**: List with cancel controls
- **Recent Trades tab**: Trade history from Alpaca
- **Place Order tab**: Market/limit order form with side, quantity, and optional limit price

---

## Analysis

Market analysis using OHLC data stored in the PostgreSQL database by the data ingestion pipeline.

- **Symbol Selection**: Dropdown from available symbols; selection persists to session state
- **Timeframe**: 1D, 1W, 1M, 3M, 6M, 1Y; selection persists to session state
- **Candlestick Chart**: OHLC bars with volume subplot
- **Technical Indicators**: SMA (20, 50, 200), EMA (12, 26), RSI (14), MACD, Bollinger Bands (20, 2σ)

> **Note**: The Analysis page requires the data ingestion pipeline to have populated market data for the selected symbol. If no data is available, a warning is displayed rather than showing simulated data.

---

## Screener

Stock screening with two operating modes:

**AI Mode** (requires Ollama with `phi3` model):
- Enter natural language queries: *"Find semiconductor stocks with RSI below 40"*
- Results returned with AI interpretation

**Filter Mode** (no dependencies):
- Sector, price range, volume threshold, RSI range, market cap filters
- Results table with technical indicators, sortable columns, CSV export

---

## Pairs Trading

Live monitoring for the statistical arbitrage strategy.

- **Status Bar**: Strategy active/inactive, total pairs, active pairs, aggregate P&L, last update time
- **Controls**: Start Strategy, Stop Strategy, Emergency Stop (two-click confirmation)
- **Active Pairs Table**: Z-score color coded — red (|z| > 2.0σ), orange (|z| > 1.5σ), normal otherwise
- **Z-Score Chart**: Historical spread z-score with entry/exit threshold lines; adjustable history window (7–90 days)
- **Performance Summary**: Sharpe ratio, max drawdown, win rate, average hold time
- **Pair Details**: Expandable panel — hedge ratio, half-life, cointegration p-value, open trade, last signal

The strategy executes two-legged trades on Alpaca (paper account). The Prefect flow runs on schedule `0 14-21 * * 1-5` UTC (9 AM–5 PM ET, Mon–Fri).

---

## Backtest Review

Historical validation of pairs trading configurations before live execution.

- **Pair Selector**: Choose pair with rank score indicator
- **Run Backtest**: Executes in-process against database data (fills at next-bar open to avoid look-ahead bias)
- **Pass/Fail Gates**: Sharpe > 0.5, max drawdown < 15%, win rate > 45%
- **Equity Curve**: Portfolio value over backtest period
- **Metrics**: Sharpe, max drawdown, win rate, profit factor, Kelly fraction
- **Trade Log**: Individual trade entries and exits
- **Run History**: Compare results across multiple backtest runs
- **Stock Analysis** (expandable):
  - *Risk Flags*: 7 automated checks
  - *Fundamentals*: Company cards and key statistics
  - *Price Chart*: Normalised price with z-score overlay and dividend/split markers
  - *Correlation*: Rolling 30-bar Pearson correlation with stability verdict

---

## Settings

System configuration and connection verification. Contains no hardcoded values.

**Connection Status**
- API server health (green/red badge)
- Alpaca account number and paper/live mode
- Market open/closed status

**Analysis Preferences**
- Default symbol (written to `st.session_state.selected_symbol`)
- Default timeframe (written to `st.session_state.selected_timeframe`)
- These values pre-populate the Analysis page on next visit

**System Info**
- API base URL (from `API_BASE_URL` environment variable or `http://localhost:8001`)
- Session start time
- Streamlit and Python versions

---

## About

System overview and author information:
- Author: Nishant Nayar, VP – Lead Solution Analyst, Greater Chicago Area
- Project features and technology stack
- Contact: LinkedIn, GitHub, Medium, Portfolio (nishantnayar.vercel.app)

---

## Session State

| Variable | Set By | Used By | Purpose |
|----------|--------|---------|---------|
| `selected_symbol` | Settings, Analysis | Analysis | Default symbol on page load |
| `selected_timeframe` | Settings, Analysis | Analysis | Default timeframe on page load |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| "Could not load account data" on Dashboard | FastAPI not running | `python -m src.web.main` |
| No symbols in Analysis dropdown | Data ingestion has not run | Run Yahoo Finance Prefect flow |
| Screener AI mode fails | Ollama not running | `ollama serve` and `ollama pull phi3` |
| Pairs Trading shows no active pairs | Pairs not registered | Run `scripts/discover_pairs.py` |
| Stale account data after API key change | Module singleton cached | Restart FastAPI server completely |
