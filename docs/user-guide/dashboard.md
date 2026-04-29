# Streamlit UI Overview

This guide covers the Streamlit multipage trading dashboard. All data is sourced live from the Alpaca paper trading API and the PostgreSQL database — no simulated or placeholder values.

## Prerequisites

- FastAPI backend running on port 8001: `python -m src.web.main`
- Streamlit running on port 8501: `python streamlit_ui/run_streamlit.py`

## Navigation

The sidebar lists all pages in workflow order. Streamlit's automatic navigation uses the filename numeric prefix to control ordering.

```
Trading System
├── Dashboard           ← streamlit_app.py (home)
├── Portfolio           ← pages/1_Portfolio.py
├── Analysis            ← pages/2_Analysis.py
├── Screener            ← pages/3_Screener.py
├── Strategy Monitor    ← pages/4_Strategy_Monitor.py  (Pairs + Baskets tabs)
├── P&L Report          ← pages/5_PnL_Report.py
├── Pair Lab            ← pages/6_Pair_Lab.py          (Scanner + Backtest tabs)
└── Ops                 ← pages/7_Ops.py               (Connections + Data Quality tabs)
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

## Strategy Monitor

Unified live view for all running strategies. Two tabs:

**Pairs tab**
- **Status Bar**: Strategy active/inactive, total pairs, active pairs, aggregate P&L, last update time
- **Controls**: Start Strategy, Stop Strategy, Emergency Stop (two-click confirmation)
- **Active Pairs Grid**: Z-score sparklines (last 48 bars), color coding — red (|z| > 2.0σ), orange (|z| > 1.5σ), unrealized P&L with delta vs. last load
- **Risk Controls**: Circuit breaker state, peak equity, drawdown threshold; reset and threshold update in place
- **Z-Score Chart**: Historical spread z-score with entry/exit threshold lines; adjustable window (7–90 days)
- **Performance Summary**: Sharpe ratio, max drawdown, win rate, average hold time

**Baskets tab**
- Active baskets with live z-score, sector, half-life, and activate/deactivate controls
- Spread + z-score dual-axis charts per basket
- Open trades with leg detail and unrealized P&L
- Last 50 closed/stopped trades with P&L and exit reason

The pairs strategy executes two-legged trades on Alpaca (paper account). Prefect flow: `0 14-21 * * 1-5` UTC.

---

## P&L Report

Realized performance across all pairs trades.

- **Summary KPIs**: Total P&L, win rate, profit factor, average hold duration
- **Equity Curve**: Cumulative realized equity over time
- **Daily P&L**: Bar chart showing day-by-day realized P&L
- **Monthly Heatmap**: Return by month for quick regime identification
- **Per-Pair Attribution**: Breakdown of P&L contribution by pair
- **Trade Log**: Full history of all closed trades

---

## Pair Lab

Scanner and backtest combined — two tabs for the full pair validation workflow.

**Scanner tab**
- Configure lookback days (90–365, default 180) and slippage (0–20 bps)
- Click **Run Scan** to backtest every registered pair in batch
- Results sorted: PASS first, then by Sharpe descending
- Failing gate metrics shown in red; inline Activate / Deactivate per row

**Backtest tab**
- Select a pair from the dropdown; configure thresholds, slippage, commission, initial capital in the sidebar
- **Stock Analysis** expander (always visible before running):
  - *Risk Flags*: 7 automated checks (market cap mismatch, liquidity imbalance, beta divergence, correlation decay, stock splits, upcoming ex-dividends, short interest)
  - *Fundamentals*: Company cards and side-by-side key statistics
  - *Price Chart*: Normalised price (base = 100) with spread z-score overlay and dividend/split markers
  - *Correlation*: Rolling 30-bar Pearson correlation with stability verdict
- Click **Run Backtest** for gate verdict, equity curve, full metrics, and trade log
- **Run History**: Compare results across all previous runs for this pair

Gate criteria (all must pass): Sharpe > 0.5, win rate > 45%, max drawdown < 15%

---

## Ops

System administration in two tabs. No hardcoded values anywhere.

**Connections & Preferences tab**
- **Connection Status**: Live badges for API server health, Alpaca account number and paper/live mode, market open/closed
- **Analysis Preferences**: Default symbol and timeframe — saved to `config/analysis_prefs.json` and written to session state to pre-fill the Analysis page
- **System Info**: API base URL, session start time, Streamlit and Python versions

**Data Quality tab**
- **Summary**: Tracked symbols, up-to-date count, stale count, last ingestion timestamp
- **Alerts**: Table of stale symbols sorted by days since last bar
- **All Ingestion Series**: Full table with freshness filter (All / Stale only / Fresh only)

---

## Session State

| Variable | Set By | Used By | Purpose |
|----------|--------|---------|---------|
| `selected_symbol` | Ops, Analysis | Analysis | Default symbol on page load |
| `selected_timeframe` | Ops, Analysis | Analysis | Default timeframe on page load |

---

## Troubleshooting

| Symptom | Likely Cause | Fix |
|---------|-------------|-----|
| "Could not load account data" on Dashboard | FastAPI not running | `python -m src.web.main` |
| No symbols in Analysis dropdown | Data ingestion has not run | Run Yahoo Finance Prefect flow |
| Screener AI mode fails | Ollama not running | `ollama serve` and `ollama pull phi3` |
| Strategy Monitor shows no active pairs | Pairs not registered | Run `scripts/discover_pairs.py` |
| Stale account data after API key change | Module singleton cached | Restart FastAPI server completely |
| Pair Lab Scanner returns no results | No market data for date range | Check data ingestion ran for the lookback period |
