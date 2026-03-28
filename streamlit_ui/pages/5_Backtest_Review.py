"""
Backtest Review — Pairs Trading Strategy Gate

Run backtests against historical data, review results, and decide whether
to enable live trading for a pair.

Gate criteria (all must pass before enabling live trading):
    Sharpe ratio  > 0.5
    Win rate      > 45%
    Max drawdown  < 15%

This page calls BacktestEngine directly (no API dependency).
"""

import os
import sys
from datetime import date, timedelta
from typing import Optional

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.services.strategy_engine.backtesting.engine import BacktestEngine  # noqa: E402
from src.services.strategy_engine.backtesting.metrics import (  # noqa: E402
    MetricsCalculator,
)
from src.services.strategy_engine.backtesting.report import BacktestReport  # noqa: E402
from src.shared.database.base import db_readonly_session, db_transaction  # noqa: E402
from src.shared.database.models.company_info import CompanyInfo  # noqa: E402
from src.shared.database.models.dividends import Dividend  # noqa: E402
from src.shared.database.models.key_statistics import KeyStatistics  # noqa: E402
from src.shared.database.models.market_data import MarketData  # noqa: E402
from src.shared.database.models.stock_splits import StockSplit  # noqa: E402
from src.shared.database.models.strategy_models import (  # noqa: E402
    BacktestRun,
    PairRegistry,
)

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Backtest Review",
    page_icon="📊",
    layout="wide",
)

PLOTLY_CONFIG = {
    "displayModeBar": True,
    "displaylogo": False,
    "modeBarButtonsToRemove": ["pan2d", "lasso2d", "select2d"],
}

# Colour palette — consistent across all charts
C1 = "#1f77b4"   # symbol1 — blue
C2 = "#ff7f0e"   # symbol2 — orange
CDIV1 = "#1f77b4"
CDIV2 = "#ff7f0e"
CSPLIT = "#e377c2"
CDANGER = "#C0392B"
CWARN = "#D97706"
CPASS = "#2A7A4B"


def _load_css() -> None:
    css_file = os.path.join(os.path.dirname(__file__), "..", "styles.css")
    try:
        with open(css_file) as f:
            css = f.read()
        from css_config import generate_css_variables, get_theme_css
        st.markdown(
            f"<style>{generate_css_variables()}{css}{get_theme_css()}</style>",
            unsafe_allow_html=True,
        )
    except Exception:
        pass

# ---------------------------------------------------------------------------
# Cached data fetchers
# ---------------------------------------------------------------------------


@st.cache_data(ttl=60)
def load_pairs() -> list:
    """Return list of registered pairs ordered active-first."""
    try:
        with db_readonly_session() as session:
            pairs = session.query(PairRegistry).all()
            # Sort: active first, then by rank_score desc (Python-side avoids
            # SQLAlchemy column-not-yet-mapped errors on stale cache)
            pairs.sort(
                key=lambda p: (
                    not p.is_active,
                    -(float(p.rank_score) if p.rank_score else 0.0),
                )
            )
            return [
                {
                    "id": p.id,
                    "label": (
                        f"#{i+1}  {p.symbol1}/{p.symbol2}"
                        f"  [{p.sector or 'N/A'}]"
                        + (
                            f"  ★{float(p.rank_score):.3f}"
                            if p.rank_score else ""
                        )
                    ),
                    "symbol1": p.symbol1,
                    "symbol2": p.symbol2,
                    "sector": p.sector,
                    "hedge_ratio": float(p.hedge_ratio),
                    "half_life_hours": (
                        float(p.half_life_hours) if p.half_life_hours else None
                    ),
                    "correlation": (
                        float(p.correlation) if p.correlation else None
                    ),
                    "coint_pvalue": (
                        float(p.coint_pvalue) if p.coint_pvalue else None
                    ),
                    "z_score_window": int(p.z_score_window),
                    "entry_threshold": float(p.entry_threshold),
                    "exit_threshold": float(p.exit_threshold),
                    "stop_loss_threshold": float(p.stop_loss_threshold),
                    "rank_score": (
                        float(p.rank_score) if p.rank_score else None
                    ),
                    "is_active": p.is_active,
                }
                for i, p in enumerate(pairs)
            ]
    except Exception as e:
        st.error(f"Error loading pairs: {e}")
        return []


@st.cache_data(ttl=300)
def load_company_info(symbol1: str, symbol2: str) -> dict:
    """Load CompanyInfo rows for both symbols."""
    result = {}
    with db_readonly_session() as session:
        for sym in (symbol1, symbol2):
            row = session.query(CompanyInfo).filter_by(symbol=sym).first()
            if row:
                result[sym] = {
                    "name": row.name or sym,
                    "sector": row.sector or "—",
                    "industry": row.industry or "—",
                    "exchange": row.exchange or "—",
                    "employees": row.employees,
                    "market_cap": row.market_cap,
                    "description": row.description or "",
                    "website": row.website or "",
                }
            else:
                result[sym] = {"name": sym}
    return result


@st.cache_data(ttl=300)
def load_key_stats(symbol1: str, symbol2: str) -> dict:
    """Load the most recent KeyStatistics row for each symbol."""
    result = {}
    with db_readonly_session() as session:
        for sym in (symbol1, symbol2):
            row = (
                session.query(KeyStatistics)
                .filter(KeyStatistics.symbol == sym)
                .order_by(KeyStatistics.date.desc())
                .first()
            )
            if row:
                result[sym] = {
                    "market_cap": row.market_cap,
                    "beta": float(row.beta) if row.beta else None,
                    "avg_volume": row.average_volume,
                    "trailing_pe": (
                        float(row.trailing_pe) if row.trailing_pe else None
                    ),
                    "price_to_book": (
                        float(row.price_to_book) if row.price_to_book else None
                    ),
                    "profit_margin": (
                        float(row.profit_margin) if row.profit_margin else None
                    ),
                    "roe": (
                        float(row.return_on_equity)
                        if row.return_on_equity else None
                    ),
                    "debt_to_equity": (
                        float(row.debt_to_equity)
                        if row.debt_to_equity else None
                    ),
                    "revenue_growth": (
                        float(row.revenue_growth)
                        if row.revenue_growth else None
                    ),
                    "earnings_growth": (
                        float(row.earnings_growth)
                        if row.earnings_growth else None
                    ),
                    "fifty_two_week_high": (
                        float(row.fifty_two_week_high)
                        if row.fifty_two_week_high else None
                    ),
                    "fifty_two_week_low": (
                        float(row.fifty_two_week_low)
                        if row.fifty_two_week_low else None
                    ),
                    "shares_short": row.shares_short,
                    "short_ratio": (
                        float(row.short_ratio) if row.short_ratio else None
                    ),
                    "held_pct_inst": (
                        float(row.held_percent_institutions)
                        if row.held_percent_institutions else None
                    ),
                    "as_of": row.date.isoformat() if row.date else "—",
                }
            else:
                result[sym] = {}
    return result


@st.cache_data(ttl=300)
def load_price_history(
    symbol1: str, symbol2: str, start: date, end: date, data_source: str = "yahoo_adjusted"
) -> tuple:
    """Load hourly close prices for both symbols over the date range."""
    with db_readonly_session() as session:
        def _fetch(sym):
            rows = (
                session.query(MarketData.timestamp, MarketData.close)
                .filter(
                    MarketData.symbol == sym,
                    MarketData.data_source == data_source,
                    MarketData.timestamp >= pd.Timestamp(start, tz="UTC"),
                    MarketData.timestamp <= pd.Timestamp(end, tz="UTC"),
                    MarketData.close.isnot(None),
                )
                .order_by(MarketData.timestamp)
                .all()
            )
            if not rows:
                return pd.Series(dtype=float, name=sym)
            idx = [r.timestamp for r in rows]
            vals = [float(r.close) for r in rows]
            return pd.Series(vals, index=pd.DatetimeIndex(idx, tz="UTC"), name=sym)

        s1 = _fetch(symbol1)
        s2 = _fetch(symbol2)
    return s1, s2


@st.cache_data(ttl=3600)
def load_corporate_events(
    symbol1: str, symbol2: str, start: date, end: date
) -> dict:
    """Load dividends and splits for both symbols in the date window."""
    events: dict = {symbol1: {"dividends": [], "splits": []},
                    symbol2: {"dividends": [], "splits": []}}
    with db_readonly_session() as session:
        for sym in (symbol1, symbol2):
            divs = (
                session.query(Dividend.ex_date, Dividend.amount)
                .filter(
                    Dividend.symbol == sym,
                    Dividend.ex_date >= start,
                    Dividend.ex_date <= end,
                )
                .order_by(Dividend.ex_date)
                .all()
            )
            events[sym]["dividends"] = [
                {"date": d.ex_date, "amount": float(d.amount)} for d in divs
            ]

            splits = (
                session.query(StockSplit.split_date, StockSplit.split_ratio,
                              StockSplit.ratio_str)
                .filter(
                    StockSplit.symbol == sym,
                    StockSplit.split_date >= start,
                    StockSplit.split_date <= end,
                )
                .order_by(StockSplit.split_date)
                .all()
            )
            events[sym]["splits"] = [
                {
                    "date": s.split_date,
                    "ratio": float(s.split_ratio),
                    "label": s.ratio_str or f"{float(s.split_ratio):.2f}",
                }
                for s in splits
            ]
    return events


@st.cache_data(ttl=30)
def load_run_history(pair_id: int) -> pd.DataFrame:
    """Load previous BacktestRun records for a pair."""
    try:
        with db_readonly_session() as session:
            runs = (
                session.query(BacktestRun)
                .filter(BacktestRun.pair_id == pair_id)
                .order_by(BacktestRun.run_date.desc())
                .limit(20)
                .all()
            )
            if not runs:
                return pd.DataFrame()
            rows = []
            for r in runs:
                rows.append({
                    "ID": r.id,
                    "Run Date": r.run_date,
                    "Period": f"{r.start_date} → {r.end_date}",
                    "Entry±": r.entry_threshold,
                    "Exit±": r.exit_threshold,
                    "Stop±": r.stop_loss_threshold,
                    "Return%": round(float(r.total_return or 0), 2),
                    "Sharpe": round(float(r.sharpe_ratio or 0), 3),
                    "MaxDD%": round(float(r.max_drawdown or 0), 2),
                    "WinRate%": round(float(r.win_rate or 0), 1),
                    "Trades": r.total_trades,
                    "Gate": "PASS" if r.passed_gate else "FAIL",
                    "Notes": r.notes or "",
                })
            return pd.DataFrame(rows)
    except Exception as e:
        st.error(f"Error loading run history: {e}")
        return pd.DataFrame()


def _set_pair_active(pair_id: int, active: bool) -> None:
    """Toggle is_active flag on a pair_registry row."""
    with db_transaction() as session:
        pair = session.query(PairRegistry).filter_by(id=pair_id).first()
        if pair:
            pair.is_active = active


# ---------------------------------------------------------------------------
# Main page
# ---------------------------------------------------------------------------

def main():
    _load_css()
    st.title("Backtest Review — Pairs Trading")
    st.caption(
        "Run strategy backtests on historical data. "
        "All three gate criteria must pass before enabling live trading."
    )

    pairs = load_pairs()
    if not pairs:
        st.warning("No pairs registered. Run `scripts/discover_pairs.py` first.")
        return

    # -----------------------------------------------------------------------
    # Sidebar — config panel
    # -----------------------------------------------------------------------
    with st.sidebar:
        st.header("Configuration")

        pair_labels = [p["label"] for p in pairs]
        selected_label = st.selectbox("Select Pair", pair_labels)
        selected = next(p for p in pairs if p["label"] == selected_label)

        st.divider()

        st.subheader("Date Range")
        default_end = date.today()
        default_start = default_end - timedelta(days=180)
        start_date = st.date_input("Start Date", value=default_start)
        end_date = st.date_input("End Date", value=default_end)

        st.divider()

        st.subheader("Strategy Parameters")
        entry_threshold = st.slider(
            "Entry threshold (±z)", 1.0, 3.5,
            float(selected["entry_threshold"]), 0.1,
        )
        exit_threshold = st.slider(
            "Exit threshold (±z)", 0.1, 1.5,
            float(selected["exit_threshold"]), 0.1,
        )
        stop_threshold = st.slider(
            "Stop loss (±z)", 2.5, 5.0,
            float(selected["stop_loss_threshold"]), 0.1,
        )

        st.divider()

        initial_capital = st.number_input(
            "Initial Capital ($)", min_value=10_000, max_value=1_000_000,
            value=100_000, step=10_000,
        )

        notes = st.text_input(
            "Notes (optional)", placeholder="e.g. Tighter stop loss test"
        )

        run_btn = st.button("Run Backtest", type="primary", use_container_width=True)

    # -----------------------------------------------------------------------
    # Pair header row: stats + activate button
    # -----------------------------------------------------------------------
    col_a, col_b, col_c, col_d, col_r, col_e = st.columns([2, 2, 2, 2, 2, 2])
    col_a.metric("Hedge Ratio (β)", f"{selected['hedge_ratio']:.4f}")
    col_b.metric(
        "Half-Life",
        f"{selected['half_life_hours']:.1f}h"
        if selected["half_life_hours"] else "N/A",
    )
    col_c.metric("Z-Score Window", f"{selected['z_score_window']} bars")

    # Rank score with colour-coded quality label
    rank = selected.get("rank_score")
    if rank is not None:
        rank_label = (
            "Excellent" if rank >= 0.85
            else "Good" if rank >= 0.75
            else "Fair" if rank >= 0.60
            else "Weak"
        )
        col_r.metric(
            "Rank Score",
            f"{rank:.4f}",
            delta=rank_label,
            delta_color="normal" if rank >= 0.75 else "inverse",
            help="(1 - coint_p) × |correlation| × liquidity. Higher = stronger pair.",
        )
    else:
        col_r.metric("Rank Score", "N/A")

    col_d.metric("Status", "Active" if selected["is_active"] else "Inactive")

    with col_e:
        if selected["is_active"]:
            if st.button("Deactivate Pair", type="secondary", use_container_width=True):
                _set_pair_active(selected["id"], False)
                load_pairs.clear()
                st.rerun()
        else:
            if st.button("Activate Pair", type="primary", use_container_width=True):
                _set_pair_active(selected["id"], True)
                load_pairs.clear()
                st.rerun()

    st.divider()

    # -----------------------------------------------------------------------
    # Stock Analysis Panel
    # -----------------------------------------------------------------------
    _render_pair_analysis(selected, start_date, end_date)

    st.divider()

    # -----------------------------------------------------------------------
    # Run backtest
    # -----------------------------------------------------------------------
    if run_btn:
        if start_date >= end_date:
            st.error("Start date must be before end date.")
            return

        with db_readonly_session() as session:
            pair_row = (
                session.query(PairRegistry).filter_by(id=selected["id"]).first()
            )
            if pair_row is None:
                st.error("Pair not found in database.")
                return
            pair_row.entry_threshold = entry_threshold
            pair_row.exit_threshold = exit_threshold
            pair_row.stop_loss_threshold = stop_threshold
            session.expunge(pair_row)

        with st.spinner(
            f"Running backtest for {selected['symbol1']}/{selected['symbol2']}…"
        ):
            try:
                engine = BacktestEngine(
                    pair=pair_row,
                    start_date=start_date,
                    end_date=end_date,
                    initial_capital=float(initial_capital),
                )
                result = engine.run()
                calc = MetricsCalculator()
                metrics = calc.compute(result)

                reporter = BacktestReport()
                run_id = reporter.save(result, metrics, notes=notes or None)

                st.session_state["last_result"] = result
                st.session_state["last_metrics"] = metrics
                st.session_state["last_run_id"] = run_id

                load_run_history.clear()

            except Exception as e:
                st.error(f"Backtest failed: {e}")
                st.exception(e)
                return

    # -----------------------------------------------------------------------
    # Backtest results
    # -----------------------------------------------------------------------
    result = st.session_state.get("last_result")
    metrics = st.session_state.get("last_metrics")
    run_id = st.session_state.get("last_run_id")

    if result is not None and metrics is not None:
        _render_results(result, metrics, run_id)

    # -----------------------------------------------------------------------
    # Run history
    # -----------------------------------------------------------------------
    st.subheader("Run History")
    history_df = load_run_history(selected["id"])
    if history_df.empty:
        st.info("No previous backtest runs for this pair.")
    else:
        def _highlight_gate(val):
            return (
                "background-color: rgba(42,122,75,0.08)"
                if val == "PASS"
                else "background-color: rgba(192,57,43,0.08)"
            )

        styled = history_df.style.map(_highlight_gate, subset=["Gate"])
        st.dataframe(styled, width="stretch", hide_index=True)


# ---------------------------------------------------------------------------
# Stock Analysis Panel
# ---------------------------------------------------------------------------

def _render_pair_analysis(selected: dict, start_date: date, end_date: date):
    """
    Full trader-focused analysis panel for the selected pair.

    Tabs:
      1. Risk Flags   — immediate go/no-go signals before running backtest
      2. Fundamentals — company profiles + side-by-side key stats
      3. Price Chart  — normalised prices, volume, dividends, splits
      4. Correlation  — rolling 30-bar correlation with stability assessment
    """
    s1 = selected["symbol1"]
    s2 = selected["symbol2"]

    with st.expander(f"Stock Analysis — {s1} / {s2}", expanded=True):
        company = load_company_info(s1, s2)
        stats = load_key_stats(s1, s2)
        prices1, prices2 = load_price_history(s1, s2, start_date, end_date)
        events = load_corporate_events(s1, s2, start_date, end_date)

        tab_flags, tab_fund, tab_price, tab_corr = st.tabs(
            ["⚠ Risk Flags", "Fundamentals", "Price Chart", "Correlation"]
        )

        # -------------------------------------------------------------------
        # Tab 1 — Risk Flags
        # -------------------------------------------------------------------
        with tab_flags:
            flags = _compute_risk_flags(
                s1, s2, stats, prices1, prices2, events, selected
            )
            if not flags:
                st.success("No risk flags detected. Pair looks clean.")
            else:
                for f in flags:
                    if f["level"] == "danger":
                        st.error(f"**{f['title']}** — {f['detail']}")
                    else:
                        st.warning(f"**{f['title']}** — {f['detail']}")

            # Quick stat summary so trader sees numbers behind each flag
            st.markdown("---")
            st.caption("Supporting figures")
            fc1, fc2, fc3, fc4 = st.columns(4)
            mc1 = stats.get(s1, {}).get("market_cap")
            mc2 = stats.get(s2, {}).get("market_cap")
            fc1.metric(
                "Market Cap Ratio",
                _mcap_ratio_str(mc1, mc2),
                help=f"{s1} vs {s2} — pairs trade best when <5×",
            )
            av1 = stats.get(s1, {}).get("avg_volume") or 0
            av2 = stats.get(s2, {}).get("avg_volume") or 0
            fc2.metric(
                "Avg Volume Ratio",
                f"{max(av1, av2) / min(av1, av2):.1f}×"
                if min(av1, av2) > 0 else "N/A",
                help="Liquidity balance — keep below 10×",
            )
            b1 = stats.get(s1, {}).get("beta")
            b2 = stats.get(s2, {}).get("beta")
            fc3.metric(
                "Beta Gap",
                f"{abs((b1 or 0) - (b2 or 0)):.2f}"
                if b1 and b2 else "N/A",
                help="Market sensitivity diff — keep below 0.5",
            )
            # Upcoming dividends within 10 days
            from datetime import date as _date
            today = _date.today()
            upcoming = []
            for sym in (s1, s2):
                for d in events[sym]["dividends"]:
                    days_away = (d["date"] - today).days
                    if 0 <= days_away <= 10:
                        upcoming.append(f"{sym} ex-div in {days_away}d")
            fc4.metric(
                "Upcoming Ex-Div",
                ", ".join(upcoming) if upcoming else "None",
                help="Ex-dividend within 10 days can distort spread",
            )

        # -------------------------------------------------------------------
        # Tab 2 — Fundamentals
        # -------------------------------------------------------------------
        with tab_fund:
            # Company cards
            cc1, cc2 = st.columns(2)
            for col, sym in ((cc1, s1), (cc2, s2)):
                info = company.get(sym, {})
                ks = stats.get(sym, {})
                with col:
                    st.markdown(
                        f"### {info.get('name', sym)}  `{sym}`"
                    )
                    st.caption(
                        f"{info.get('industry', '—')}  ·  "
                        f"{info.get('exchange', '—')}  ·  "
                        f"{info.get('sector', '—')}"
                    )
                    mc = info.get("market_cap") or ks.get("market_cap")
                    emp = info.get("employees")
                    st.markdown(
                        f"**Market Cap:** {_fmt_mcap(mc)}  "
                        f"  **Employees:** {emp:,}" if emp else
                        f"**Market Cap:** {_fmt_mcap(mc)}"
                    )
                    desc = info.get("description", "")
                    if desc:
                        st.caption(desc[:280] + ("…" if len(desc) > 280 else ""))

            st.markdown("---")

            # Side-by-side key stats table
            st.subheader("Key Statistics")
            rows = [
                ("Market Cap", _fmt_mcap, "market_cap"),
                ("Beta (β)", lambda v: f"{v:.2f}", "beta"),
                ("Avg Daily Volume", lambda v: f"{int(v):,}", "avg_volume"),
                ("Trailing P/E", lambda v: f"{v:.1f}×", "trailing_pe"),
                ("Price / Book", lambda v: f"{v:.2f}×", "price_to_book"),
                ("Profit Margin", lambda v: f"{v*100:.1f}%", "profit_margin"),
                ("Return on Equity", lambda v: f"{v*100:.1f}%", "roe"),
                ("Debt / Equity", lambda v: f"{v:.2f}", "debt_to_equity"),
                ("Revenue Growth", lambda v: f"{v*100:+.1f}%", "revenue_growth"),
                ("Earnings Growth", lambda v: f"{v*100:+.1f}%", "earnings_growth"),
                ("52-Wk High", lambda v: f"${v:.2f}", "fifty_two_week_high"),
                ("52-Wk Low", lambda v: f"${v:.2f}", "fifty_two_week_low"),
                ("Short Ratio", lambda v: f"{v:.1f}d", "short_ratio"),
                ("Inst. Ownership", lambda v: f"{v*100:.1f}%", "held_pct_inst"),
            ]
            table_data = {"Metric": [], s1: [], s2: []}
            for label, fmt, key in rows:
                v1 = stats.get(s1, {}).get(key)
                v2 = stats.get(s2, {}).get(key)
                table_data["Metric"].append(label)
                table_data[s1].append(_safe_fmt(v1, fmt))
                table_data[s2].append(_safe_fmt(v2, fmt))
            st.dataframe(
                pd.DataFrame(table_data),
                width="stretch",
                hide_index=True,
            )
            if stats.get(s1):
                st.caption(
                    f"Data as of: {s1} → {stats[s1].get('as_of', '—')}  "
                    f"  {s2} → {stats.get(s2, {}).get('as_of', '—')}"
                )

        # -------------------------------------------------------------------
        # Tab 3 — Price Chart
        # -------------------------------------------------------------------
        with tab_price:
            if prices1.empty or prices2.empty:
                st.info("Not enough price data in the selected date range.")
            else:
                _render_price_chart(s1, s2, prices1, prices2, events)

        # -------------------------------------------------------------------
        # Tab 4 — Correlation
        # -------------------------------------------------------------------
        with tab_corr:
            if prices1.empty or prices2.empty:
                st.info("Not enough price data to compute rolling correlation.")
            else:
                _render_correlation_chart(
                    s1, s2, prices1, prices2,
                    registered_corr=selected.get("correlation"),
                )


# ---------------------------------------------------------------------------
# Risk flag logic
# ---------------------------------------------------------------------------

def _compute_risk_flags(
    s1: str,
    s2: str,
    stats: dict,
    prices1: pd.Series,
    prices2: pd.Series,
    events: dict,
    selected: dict,
) -> list:
    flags = []
    ks1 = stats.get(s1, {})
    ks2 = stats.get(s2, {})

    # 1. Market cap mismatch (>10× is a structural mismatch)
    mc1 = ks1.get("market_cap") or 0
    mc2 = ks2.get("market_cap") or 0
    if mc1 > 0 and mc2 > 0:
        ratio = max(mc1, mc2) / min(mc1, mc2)
        if ratio > 10:
            flags.append({
                "level": "danger",
                "title": "Large Market Cap Mismatch",
                "detail": (
                    f"{s1} vs {s2} market cap ratio is {ratio:.1f}×. "
                    "Extreme size differences weaken cointegration stability."
                ),
            })
        elif ratio > 5:
            flags.append({
                "level": "warn",
                "title": "Market Cap Mismatch",
                "detail": (
                    f"Ratio is {ratio:.1f}×. Monitor — the larger company may "
                    "absorb sector shocks differently."
                ),
            })

    # 2. Liquidity mismatch (>10× avg volume makes leg balancing hard)
    av1 = ks1.get("avg_volume") or 0
    av2 = ks2.get("avg_volume") or 0
    if av1 > 0 and av2 > 0:
        liq_ratio = max(av1, av2) / min(av1, av2)
        if liq_ratio > 10:
            flags.append({
                "level": "danger",
                "title": "Liquidity Mismatch",
                "detail": (
                    f"Average volume ratio is {liq_ratio:.1f}×. "
                    "The thinner leg may experience significant slippage."
                ),
            })
        elif liq_ratio > 5:
            flags.append({
                "level": "warn",
                "title": "Liquidity Imbalance",
                "detail": (
                    f"Volume ratio is {liq_ratio:.1f}×. "
                    "Watch for slippage on the smaller leg."
                ),
            })

    # 3. Beta divergence (different market sensitivity → spread driven by beta, not mean-reversion)
    b1 = ks1.get("beta")
    b2 = ks2.get("beta")
    if b1 is not None and b2 is not None:
        gap = abs(b1 - b2)
        if gap > 0.7:
            flags.append({
                "level": "danger",
                "title": "High Beta Divergence",
                "detail": (
                    f"{s1} β={b1:.2f}, {s2} β={b2:.2f} (gap {gap:.2f}). "
                    "The spread will be heavily influenced by market direction."
                ),
            })
        elif gap > 0.4:
            flags.append({
                "level": "warn",
                "title": "Beta Divergence",
                "detail": (
                    f"Gap is {gap:.2f}. Consider delta-hedging or using "
                    "beta-adjusted position sizing."
                ),
            })

    # 4. Recent correlation decay
    if len(prices1) > 60 and len(prices2) > 60:
        aligned = pd.concat([prices1, prices2], axis=1).dropna()
        if len(aligned) > 60:
            log_ret = np.log(aligned / aligned.shift(1)).dropna()
            # Last 30 bars vs registered correlation
            recent_corr = (
                log_ret.iloc[-30:][s1].corr(log_ret.iloc[-30:][s2])
                if len(log_ret) >= 30
                else None
            )
            reg_corr = selected.get("correlation")
            if recent_corr is not None and reg_corr is not None:
                decay = reg_corr - recent_corr
                if recent_corr < 0.5:
                    flags.append({
                        "level": "danger",
                        "title": "Correlation Breakdown",
                        "detail": (
                            f"Recent 30-bar correlation is {recent_corr:.3f} "
                            f"(registered: {reg_corr:.3f}). "
                            "The statistical relationship may have broken down."
                        ),
                    })
                elif decay > 0.2:
                    flags.append({
                        "level": "warn",
                        "title": "Correlation Weakening",
                        "detail": (
                            f"Recent correlation dropped {decay:.3f} pts to "
                            f"{recent_corr:.3f}. Re-validate the pair."
                        ),
                    })

    # 5. Stock splits in the window
    for sym in (s1, s2):
        for sp in events[sym]["splits"]:
            flags.append({
                "level": "danger",
                "title": f"Stock Split — {sym}",
                "detail": (
                    f"{sym} had a {sp['label']} split on {sp['date']}. "
                    "This may have introduced a price discontinuity in the spread."
                ),
            })

    # 6. Upcoming ex-dividend within 10 days
    from datetime import date as _date
    today = _date.today()
    for sym in (s1, s2):
        for d in events[sym]["dividends"]:
            days_away = (d["date"] - today).days
            if 0 <= days_away <= 10:
                flags.append({
                    "level": "warn",
                    "title": f"Upcoming Ex-Dividend — {sym}",
                    "detail": (
                        f"{sym} goes ex-div on {d['date']} "
                        f"(${d['amount']:.4f}, in {days_away} day(s)). "
                        "Dividend capture effects can spike the spread near ex-date."
                    ),
                })

    # 7. High short ratio (>5 days to cover = potential squeeze risk)
    for sym, ks in ((s1, ks1), (s2, ks2)):
        sr = ks.get("short_ratio")
        if sr and sr > 5:
            flags.append({
                "level": "warn",
                "title": f"Elevated Short Interest — {sym}",
                "detail": (
                    f"Short ratio is {sr:.1f} days-to-cover. "
                    "A squeeze could cause an outsized move in this leg."
                ),
            })

    return flags


# ---------------------------------------------------------------------------
# Price chart renderer
# ---------------------------------------------------------------------------

def _render_price_chart(
    s1: str,
    s2: str,
    prices1: pd.Series,
    prices2: pd.Series,
    events: dict,
) -> None:
    """Normalised price chart (rebased to 100) with volume bars and event markers."""
    aligned = pd.concat([prices1, prices2], axis=1).dropna()
    if aligned.empty:
        st.info("Insufficient overlapping price data.")
        return

    base1 = aligned[s1].iloc[0]
    base2 = aligned[s2].iloc[0]
    norm1 = aligned[s1] / base1 * 100
    norm2 = aligned[s2] / base2 * 100

    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=norm1.index, y=norm1.values,
        mode="lines", name=s1,
        line=dict(color=C1, width=1.8),
    ))
    fig.add_trace(go.Scatter(
        x=norm2.index, y=norm2.values,
        mode="lines", name=s2,
        line=dict(color=C2, width=1.8),
    ))

    # Spread (right y-axis) — log spread normalised to 0 start
    log_spread = np.log(aligned[s1]) - np.log(aligned[s2])
    log_spread_norm = (log_spread - log_spread.mean()) / (log_spread.std() or 1)
    fig.add_trace(go.Scatter(
        x=log_spread_norm.index,
        y=log_spread_norm.values,
        mode="lines", name="Spread (z-score)",
        line=dict(color="#9467bd", width=1, dash="dot"),
        yaxis="y2",
        opacity=0.7,
    ))

    # Dividend markers
    for sym, color, side in ((s1, CDIV1, "left"), (s2, CDIV2, "right")):
        for d in events[sym]["dividends"]:
            dt = pd.Timestamp(d["date"]).tz_localize("UTC")
            if dt in aligned.index or True:  # add anyway as vline
                fig.add_vline(
                    x=dt.value / 1e6,  # plotly expects ms
                    line=dict(color=color, width=1, dash="dot"),
                    annotation_text=f"${d['amount']:.2f} {sym}",
                    annotation_position=f"top {side}",
                    annotation_font_size=9,
                )

    # Split markers
    for sym in (s1, s2):
        for sp in events[sym]["splits"]:
            dt = pd.Timestamp(sp["date"]).tz_localize("UTC")
            fig.add_vline(
                x=dt.value / 1e6,
                line=dict(color=CSPLIT, width=2),
                annotation_text=f"Split {sp['label']} {sym}",
                annotation_position="top left",
                annotation_font_size=9,
                annotation_font_color=CSPLIT,
            )

    fig.update_layout(
        yaxis=dict(title="Normalised Price (base=100)", side="left"),
        yaxis2=dict(
            title="Spread Z-Score",
            side="right",
            overlaying="y",
            showgrid=False,
            zeroline=True,
            zerolinecolor="#ccc",
        ),
        xaxis_title="Date",
        height=420,
        template="none",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=60, t=30, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
    st.caption(
        "Both prices rebased to 100 at period start.  "
        "Dotted vertical lines = ex-dividend dates.  "
        "Purple solid lines = stock splits.  "
        "Right axis = log-spread z-score."
    )


# ---------------------------------------------------------------------------
# Correlation chart renderer
# ---------------------------------------------------------------------------

def _render_correlation_chart(
    s1: str,
    s2: str,
    prices1: pd.Series,
    prices2: pd.Series,
    registered_corr: Optional[float],
    window: int = 30,
) -> None:
    """Rolling Pearson correlation on hourly log-returns."""
    aligned = pd.concat([prices1, prices2], axis=1).dropna()
    if len(aligned) < window + 5:
        st.info(f"Need at least {window + 5} bars to compute rolling correlation.")
        return

    log_ret = np.log(aligned / aligned.shift(1)).dropna()
    rolling_corr = log_ret[s1].rolling(window).corr(log_ret[s2]).dropna()

    # Stats
    curr_corr = float(rolling_corr.iloc[-1])
    mean_corr = float(rolling_corr.mean())
    min_corr = float(rolling_corr.min())
    pct_below_05 = float((rolling_corr < 0.5).mean() * 100)

    # Metrics row
    mc1, mc2, mc3, mc4 = st.columns(4)
    mc1.metric(
        "Current (last bar)",
        f"{curr_corr:.3f}",
        delta=f"{curr_corr - (registered_corr or 0):+.3f} vs registered"
        if registered_corr else None,
        delta_color="normal",
    )
    mc2.metric("Mean (period)", f"{mean_corr:.3f}")
    mc3.metric("Min (period)", f"{min_corr:.3f}")
    mc4.metric(
        "% Bars Below 0.5",
        f"{pct_below_05:.1f}%",
        help="High % indicates unstable relationship",
    )

    # Chart
    fig = go.Figure()

    # Red shaded danger zone below 0.5
    fig.add_hrect(
        y0=-1, y1=0.5,
        fillcolor="rgba(214,39,40,0.08)",
        line_width=0,
        annotation_text="Weak correlation zone",
        annotation_position="bottom right",
        annotation_font_size=10,
        annotation_font_color=CDANGER,
    )

    fig.add_trace(go.Scatter(
        x=rolling_corr.index,
        y=rolling_corr.values,
        mode="lines",
        name=f"{window}-bar rolling corr",
        line=dict(color=C1, width=1.8),
        fill="tozeroy",
        fillcolor="rgba(31,119,180,0.12)",
    ))

    if registered_corr is not None:
        fig.add_hline(
            y=registered_corr,
            line=dict(color=CPASS, dash="dash", width=1.5),
            annotation_text=f"Registered: {registered_corr:.3f}",
            annotation_position="right",
            annotation_font_color=CPASS,
        )

    fig.add_hline(
        y=0.5,
        line=dict(color=CDANGER, dash="dot", width=1),
        annotation_text="0.5 threshold",
        annotation_position="right",
        annotation_font_color=CDANGER,
        annotation_font_size=10,
    )

    fig.update_layout(
        xaxis_title="Date",
        yaxis_title="Pearson Correlation",
        yaxis=dict(range=[-1, 1]),
        height=360,
        template="none",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=0, r=80, t=30, b=0),
        showlegend=True,
        hovermode="x unified",
    )
    st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)

    # Stability verdict
    if pct_below_05 > 20:
        st.error(
            f"Correlation unstable — {pct_below_05:.0f}% of bars fell below 0.5. "
            "Consider re-running pair discovery with stricter filters."
        )
    elif pct_below_05 > 10:
        st.warning(
            f"{pct_below_05:.0f}% of bars below 0.5 threshold. "
            "Relationship shows periods of weakness."
        )
    else:
        st.success(
            f"Correlation stable — only {pct_below_05:.0f}% of bars below 0.5."
        )


# ---------------------------------------------------------------------------
# Backtest results renderer
# ---------------------------------------------------------------------------

def _render_results(result, metrics, run_id: Optional[int]):
    # Gate verdict banner
    if metrics.passed_gate:
        st.success(
            f"GATE: PASS  |  Sharpe {metrics.sharpe_ratio:.3f}  |  "
            f"Win rate {metrics.win_rate_pct:.1f}%  |  "
            f"Max drawdown {metrics.max_drawdown_pct:.2f}%"
            + (f"  |  run_id={run_id}" if run_id else "")
        )
    else:
        failures = []
        if metrics.sharpe_ratio < metrics.gate_sharpe_threshold:
            failures.append(
                f"Sharpe {metrics.sharpe_ratio:.3f} < {metrics.gate_sharpe_threshold}"
            )
        if metrics.win_rate_pct < metrics.gate_win_rate_threshold:
            failures.append(
                f"Win rate {metrics.win_rate_pct:.1f}% < {metrics.gate_win_rate_threshold}%"
            )
        if metrics.max_drawdown_pct > metrics.gate_drawdown_threshold:
            failures.append(
                f"Drawdown {metrics.max_drawdown_pct:.2f}% > {metrics.gate_drawdown_threshold}%"
            )
        st.error("GATE: FAIL  |  " + "  |  ".join(failures))

    # Key metrics
    st.subheader("Performance Metrics")
    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Total Return", f"{metrics.total_return_pct:+.2f}%")
    c2.metric("Ann. Return", f"{metrics.annualized_return_pct:+.2f}%")
    c3.metric("Sharpe", f"{metrics.sharpe_ratio:.3f}")
    c4.metric("Max Drawdown", f"{metrics.max_drawdown_pct:.2f}%")
    c5.metric("Win Rate", f"{metrics.win_rate_pct:.1f}%")
    c6.metric(
        "Profit Factor",
        f"{metrics.profit_factor:.2f}" if metrics.profit_factor < 999 else "∞",
    )

    c7, c8, c9, c10, c11, c12 = st.columns(6)
    c7.metric("Total Trades", metrics.total_trades)
    c8.metric("Wins / Losses", f"{metrics.winning_trades} / {metrics.losing_trades}")
    c9.metric("Avg Win", f"{metrics.avg_win_pct:+.2f}%")
    c10.metric("Avg Loss", f"-{metrics.avg_loss_pct:.2f}%")
    c11.metric("Avg Hold", f"{metrics.avg_hold_hours:.1f}h")
    c12.metric("Kelly Fraction", f"{metrics.kelly_fraction:.3f}")

    # Equity curve
    st.subheader("Equity Curve")
    if result.equity_curve:
        eq_df = pd.DataFrame(result.equity_curve)
        eq_df["timestamp"] = pd.to_datetime(eq_df["timestamp"])
        eq_df = eq_df.sort_values("timestamp")

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=eq_df["timestamp"],
            y=eq_df["equity"],
            mode="lines",
            name="Portfolio Equity",
            line=dict(color=C1, width=2),
            fill="tozeroy",
            fillcolor="rgba(31,119,180,0.08)",
        ))
        fig.add_hline(
            y=result.initial_capital,
            line_dash="dash",
            line_color="gray",
            annotation_text="Initial Capital",
        )
        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Equity ($)",
            height=380,
            template="none",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=0, r=0, t=30, b=0),
        )
        st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
    else:
        st.info("No equity curve data.")

    # Trade log
    st.subheader("Trade Log")
    if result.trades:
        trade_rows = []
        for t in result.trades:
            trade_rows.append({
                "Side": t.side,
                "Entry": (
                    t.entry_time.strftime("%Y-%m-%d %H:%M") if t.entry_time else ""
                ),
                "Exit": (
                    t.exit_time.strftime("%Y-%m-%d %H:%M") if t.exit_time else ""
                ),
                "Entry Z": f"{t.entry_z:.3f}" if t.entry_z is not None else "",
                "Exit Z": f"{t.exit_z:.3f}" if t.exit_z is not None else "",
                "P&L ($)": round(t.pnl or 0, 2),
                "P&L %": f"{t.pnl_pct:+.2f}%" if t.pnl_pct is not None else "",
                "Hold (h)": f"{t.hold_hours:.1f}" if t.hold_hours is not None else "",
                "Exit Reason": t.exit_reason or "",
            })
        trade_df = pd.DataFrame(trade_rows)

        def _colour_pnl(val):
            try:
                v = float(str(val).replace("%", "").replace("$", "").replace(",", ""))
                return "color: green" if v > 0 else ("color: red" if v < 0 else "")
            except Exception:
                return ""

        styled_trades = trade_df.style.map(
            _colour_pnl, subset=["P&L ($)", "P&L %"]
        )
        st.dataframe(styled_trades, width="stretch", hide_index=True)
    else:
        st.info("No trades generated in this backtest.")


# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

def _fmt_mcap(v) -> str:
    if v is None:
        return "N/A"
    v = float(v)
    if v >= 1e12:
        return f"${v/1e12:.2f}T"
    if v >= 1e9:
        return f"${v/1e9:.2f}B"
    if v >= 1e6:
        return f"${v/1e6:.0f}M"
    return f"${v:,.0f}"


def _mcap_ratio_str(mc1, mc2) -> str:
    if not mc1 or not mc2:
        return "N/A"
    return f"{max(mc1, mc2) / min(mc1, mc2):.1f}×"


def _safe_fmt(value, fmt_fn) -> str:
    if value is None:
        return "—"
    try:
        return fmt_fn(value)
    except Exception:
        return "—"


# ---------------------------------------------------------------------------

if __name__ == "__main__" or True:
    main()
