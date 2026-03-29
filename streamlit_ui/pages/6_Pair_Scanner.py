"""
Pair Scanner — Backtest All Pairs & Rank by Performance

Runs a backtest on every registered pair using the last 180 days of data,
then displays results sorted by Sharpe ratio (best first) with gate PASS/FAIL
status and inline activate/deactivate controls.

Gate criteria (all must pass):
    Sharpe ratio  > 0.5
    Win rate      > 45%
    Max drawdown  < 15%
"""

import json
import os
import sys
from datetime import date, timedelta
from typing import List, Optional

import streamlit as st

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.services.strategy_engine.backtesting.engine import BacktestEngine  # noqa: E402
from src.services.strategy_engine.backtesting.metrics import (  # noqa: E402
    MetricsCalculator,
)
from src.shared.database.base import db_readonly_session, db_transaction  # noqa: E402
from src.shared.database.models.strategy_models import PairRegistry  # noqa: E402

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Pair Scanner",
    page_icon="🔍",
    layout="wide",
)

GATE_SHARPE = 0.5
GATE_WIN_RATE = 45.0
GATE_DRAWDOWN = 15.0

COLOR_PASS = "#2A7A4B"
COLOR_FAIL = "#C0392B"
COLOR_ACTIVE = "#1f77b4"

_PREFS_FILE = os.path.join(
    os.path.dirname(__file__), "..", "..", "config", "scanner_prefs.json"
)
_PREFS_DEFAULTS = {"lookback_days": 180, "slippage_bps": 5}


def _load_prefs() -> dict:
    try:
        with open(_PREFS_FILE) as f:
            data = json.load(f)
        # Ensure all keys present (handles old prefs files missing new keys)
        return {**_PREFS_DEFAULTS, **data}
    except Exception:
        return dict(_PREFS_DEFAULTS)


def _save_prefs(lookback_days: int, slippage_bps: int) -> None:
    try:
        os.makedirs(os.path.dirname(_PREFS_FILE), exist_ok=True)
        with open(_PREFS_FILE, "w") as f:
            json.dump({"lookback_days": lookback_days, "slippage_bps": slippage_bps}, f)
    except Exception:
        pass


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
# Data helpers
# ---------------------------------------------------------------------------


@st.cache_data(ttl=300)
def _load_all_pairs() -> list:
    """Return all PairRegistry rows as plain dicts."""
    try:
        with db_readonly_session() as session:
            pairs = session.query(PairRegistry).order_by(PairRegistry.id).all()
            return [
                {
                    "id": p.id,
                    "symbol1": p.symbol1,
                    "symbol2": p.symbol2,
                    "sector": p.sector or "—",
                    "hedge_ratio": float(p.hedge_ratio),
                    "z_score_window": int(p.z_score_window),
                    "entry_threshold": float(p.entry_threshold),
                    "exit_threshold": float(p.exit_threshold),
                    "stop_loss_threshold": float(p.stop_loss_threshold),
                    "max_hold_hours": (
                        float(p.max_hold_hours) if p.max_hold_hours else 48.0
                    ),
                    "rank_score": float(p.rank_score) if p.rank_score else 0.0,
                    "is_active": bool(p.is_active),
                }
                for p in pairs
            ]
    except Exception as e:
        st.error(f"Failed to load pairs: {e}")
        return []


def _set_pair_active(pair_id: int, active: bool) -> None:
    """Toggle is_active on a pair_registry row."""
    with db_transaction() as session:
        pair = session.query(PairRegistry).filter_by(id=pair_id).first()
        if pair:
            pair.is_active = active


def _run_backtest_for_pair(
    pair_dict: dict, start: date, end: date, slippage_bps: float
) -> Optional[dict]:
    """
    Run a BacktestEngine for a single pair dict and return a result summary dict,
    or None if insufficient data.
    """

    # Build a minimal mock-compatible object from the dict
    class _PairProxy:
        def __init__(self, d: dict) -> None:
            self.id = d["id"]
            self.symbol1 = d["symbol1"]
            self.symbol2 = d["symbol2"]
            self.hedge_ratio = d["hedge_ratio"]
            self.z_score_window = d["z_score_window"]
            self.entry_threshold = d["entry_threshold"]
            self.exit_threshold = d["exit_threshold"]
            self.stop_loss_threshold = d["stop_loss_threshold"]
            self.max_hold_hours = d["max_hold_hours"]

    try:
        engine = BacktestEngine(
            pair=_PairProxy(pair_dict),  # type: ignore[arg-type]
            start_date=start,
            end_date=end,
            initial_capital=100_000.0,
            slippage_bps=slippage_bps,
            commission_per_trade=0.0,
        )
        result = engine.run()

        if not result.trades:
            return None

        calc = MetricsCalculator()
        m = calc.compute(result)

        return {
            "id": pair_dict["id"],
            "pair": f"{pair_dict['symbol1']}/{pair_dict['symbol2']}",
            "sector": pair_dict["sector"],
            "rank_score": pair_dict["rank_score"],
            "sharpe": m.sharpe_ratio,
            "win_rate": m.win_rate_pct,
            "max_dd": m.max_drawdown_pct,
            "total_trades": m.total_trades,
            "total_return": m.total_return_pct,
            "passed": m.passed_gate,
            "is_active": pair_dict["is_active"],
        }
    except Exception as e:
        return {
            "id": pair_dict["id"],
            "pair": f"{pair_dict['symbol1']}/{pair_dict['symbol2']}",
            "sector": pair_dict["sector"],
            "rank_score": pair_dict["rank_score"],
            "sharpe": None,
            "win_rate": None,
            "max_dd": None,
            "total_trades": 0,
            "total_return": None,
            "passed": False,
            "is_active": pair_dict["is_active"],
            "error": str(e),
        }


# ---------------------------------------------------------------------------
# Main page
# ---------------------------------------------------------------------------


def main() -> None:
    _load_css()
    st.title("Pair Scanner")
    st.caption(
        "Backtest every registered pair and rank by Sharpe ratio. "
        "Activate passing pairs to include them in live trading."
    )

    pairs = _load_all_pairs()
    if not pairs:
        st.warning("No pairs registered. Run `scripts/discover_pairs.py` first.")
        return

    prefs = _load_prefs()

    # --- Scan parameters ---
    with st.expander("Scan Parameters", expanded=False):
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            lookback_days = st.slider(
                "Lookback (days)",
                90,
                365,
                prefs["lookback_days"],
                30,
                key="scanner_lookback",
            )
        with col_b:
            slippage_bps = st.slider(
                "Slippage (bps/fill)",
                0,
                20,
                prefs["slippage_bps"],
                1,
                key="scanner_slippage",
            )
        with col_c:
            st.metric("Pairs to scan", len(pairs))

    end_date = date.today()
    start_date = end_date - timedelta(days=lookback_days)

    # --- Run scan ---
    if st.button("Run Scan", type="primary", use_container_width=False):
        _save_prefs(int(lookback_days), int(slippage_bps))
        results: list = []
        progress = st.progress(0, text="Scanning pairs…")

        for i, pair in enumerate(pairs):
            progress.progress(
                (i + 1) / len(pairs),
                text=f"Scanning {pair['symbol1']}/{pair['symbol2']} ({i+1}/{len(pairs)})…",
            )
            r = _run_backtest_for_pair(pair, start_date, end_date, float(slippage_bps))
            if r is not None:
                results.append(r)

        progress.empty()

        if not results:
            st.warning(
                "No results — check that market data is loaded for the date range."
            )
            return

        # Sort: PASS first, then by Sharpe descending; FAILs sorted by Sharpe desc too
        results.sort(
            key=lambda r: (
                not r["passed"],
                -(r["sharpe"] if r["sharpe"] is not None else -999),
            )
        )

        st.session_state["scanner_results"] = results
        st.session_state["scanner_params"] = {
            "start": start_date.isoformat(),
            "end": end_date.isoformat(),
            "slippage_bps": slippage_bps,
        }

    # --- Display results ---
    if "scanner_results" not in st.session_state:
        st.info(
            "Configure parameters above and click **Run Scan** to evaluate all pairs."
        )
        return

    results = st.session_state["scanner_results"]
    params = st.session_state["scanner_params"]

    passing = [r for r in results if r["passed"]]
    failing = [r for r in results if not r["passed"]]

    st.markdown(
        f"**Scan period:** {params['start']} → {params['end']}  ·  "
        f"**Slippage:** {params['slippage_bps']} bps  ·  "
        f"**{len(passing)} PASS** / {len(failing)} FAIL  ·  "
        f"{sum(1 for r in results if r['is_active'])} currently active"
    )

    # Summary metrics row
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Pairs Scanned", len(results))
    m2.metric("Passing Gate", len(passing))
    m3.metric(
        "Best Sharpe",
        f"{results[0]['sharpe']:.3f}" if results[0]["sharpe"] is not None else "—",
        results[0]["pair"],
    )
    active_passing = sum(1 for r in passing if r["is_active"])
    m4.metric("Active & Passing", active_passing)

    st.divider()

    # --- Results table with inline controls ---
    _render_results_table(results)


def _render_results_table(results: list) -> None:
    """Render one row per pair with metrics and activate/deactivate button."""
    # Header row
    hcols = st.columns([0.5, 2.0, 1.5, 0.9, 0.9, 0.9, 0.7, 1.0, 1.2, 1.2])
    headers = [
        "#",
        "Pair",
        "Sector",
        "Sharpe",
        "Win Rate",
        "Max DD",
        "Trades",
        "Return",
        "Gate",
        "Action",
    ]
    for col, h in zip(hcols, headers):
        col.markdown(f"**{h}**")

    st.markdown("<hr style='margin:4px 0'>", unsafe_allow_html=True)

    for i, r in enumerate(results):
        cols = st.columns([0.5, 2.0, 1.5, 0.9, 0.9, 0.9, 0.7, 1.0, 1.2, 1.2])

        gate_color = COLOR_PASS if r["passed"] else COLOR_FAIL
        gate_label = "✓ PASS" if r["passed"] else "✗ FAIL"
        active_badge = " 🔵" if r["is_active"] else ""

        sharpe_str = f"{r['sharpe']:.3f}" if r["sharpe"] is not None else "—"
        win_str = f"{r['win_rate']:.1f}%" if r["win_rate"] is not None else "—"
        dd_str = f"{r['max_dd']:.2f}%" if r["max_dd"] is not None else "—"
        ret_str = f"{r['total_return']:.2f}%" if r["total_return"] is not None else "—"

        # Colour-code individual metric cells that fail their gate
        sharpe_color = (
            "" if r["sharpe"] is None or r["sharpe"] >= GATE_SHARPE else COLOR_FAIL
        )
        win_color = (
            ""
            if r["win_rate"] is None or r["win_rate"] >= GATE_WIN_RATE
            else COLOR_FAIL
        )
        dd_color = (
            "" if r["max_dd"] is None or r["max_dd"] < GATE_DRAWDOWN else COLOR_FAIL
        )

        def _colored(text: str, color: str) -> str:
            if color:
                return f'<span style="color:{color}">{text}</span>'
            return text

        cols[0].write(i + 1)
        cols[1].markdown(f"**{r['pair']}**{active_badge}")
        cols[2].write(r["sector"])
        cols[3].markdown(_colored(sharpe_str, sharpe_color), unsafe_allow_html=True)
        cols[4].markdown(_colored(win_str, win_color), unsafe_allow_html=True)
        cols[5].markdown(_colored(dd_str, dd_color), unsafe_allow_html=True)
        cols[6].write(r["total_trades"])
        cols[7].write(ret_str)
        cols[8].markdown(
            f'<span style="color:{gate_color};font-weight:bold">{gate_label}</span>',
            unsafe_allow_html=True,
        )

        # Action button
        if r["is_active"]:
            if cols[9].button(
                "Deactivate", key=f"deact_{r['id']}", use_container_width=True
            ):
                _set_pair_active(r["id"], False)
                r["is_active"] = False
                st.rerun()
        else:
            btn_label = "Activate" if r["passed"] else "Activate ⚠"
            if cols[9].button(
                btn_label,
                key=f"act_{r['id']}",
                type="primary" if r["passed"] else "secondary",
                use_container_width=True,
            ):
                _set_pair_active(r["id"], True)
                r["is_active"] = True
                st.rerun()

    st.markdown("<hr style='margin:4px 0'>", unsafe_allow_html=True)
    st.caption("🔵 = currently active  ·  ⚠ = activating a failing pair")


main()
