# Changelog

All notable changes to the Trading System will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Screener — Advanced Traditional Filters**: MACD signal (bullish/bearish), Bollinger Band position range, SMA crossover (golden cross, death cross, price above/below SMA20), max volatility, and sort-by dropdown in the Traditional Filters tab
- **Screener — Signal Badge column**: `_compute_signal()` derives Oversold / Overbought / Bullish / Bearish / Neutral badge for each result row with colour-coded AgGrid styling
- **Screener — Multi-turn AI Chat**: After screening, an expandable "Ask a follow-up question" panel allows conversational queries about the results using `LLMService.chat_about_results()` (last 6 turns of history trimmed to avoid context bloat)
- **LLM Service — `chat_about_results()`**: New method for context-aware follow-up questions using conversation history; `@st.cache_resource` replaces deprecated `@st.cache`
- **LLM Service — `_fix_comparison_direction()`**: Post-parse regex correction that enforces correct `rsi_min`/`rsi_max` and `min_price`/`max_price` mapping when the model swaps comparison direction
- **LLM Service — `_fallback_parse()`**: Regex-based fallback parser for responses where the model returns malformed JSON despite `format="json"`
- **LLM Service — keyword hallucination filter**: Keywords not present in the original query text are stripped from parsed criteria before screening
- **LLM Service — `sort_by` support**: `interpret_screening_query()` now returns a `sort_by` field (`rsi_desc`, `rsi_asc`, `price_change_desc`, `price_change_asc`, `market_cap_desc`, `price_desc`) which drives automatic result sorting + top-10 truncation for LLM-driven searches
- **Screener — sector alias expansion** (`SECTOR_VARIATIONS`): Common synonyms (e.g. "finance"/"banking" → "Financial Services") resolved in both the AI and traditional filter paths
- **Market Data API — `_safe_float()`**: All OHLC float conversions now reject `NaN` and `Inf` values (returns `None`) to prevent JSON serialization errors for corrupt data points

### Planned
- Risk management service
- Advanced analytics and reporting
- Additional pairs beyond QRVO/SWKS

## [1.1.0] - 2026-03-28

### Added
- ✅ **Pairs Trading Strategy Engine** — full statistical arbitrage pipeline:
  - `scripts/discover_pairs.py` — automated pair discovery via Engle-Granger cointegration, Pearson correlation, OLS hedge ratio, and half-life calculation. Auto-upserts top pairs into `pair_registry` DB with `rank_score` composite metric.
  - `src/services/strategy_engine/pairs/spread_calculator.py` — log-spread z-score computation with configurable rolling window
  - `src/services/strategy_engine/pairs/signal_generator.py` — LONG_SPREAD / SHORT_SPREAD / EXIT / STOP_LOSS / EXPIRE signals with max hold-period enforcement
  - `src/services/strategy_engine/pairs/position_sizer.py` — Kelly criterion position sizing (bootstrap: 2% fixed for first 20 trades; full Half-Kelly thereafter)
  - `src/services/strategy_engine/pairs/pair_executor.py` — two-legged Alpaca order execution (open, close, emergency stop)
  - `src/services/strategy_engine/pairs/strategy.py` — `PairsStrategy` orchestrator tying all components together
- ✅ **Backtesting Engine**:
  - `src/services/strategy_engine/backtesting/engine.py` — in-memory historical replay on DB data, fills at next-bar open to avoid look-ahead bias
  - `src/services/strategy_engine/backtesting/metrics.py` — Sharpe, max drawdown, win rate, profit factor, Kelly fraction
  - `src/services/strategy_engine/backtesting/report.py` — saves run to `backtest_run` table with full equity curve + trade log as JSONB
- ✅ **Backtest Review Streamlit UI** (`streamlit_ui/pages/Backtest_Review.py`):
  - Pair selector with rank score labels, activate/deactivate toggle
  - Run backtest in-process with pass/fail gate (Sharpe > 0.5, drawdown < 15%, win rate > 45%)
  - Equity curve chart, metrics table, trade log, run history comparison
  - **Stock Analysis** expander with 4 tabs: Risk Flags (7 checks), Fundamentals (company cards + key stats), Price Chart (normalised + z-score overlay + dividend/split markers), Correlation (rolling 30-bar Pearson with stability verdict)
- ✅ **Intraday Pairs Trading Prefect Flow** (`src/shared/prefect/flows/strategy_engine/pairs_flow.py`):
  - Scheduled `0 14-21 * * 1-5` UTC (9 AM–5 PM ET Mon–Fri)
  - Market open check via Alpaca clock, `skip_market_check` flag for testing
  - Deploy via `python pairs_flow.py --deploy` (Prefect 3.x `from_source().deploy()` pattern)
- ✅ **Pairs Trading FastAPI Endpoints** (`src/web/api/pairs_trading.py`) — replaced all fake/random data with real DB queries:
  - `GET /api/strategies/pairs/status` — active pair count, total P&L
  - `GET /api/strategies/pairs/active` — live pair list with z-scores and open trade state
  - `GET /api/strategies/pairs/performance` — aggregated Sharpe, win rate, drawdown
  - `GET /api/strategies/pairs/{pair_id}/history` — `pair_spread` time-series
  - `GET /api/strategies/pairs/{pair_id}/details` — registry stats + open trade + last signal
  - `POST /api/strategies/pairs/start|stop|emergency-stop` — lifecycle control
  - `POST /api/strategies/pairs/backtest` — trigger backtest engine, return results
  - `GET /api/strategies/pairs/backtest/history` — past `backtest_run` records
  - `POST /api/strategies/pairs/{pair_id}/close` — manually close open trade
  - `GET /api/strategies/pairs/config` / `POST /api/strategies/pairs/config` — threshold configuration
- ✅ **Pairs Trading Monitoring Page** (`streamlit_ui/pages/Pairs_Trading.py`) — live monitoring via FastAPI, z-score chart, pair details expander
- ✅ **Database Schema** (`strategy_engine` schema):
  - `pair_registry` — validated pair definitions with `rank_score` composite metric
  - `pair_spread` — hourly spread/z-score time series
  - `pair_signal` — generated signals
  - `pair_trade` — open and closed two-legged trades with full audit columns
  - `pair_performance` — daily cumulative metrics
  - `backtest_run` — historical backtest results with equity curve + trade log (JSONB)
  - SQL migrations: `scripts/21_create_strategy_engine_tables.sql`, `scripts/22_strategy_engine_schema_fixes.sql`
- ✅ **Alpaca `get_bars()`** — added intraday bar fetching to `AlpacaClient`; strategy now pulls live hourly prices from Alpaca (not end-of-day DB) during market hours

### Changed
- `AlpacaClient` extended with `get_bars(symbol, limit, adjustment)` for intraday price data
- `PairsStrategy._fetch_prices()` switched from `market_data` DB table to Alpaca live bars
- Streamlit deprecations resolved: `Styler.applymap` → `Styler.map`, `st.dataframe(use_container_width)` → `width='stretch'`
- `src/web/main.py` — registered `pairs_trading_router`
- **UI Redesign** — full paper/ink design system applied across all pages:
  - `css_config.py` rewritten with design tokens (`--color-ink`, `--color-paper`, `--color-profit`, `--color-loss`, `--font-display`, `--font-body`, `--font-mono`)
  - `styles.css` rewritten — Playfair Display headings, DM Sans body, DM Mono for all numeric values; flat 4px-radius cards; no drop shadows; market status banners
  - `streamlit_app.py` (Dashboard) rebuilt — live Alpaca data, market clock banner, time-aware greeting, account metrics, positions table, open orders panel
  - `pages/1_Portfolio.py` rebuilt — real account data, close/cancel controls, allocation pie chart, order placement form
  - `pages/2_Analysis.py` — removed simulated OHLC fallback; warning shown when no data available
  - `pages/4_Pairs_Trading.py` and `pages/5_Backtest_Review.py` — `_load_css()` added; Plotly charts converted to transparent backgrounds
  - `pages/6_Settings.py` rebuilt — live connection status, real analysis preferences, system info; all fake hardcoded values removed
  - `pages/7_About.py` rebuilt (renamed from `Author.py`) — removed all `[placeholder]` template content; real bio, tech stack, contact links
  - Pages renamed with numeric prefixes for controlled sidebar ordering: `1_Portfolio`, `2_Analysis`, `3_Screener`, `4_Pairs_Trading`, `5_Backtest_Review`, `6_Settings`, `7_About`
  - `run_streamlit.py` — config.toml always written with paper/ink theme colors

### Active Pair (Paper Trading)
- **QRVO/SWKS** (Semiconductor sector): hedge ratio 0.9231, half-life 18.4h, correlation 0.8697, coint p-value 0.0024, rank score 0.8845
- Backtest result (180 days): Sharpe 0.516, win rate 61.5%, max drawdown 8.2% — **PASSED gate**
- Paper trading via Alpaca (`https://paper-api.alpaca.markets`), equity ~$100k

## [1.0.0] - 2025-12-XX

### Added
- ✅ **Paper Trading Integration**: Alpaca Markets API integration for paper trading
- ✅ **Multi-Source Data Ingestion**: 
  - Polygon.io integration for historical data
  - Yahoo Finance integration (10 data types: market data, company info, key statistics, dividends, splits, institutional holders, financial statements, company officers, analyst recommendations, ESG scores)
  - Alpaca integration for real-time trading data
- ✅ **Streamlit Web Dashboard**: 
  - Portfolio management page
  - Market analysis page with interactive Plotly charts
  - AI-powered stock screener with Ollama integration
  - Settings and system information pages
- ✅ **Database-First Logging**: Structured logging with PostgreSQL storage
- ✅ **Technical Indicators**: Automated calculation and storage (SMA, EMA, RSI, MACD, Bollinger Bands)
- ✅ **Prefect Workflow Orchestration**: 
  - Daily market data updates
  - Weekly company information updates
  - Weekly key statistics updates
- ✅ **Timezone Management**: UTC storage with Central Time display
- ✅ **FastAPI REST API**: Comprehensive API endpoints for trading operations
- ✅ **Database Architecture**: 
  - Separate `trading_system` and `prefect` databases
  - Service-specific schemas
  - Comprehensive table structure
- ✅ **Code Quality Tools**: Black, isort, Flake8, mypy integration
- ✅ **Testing Infrastructure**: Comprehensive test suite with pytest
- ✅ **Documentation**: Complete MkDocs documentation

### Changed
- Improved database schema with enhanced constraints and indexing
- Enhanced error handling across all services
- Optimized data ingestion workflows

### Fixed
- Database connection pooling issues
- Timezone handling in data storage
- Session state management in Streamlit UI

## [0.9.0] - 2025-11-XX

### Added
- Initial Yahoo Finance integration
- Basic Streamlit UI
- Database logging foundation

### Changed
- Refactored data ingestion architecture
- Improved error handling

## [0.8.0] - 2025-10-XX

### Added
- Polygon.io data integration
- Basic FastAPI endpoints
- Initial database schema

### Changed
- Migrated to modular architecture

## [0.7.0] - 2025-09-XX

### Added
- Initial project structure
- Basic Alpaca integration
- Core database models

---

## Version History

- **v1.0.0** (Released): Core features — paper trading, data ingestion, Streamlit dashboard, Prefect orchestration
- **v1.1.0** (Released 2026-03-28): Pairs trading strategy engine, backtesting, professional UI redesign
- **v1.2.0** (Planned): Risk management service, advanced analytics, data quality monitoring
- **v1.3.0** (Future): Microservices architecture, cloud deployment

## Status Indicators

- ✅ **Implemented**: Feature is complete and working
- 🚧 **In Progress**: Feature is being developed
- 📋 **Planned**: Feature is planned for future release
- 🔮 **Future**: Feature is under consideration

---

For detailed release notes, see [GitHub Releases](https://github.com/nishantnayar/trading-system/releases).

