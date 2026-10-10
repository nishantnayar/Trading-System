# Code Redundancy Review

**Date**: 2026-10-09
**Scope**: `src/`, `streamlit_ui/`, `scripts/`, root config/tooling (working tree incl. uncommitted changes)
**Goal**: Find duplicated or dead functionality and suggest where each concern should live.

---

## Status (2026-10-09)

Everything below has been applied unless listed here. See CHANGELOG `[Unreleased]` for the full list.

**Also done beyond the original list**: harmonic strategy removed on live-results grounds
(net -$81 over 173 paper trades); backtest equity double-count and 2x sizing fixed; P&L page
100x display bug fixed; RSI no-loss bug fixed; `pairs_flow.py` logging fixed.

**Deliberately not done / left for a decision**
- **CI black step is a no-op**: `pyproject.toml` `include = '\.pyi?$'` matches no files, so
  `black --check .` reports "No Python files". Fixing the regex reformats most of the repo -
  do it as its own commit.
- **SQL migration numbering** (`11b`, `13b`, `21b`, `22b`) - not renamed; renaming applied
  migrations breaks references. New migrations continue at 28, 29.
- **UI data access**: pages now use typed `api_client` methods; Strategy Monitor baskets and
  Pair Lab still read the DB directly (adding API endpoints for them is the follow-up).
- **`yahoo_adjusted_1h`** is still allowed by the market_data CHECK constraint (re-validating it
  scans the whole table); no code writes it.
- **4.4 spread calculators** left separate (small, well tested, different call shapes).
- **`run_discover_baskets_all_sectors.py`** still shells out per sector (it forwards CLI flags).
- **Harmonic paper positions**: the 5 open positions must be closed in Alpaca and the
  `intraday-harmonic` Prefect deployment deleted by the user.

---

## TL;DR - Top 10

| # | Issue | Impact | Effort |
|---|---|---|---|
| 1 | Two identical FastAPI entry points (`main.py`, `src/web/main.py`) | Every new router must be registered twice | S |
| 2 | `pairs_trading` router mounted twice (via `routes.py` and directly) | Every `/api/strategies/pairs/*` route registered 2x | S |
| 3 | Backend imports indicator math from the Streamlit UI package via `sys.path` hack | `src/` depends on `streamlit_ui/` - inverted layering | S |
| 4 | Same 1h bars stored under two labels (`yahoo_adjusted` and `yahoo_adjusted_1h`) - **DB-verified, 99.8% identical closes**; `yahoo_adjusted` timestamps also shifted 4-5h by a tz bug | Duplicate storage; discovery/backtest and live read different series | M |
| 5 | Five separate "load close prices from market_data" implementations | Inconsistent filters, timezones, sources | M |
| 6 | Signal logic duplicated (`SignalGenerator._evaluate` vs `BacktestSignalGenerator.evaluate`) | Backtest can silently diverge from live | S |
| 7 | P&L math duplicated 3x; position sizing differs between backtest and live | Backtest results not representative of live sizing | M |
| 8 | Discovery stats live in `scripts/` and are loaded by Prefect via `importlib` | Core logic not importable/testable as a module | M |
| 9 | UI uses three data-access styles (API client, raw `_make_request`, direct DB) | Same data fetched different ways per page | L |
| 10 | Large dead-code surface (Polygon stack, Redis config, Ollama stubs, ~30 unused settings, ~15 unused UI helpers) | Noise, misleading docs | S |

S = < 1 hour, M = half day, L = multi-day.

---

## 1. Application entry points & routing

### 1.1 Duplicate FastAPI apps
- [main.py](../../main.py) and [src/web/main.py](../../src/web/main.py) are the same app: same middleware, lifespan, and the same 10 `include_router` calls. Only differences: root `main.py` adds the conda-env check; `src/web/main.py` has type hints and `noqa` markers.
- Your memory note already says "register new routers in both" - that is the symptom.
- **Fix**: Keep `src/web/main.py` as the single app factory. Reduce root `main.py` to:
  ```python
  _check_conda_env()
  from src.web.main import app  # noqa: E402
  ```

### 1.2 `pairs_trading` router registered twice
- [src/web/api/routes.py:17](../../src/web/api/routes.py) does `router.include_router(pairs_trading_router)`, and both `main.py` files *also* call `app.include_router(pairs_trading_router)`.
- Result: every pairs route is added to the app twice (FastAPI won't error, the first match wins, but OpenAPI and route tables are doubled).
- **Fix**: Delete the include from `routes.py`; it should only hold `/` and `/health`.

### 1.3 Unused pairs API endpoints
No caller in `streamlit_ui/`, `scripts/`, or `src/` for:
- `POST /api/strategies/pairs/backtest` - Pair Lab runs `BacktestEngine` directly instead ([6_Pair_Lab.py:167](../../streamlit_ui/pages/6_Pair_Lab.py))
- `GET /api/strategies/pairs/backtest/history`
- `GET/POST /api/strategies/pairs/config` (reads/writes `config/strategies.yaml`, which nothing else reads)
- `POST /api/strategies/pairs/{pair_id}/close`
- `GET /api/market-data/stats`, `/symbols`, `/data/{symbol}/count`

Either have the UI use them or delete them. Having both the endpoint and an in-page reimplementation is the worst case.

### 1.4 Behavioural note (not redundancy, but spotted)
`POST /start` ([pairs_trading.py:383](../../src/web/api/pairs_trading.py)) sets `is_active=True` on **every** row in `pair_registry`, including pairs that `check_and_disable_failing_pairs_task` deliberately disabled. A Stop -> Start in Strategy Monitor reactivates every pair ever discovered. Consider a separate "strategy enabled" flag instead of overloading `is_active`.

---

## 2. Layering violations

### 2.1 Backend importing from the UI
[src/services/analytics/indicator_calculator.py:28-40](../../src/services/analytics/indicator_calculator.py) inserts `streamlit_ui/` into `sys.path` and imports `utils.technical_indicators`. The comment there already says "In production, these should be moved to a shared location".
- **Fix**: Move `streamlit_ui/utils/technical_indicators.py` to `src/shared/indicators.py` (or `src/services/analytics/indicators.py`). Have both the indicator service and the UI import from there.

### 2.2 `streamlit_ui/utils.py` vs `streamlit_ui/utils/` package
- A module `utils.py` and a package `utils/` with the same name coexist. Python always resolves `utils` to the package, so [streamlit_ui/utils/__init__.py](../../streamlit_ui/utils/__init__.py) uses `importlib` to load the shadowed `utils.py` and manually re-exports ~50 names.
- Pages import it three different ways: `from utils import ...`, `from streamlit_ui.utils import ...`, and a local `from utils import ...` inside a function.
- **Fix**: Rename `utils.py` -> e.g. `streamlit_ui/ui_helpers.py` (or split into `formatting.py`, `charts.py`, `data.py`), delete the importlib shim, use one import style.

### 2.3 Name collision: two `calculate_volatility`
- `streamlit_ui/utils.py:168` - `calculate_volatility(returns: pd.Series, window)` -> rolling Series
- `streamlit_ui/utils/technical_indicators.py:171` - `calculate_volatility(prices: List[float], period)` -> scalar
Same name, different semantics, both under "utils". Rename one after 2.1/2.2.

---

## 3. Market data: storage and loaders

### 3.1 Same bars stored twice under different labels
- The scheduled "Daily Market Data Update" deployment ([yahoo_flows.py:429-437](../../src/shared/prefect/flows/data_ingestion/yahoo_flows.py)) loads **`interval="1h"`** bars, and `backpopulate_yahoo_adjusted.py` defaults to `1h` too. So `yahoo_adjusted` is hourly data, not EOD as `CLAUDE.md` describes.
- `refresh_pair_prices_task` ([pairs_flow.py:132](../../src/shared/prefect/flows/strategy_engine/pairs_flow.py)) writes the same Yahoo 1h adjusted bars again as `yahoo_adjusted_1h`.
- Live strategy reads `yahoo_adjusted_1h` ([src/shared/market_data.py:22](../../src/shared/market_data.py)); discovery, backtest, Pair Lab and indicators read `yahoo_adjusted`.
- **Consequence**: two copies of the same series that can drift (different fetch times, adjustment snapshots), and pairs are discovered/backtested on a different series than they're traded on.
- **Related inconsistency**: [discover_baskets.py:332](../../scripts/discover_baskets.py) says "Data is daily bars (yahoo_adjusted); convert to hours" and multiplies half-life by 7, while [discover_pairs.py](../../scripts/discover_pairs.py) treats the same source as hourly. The DB check below shows the data **is** hourly, so basket half-lives (and therefore `z_score_window` / `max_hold_hours`) are inflated 7x.
- **Fix**: Pick one label for adjusted 1h bars and have every reader use it. If you want EOD bars too, give them an explicit label (`yahoo_adjusted_1d`).

#### DB verification (2026-10-09, read-only queries against `trading_system`)

| Source | Rows | Symbols | Spacing | Bars/day |
|---|---|---|---|---|
| `yahoo` | 4,792,436 | 1,038 | 1h | 7 |
| `yahoo_adjusted` | 4,792,579 | 1,038 | 1h (4.10M of 4.79M gaps = 1:00) | 7 (681k of 689k symbol-days) |
| `yahoo_adjusted_1h` | 12,569 | 20 | 1h | 7 |

**Timestamp bug found while comparing**: `yahoo_adjusted` (and `yahoo`) bars sit at **04:30-11:30 ET**, not the real session of 09:30-15:30 ET. Shifting by the ET offset lines them up exactly. Cause: [yahoo/client.py:94](../../src/services/yahoo/client.py) does `timestamp.to_pydatetime().replace(tzinfo=timezone.utc)` on an ET-aware index, which relabels ET wall-clock time as UTC (it should be `.astimezone(timezone.utc)`, which is what `refresh_pair_prices_task` uses). So every row written by `YahooDataLoader` is stamped 4h (EDT) / 5h (EST) too early. A naive join on `timestamp` therefore matches the wrong bars (only 40.8% overlap, avg 75 bps apart).

**After correcting the shift** (`a.timestamp AT TIME ZONE 'UTC' = h.timestamp AT TIME ZONE 'America/New_York'`):

| Metric | Value |
|---|---|
| `yahoo_adjusted_1h` rows with a matching `yahoo_adjusted` bar | 11,891 / 12,569 (94.6%) |
| Close exactly equal | 11,869 / 11,891 (**99.8%**) |
| Close within 1 bp | 11,871 |
| Volume exactly equal | 11,633 (97.8%) |
| Avg close difference | 0.08 bps |
| Per-symbol close ratio | 1.000000 +/- <0.0003 for 17 of 19 symbols |

Example (EWBC, 2026-06-23): five of six bars have identical close and volume; the 14:30 bar differs (130.88 vs 131.25, vol 30,725 vs 112,492) because the 1h copy captured a partially formed bar that was never refreshed.

Unmatched remainder:
- **BNY** (678 rows): `yahoo_adjusted` stops at 2026-07-27, so 1h is the only copy after that. Likely the symbol was deactivated in `symbols` or renamed, and the daily flow stopped loading it.
- A handful of first-bar-of-day / partial-bar differences (LRCX/KLAC 2026-08-05 09:30, last bar of 2026-10-09).

**Verdict**: Duplicate. `yahoo_adjusted_1h` is the same Yahoo adjusted 1h bars for 20 symbols, re-fetched every cycle, with correct timestamps. `yahoo_adjusted` holds the same bars for the whole universe with timestamps shifted 4-5h. The only real value the `_1h` copy adds is freshness (intraday updates) and correct timestamps.

**Impact of the timestamp bug**: 
- Series order is preserved, so z-scores, cointegration and indicator values are mostly unaffected (dates don't change because 04:30-11:30 ET stays on the same calendar day).
- Anything that uses time of day is wrong: Pair Lab / Analysis chart axes, any market-hours filter, and any join or `concat` between `yahoo_adjusted` and `yahoo_adjusted_1h`.
- Hold-time math across a DST change is off by 1h.

**Recommended consolidation**:
1. Fix `yahoo/client.py:94` to `.astimezone(timezone.utc)`.
2. Backfill: shift existing `yahoo` / `yahoo_adjusted` rows. This needs care because of the unique key on (symbol, timestamp, data_source) and the DST-dependent offset. Safest is `UPDATE ... SET timestamp = (timestamp AT TIME ZONE 'UTC') AT TIME ZONE 'America/New_York'`, run in a transaction against a backup first (or re-download).
3. Have `refresh_pair_prices_task` upsert into `yahoo_adjusted` (same label) for active symbols, so live, discovery, backtest and Pair Lab all read one series. Then drop `yahoo_adjusted_1h` from `get_price_series`, the CHECK constraint, and the DB.
4. Fix the basket half-life `* 7.0` in `discover_baskets.py:333`.

### 3.2 Two Yahoo ingestion code paths
- `YahooDataLoader.load_market_data` ([yahoo/loader.py:184](../../src/services/yahoo/loader.py)) -> `YahooClient.get_historical_data` -> per-ticker `yf.Ticker`, batched upsert.
- `refresh_pair_prices_task` re-implements fetch + record building + `pg_insert ... on_conflict_do_update` inline with batched `yf.download`.
- **Fix**: Add a batched `YahooClient.download_bars(symbols, ...)` + reuse `YahooDataLoader._upsert_records`; the Prefect task becomes ~15 lines.

### 3.3 Five "read close prices" implementations
| Location | Shape | Source default |
|---|---|---|
| `src/shared/market_data.py:get_price_series` | 1 symbol, last N, raw SQL | `yahoo_adjusted_1h` |
| `scripts/discover_pairs.py:get_hourly_closes` | N symbols, date range, pivot | `yahoo_adjusted` |
| `scripts/discover_baskets.py:get_hourly_closes` | **copy-paste** of the above | `yahoo_adjusted` |
| `backtesting/engine.py:_load_prices` | 2 symbols, date range | `yahoo_adjusted` |
| `6_Pair_Lab.py:load_price_history` + `_load_harmonic_prices` | UI, direct ORM | `yahoo_adjusted` |
| `harmonic_flow.py:load_prices_task` | N symbols | (own query) |

- **Fix**: One module (`src/shared/market_data.py`) with `get_price_series(symbol, limit|start/end, source)` and `get_close_panel(symbols, start, end, source)`. Everything else calls it.

### 3.4 Polygon stack is dead
`CLAUDE.md` says all price data comes from Yahoo. Still present:
- `src/services/polygon/` (client, models, exceptions) and `tests/unit/test_polygon_client.py`
- `src/services/data_ingestion/historical_loader.py` (683 lines) - only used by `examples/` and its own test
- `SymbolService` ([symbols.py:11,137,145](../../src/services/data_ingestion/symbols.py)) constructs a `PolygonClient` for `check_symbol_health` / `detect_delisted_symbols`
- `polygon_*` settings
- **Fix**: Delete `polygon/` and `historical_loader.py`; move symbol-health checks to Yahoo (or drop them).

### 3.5 Alpaca market-data client unused
`AlpacaClient.get_bars` ([alpaca/client.py:299](../../src/services/alpaca/client.py)) and the `StockHistoricalDataClient` built in `__init__` have no callers. Remove both - also removes a credential-using client you don't need.

---

## 4. Strategy engine duplication

### 4.1 Signal logic defined twice
`SignalGenerator._evaluate` ([signal_generator.py:118](../../src/services/strategy_engine/pairs/signal_generator.py)) and `BacktestSignalGenerator.evaluate` (line 215) are the same decision tree (stop-loss -> expire -> exit -> entry), differing only in reason strings and how the open-trade time is obtained.
- **Risk**: Change one threshold rule and the backtest no longer tests what you trade.
- **Fix**: One pure function `evaluate_signal(z, thresholds, open_entry_time, now)`; `SignalGenerator` does DB I/O then calls it, `BacktestSignalGenerator` just calls it.

### 4.2 P&L computed three ways
- `pair_executor._compute_pnl` (line 293)
- `backtesting/engine._compute_pnl` (line 421) - same formula + commission
- `harmonic_executor._compute_pnl` (line 312) - single-leg variant
- Baskets compute their own P&L inline in `baskets/strategy.py:354-366` - and **`pnl_pct` there is a fraction** (`pnl / total_invested`), while pairs and harmonic store a percentage (`* 100`). Any UI or report that mixes `pair_trade.pnl_pct` and `basket_trade.pnl_pct` is off by 100x.
- **Fix**: `src/services/strategy_engine/common/pnl.py` with `pair_pnl(...)`, `leg_pnl(...)` operating on plain floats; executors/engine adapt their objects.

### 4.3 Position sizing: three rules, backtest doesn't match live
- Live pairs: `KellySizer` - 2% bootstrap, Half-Kelly, 12% cap ([position_sizer.py](../../src/services/strategy_engine/pairs/position_sizer.py))
- Backtest: hardcoded 2% per leg, fractional shares ([engine.py:384](../../src/services/strategy_engine/backtesting/engine.py))
- Harmonic: own `compute_qty` 2% / 10% cap ([harmonic_executor.py:34](../../src/services/strategy_engine/harmonic/harmonic_executor.py))
- `BOOTSTRAP_FRACTION` / `MAX_LEG_FRACTION` constants exist but backtest and harmonic don't use them.
- **Fix**: Import the constants at minimum; ideally let `KellySizer` accept an injected trade history so the backtest can use it.

### 4.4 Spread calculators
`pairs/spread_calculator.py` and `baskets/spread_calculator.py` duplicate align -> log -> rolling mean/std -> z-score. A pair is a 2-asset basket with weights `[1, -hedge_ratio]`.
- **Fix**: Keep `SpreadCalculator` as a thin wrapper over `BasketSpreadCalculator` (or a shared `rolling_zscore(spread, window)` helper). Low priority - the code is small and well tested.

### 4.5 Basket strategy reuses pair machinery via a shim
`_make_fake_pair` ([baskets/strategy.py:42](../../src/services/strategy_engine/baskets/strategy.py)) builds a `SimpleNamespace` impersonating `PairRegistry` (`symbol2="_basket_"`) so it can use `SignalGenerator`. Fixing 4.1 removes the need for this.

### 4.6 Order placement outside `pair_executor.py`
`CLAUDE.md` says "Never write code that submits real Alpaca orders outside of `pair_executor.py`", but orders are also placed by:
- `baskets/strategy.py:_place_basket_orders` (line 304)
- `harmonic/harmonic_executor.py`
- `web/api/alpaca_routes.py` `POST /orders`
Either update the rule (e.g. "only executors and the manual-order API") or route these through a common executor.

### 4.7 Two backtesters, two metrics paths
- Pairs: `backtesting/engine.py` + `metrics.py` (`_sharpe_ratio`, `_max_drawdown`) + `report.py`
- Harmonic: `harmonic/backtest.py` with its own `summary()` metrics
- UI: `streamlit_ui/utils.py` has a third `calculate_sharpe_ratio` / `calculate_max_drawdown`
- **Fix**: Share `metrics.py` helpers (`sharpe`, `max_drawdown`) across all three.

### 4.8 Discovery logic lives in `scripts/`
- [pair_discovery_flow.py:77-85](../../src/shared/prefect/flows/strategy_engine/pair_discovery_flow.py) loads `scripts/discover_pairs.py` via `importlib.util.spec_from_file_location`.
- `compute_half_life` is implemented in both `discover_pairs.py:159` and `discover_baskets.py:173`; `get_active_symbols` and `get_hourly_closes` are copy-pasted too.
- `run_discover_baskets_all_sectors.py` shells out to `discover_baskets.py` via `subprocess`.
- **Fix**: Move stats + discovery into `src/services/strategy_engine/discovery/` (`stats.py`: correlation, Engle-Granger, Johansen, half-life/AR1; `pairs.py`; `baskets.py`). Keep the scripts as thin CLI wrappers.

### 4.9 Duplicated Prefect tasks
`check_market_open_task` and `_flow_run_name` are defined in both `pairs_flow.py` and `harmonic_flow.py`; both flows construct `AlpacaClient(is_paper=True)` themselves. Move to `src/shared/prefect/tasks/common_tasks.py`.

---

## 5. Streamlit UI

### 5.1 Three data-access styles
| Page | Access |
|---|---|
| 1 Portfolio, 2 Analysis, 3 Screener, 7 Ops | `get_api_client()` typed methods |
| 4 Strategy Monitor (Pairs tab), 5 P&L | `TradingSystemAPI(...)` + raw `api._make_request("GET", "/api/...")` |
| 4 Strategy Monitor (Baskets + Harmonic tabs), 6 Pair Lab | Direct `db_readonly_session` / `db_transaction` + ORM |

- Same page (4) mixes API for pairs and raw DB for baskets/harmonic.
- `TradingSystemAPI` has no pairs methods, so pages call the private `_make_request`.
- **Fix (incremental)**: Add `get_pairs_*`, `get_pnl_*`, `get_risk_*` methods to `api_client.py`; always use `get_api_client()`. Longer term, add basket/harmonic endpoints and remove direct DB access from pages (or explicitly decide the UI talks to the DB and drop the API for read-only views - but pick one).

### 5.2 Duplicate helpers across pages
- `_load_css()` copy-pasted in pages 4, 5, 6; `load_custom_css()` in pages 2, 3, *and* `utils.py:954`.
- `st.set_page_config` + `sys.path` manipulation boilerplate in every page, each slightly different (`insert(0)` vs `append`, one vs two levels).
- Formatters: `api_client.py:228-253` defines its own `format_currency`, `format_percentage`, `get_timeframe_days` with **different behaviour** from the `utils.py` versions (e.g. `format_currency` abbreviates to K/M in one, not the other). Plus `_fmt_dt`, `_fmt_dollar`, `_fmt_pct`, `_fmt_pnl`, `_fmt_mcap` per page.
- **Fix**: One `streamlit_ui/common.py` with `page_setup(title)`, `load_css()`, and formatters. Delete the formatters from `api_client.py`.

### 5.3 Unused helpers in `streamlit_ui/utils.py`
No caller outside `utils.py` / its re-export shim:
`format_date`, `create_pie_chart`, `initialize_session_state`, `update_session_state`, `get_session_state`, `reset_session_state`, `create_metric_card`, `create_info_card`, `create_expandable_section`, `validate_date_range`, `validate_numeric_input`, `handle_api_error`, `show_success_message`, `show_warning_message`, `generate_ohlc_data` (synthetic data generator).

### 5.4 LLM stubs
`streamlit_ui/services/llm_service.py` is a stub returning empty results ("Ollama has been removed"), but `3_Screener.py` still imports and wires it into an "AI powered" flow. Remove the AI paths from the Screener or remove the stub.

---

## 6. Dead modules & config

| Item | Status | Action |
|---|---|---|
| `src/services/agent/ops_monitor_agent.py` | 13-line no-op stub, **not called anywhere** (no task in `pairs_flow.py`) | Delete; update `CLAUDE.md` (still documents it as active, plus `AGENT_ENABLED`, `OLLAMA_MODEL`) |
| `src/services/alpaca/websocket.py` | No importers | Delete or park |
| `src/services/execution/`, `src/services/strategy_engine/strategies/` | Empty packages | Delete |
| `src/web/api/timezone_helpers.py` | Only used by `tests/unit/test_web_api.py` | Delete with its tests |
| `src/shared/logging/performance.py` | Decorators (`log_performance`, `track_execution_time`, ...) never applied | Delete or start using |
| `config/strategies.yaml` | Only read by the unused `/config` endpoint | Delete with endpoint |
| `config/pairs.yaml` | Only mentioned in a stale help string in `discover_pairs.py:455`; pairs live in the DB | Delete |
| Redis | `redis` in `requirements.txt`, `pytest-redis`/`types-redis` in test reqs + CI, `redis_*` in **both** `settings.py` and `config/database.py`, `test_settings.py` asserts them | Remove all |
| Logging | `src/` mixes stdlib `logging` (7 files incl. `pairs_flow.py`, `alpaca/client.py`) with `loguru` everywhere else | Standardise on loguru |

### 6.1 Settings duplication and unused fields
- `postgres_*`, `trading_db_name`, `redis_*` are defined in both `src/config/settings.py` and `src/config/database.py`. Only `DatabaseConfig` versions are used.
- Settings fields with **no reader** anywhere: `app_name`, `app_version`, `postgres_*` (in Settings), `redis_*`, `alpaca_base_url`, `alpaca_data_url`, `polygon_data_delay_minutes`, `jwt_*`, `max_position_size`, `risk_enabled`, `circuit_breaker_enabled`, `max_orders_per_hour/day`, `log_file_path`, `log_retention_days`, `log_rotation_size` (logging uses `config/logging.yaml`), all four `*_timezone` fields (`timezone.py` hardcodes zones), `backtest_slippage_bps`, `backtest_commission_per_trade`.
- **Paper flag has two sources of truth**: `settings.paper_trading` only affects the email subject tag, while every `AlpacaClient(...)` is hardcoded `is_paper=True` (pairs_flow, harmonic_flow, alpaca_routes, pairs_trading x2). Fine for safety, but the `[PAPER]`/`[LIVE]` tag can lie. Either derive both from settings or drop the setting. (`CLAUDE.md` also calls it `IS_PAPER_TRADING`; the actual env var is `PAPER_TRADING`.)

---

## 7. Repo / tooling clutter

- **Config defined in multiple places**:
  - isort: `.isort.cfg`, `pyproject.toml`, `tools/pyproject.toml`
  - mypy: `mypy.ini`, `tools/pyproject.toml`
  - pytest: `pytest.ini`, `tools/pyproject.toml`
  - mkdocs: `mkdocs.yml`, `tools/mkdocs.yml` (differ)
  - pre-commit config lives in `tools/` where pre-commit won't find it
  - `tools/` is not referenced by CI. Merge into root `pyproject.toml` and delete `tools/`.
- **Docs duplicated**: `CHANGELOG.md` and `CONTRIBUTING.md` exist in root *and* `docs/` with different contents. Git tracks `Readme.md` while the working copy shows `README.md` (case-only mismatch on Windows - will bite on Linux/CI).
- **`scripts/test_*.py`** (`test_database_connections.py`, `test_prefect.py`) overlap `tests/unit/test_database_connections.py` and `tests/integration/test_prefect_config.py`; their `test_` prefix also risks pytest collection. Rename to `check_*.py` or delete.
- **SQL migration numbering**: `11`/`11b`, `13`/`13b`, `21`/`21b`, `22`/`22b` - the `b` files are unrelated new tables, not amendments (e.g. `13b_create_dividends_table.sql`). `CLAUDE.md` references both `21_add_yahoo_adjusted_1h_source.sql` (doesn't exist) and `21b_...`. Consider a migration tool (Alembic) or at least strictly sequential numbers.
- **`examples/`** (~2.2k lines) - demo scripts for Polygon loader, timezone utils, Yahoo loaders. Several target code that's dead (see 3.4). Prune.
- **`notebooks/`** - 13 TFT/LSTM notebook versions plus `models/lstm_mu_model.pth`, `df_market.pkl`, `lightning_logs/`. Unrelated to the pairs system; keep latest or move to a separate research repo.

---

## Suggested order

1. **Quick, zero-risk deletions** (one PR): 1.1, 1.2, 3.5, section 6 dead modules, Redis, unused settings, 5.3, `tools/`. Run `black`/`isort`/`mypy`/unit tests.
2. **Correctness-adjacent**: verify bar spacing in `yahoo_adjusted` (3.1), then fix the basket half-life conversion if needed and unify the data source label.
3. **Shared quant core**: 4.1 (signal), 4.2 (P&L), 4.3 (sizing constants), 2.1 (indicators out of UI). Each has existing unit tests to lean on.
4. **Move discovery into `src/`** (4.8) and unify price loaders (3.3).
5. **UI consolidation** (2.2, 5.1, 5.2) - largest but lowest risk to trading.
