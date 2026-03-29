"""
Pairs Trading — Live Monitoring Page

Displays real-time strategy status, active pair positions,
z-score charts, recent trades, and performance summary.

All data fetched from the FastAPI server via TradingSystemAPI.
"""

import os
import sys
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from api_client import TradingSystemAPI
from utils import render_market_banner

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Pairs Trading",
    page_icon="⚖️",
    layout="wide",
)

PLOTLY_CONFIG = {
    "displayModeBar": True,
    "displaylogo": False,
    "modeBarButtonsToRemove": ["pan2d", "lasso2d", "select2d"],
}

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8001")
api = TradingSystemAPI(base_url=API_BASE)


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


@st.cache_data(ttl=30)
def fetch_status():
    return api._make_request("GET", "/api/strategies/pairs/status")


@st.cache_data(ttl=30)
def fetch_active_pairs():
    data = api._make_request("GET", "/api/strategies/pairs/active")
    return data.get("pairs", [])


@st.cache_data(ttl=60)
def fetch_performance():
    return api._make_request("GET", "/api/strategies/pairs/performance")


@st.cache_data(ttl=30)
def fetch_pair_history(pair_id: int, days: int = 30):
    return api._make_request(
        "GET", f"/api/strategies/pairs/{pair_id}/history?days={days}"
    )


@st.cache_data(ttl=30)
def fetch_pair_details(pair_id: int):
    return api._make_request("GET", f"/api/strategies/pairs/{pair_id}/details")


@st.cache_data(ttl=30)
def fetch_risk_state():
    return api._make_request("GET", "/api/strategies/pairs/risk")


@st.cache_data(ttl=60)
def fetch_market_clock():
    return api._make_request("GET", "/clock")


@st.cache_data(ttl=60)
def fetch_pair_sparkline(pair_id: int, points: int = 48):
    return api._make_request(
        "GET", f"/api/strategies/pairs/{pair_id}/sparkline?points={points}"
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def _render_sparkline(z_values: list, entry_thr: float = 2.0) -> go.Figure:
    """Return a compact Plotly sparkline figure for a z-score series."""
    colours = [
        "red" if abs(z) > entry_thr else ("orange" if abs(z) > 1.5 else "#1f77b4")
        for z in z_values
    ]
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            y=z_values,
            mode="lines",
            line=dict(color="#1f77b4", width=1.5),
            showlegend=False,
            hovertemplate="z=%{y:.2f}<extra></extra>",
        )
    )
    # shade the last point
    if z_values:
        fig.add_trace(
            go.Scatter(
                x=[len(z_values) - 1],
                y=[z_values[-1]],
                mode="markers",
                marker=dict(color=colours[-1], size=6),
                showlegend=False,
                hoverinfo="skip",
            )
        )
    for level, color, dash in [
        (entry_thr, "rgba(255,60,60,0.5)", "dot"),
        (-entry_thr, "rgba(255,60,60,0.5)", "dot"),
        (0, "rgba(150,150,150,0.4)", "dot"),
    ]:
        fig.add_hline(y=level, line_color=color, line_dash=dash, line_width=1)
    fig.update_layout(
        height=70,
        margin=dict(l=0, r=0, t=4, b=4),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    return fig


def main():
    _load_css()
    st.title("Pairs Trading — Live Monitoring")

    clock = fetch_market_clock()
    if "error" not in clock:
        render_market_banner(clock)

    # ---- Strategy Status Bar ----
    status = fetch_status()
    if "error" not in status:
        is_active = status.get("is_active", False)
        last_update = status.get("last_update", "—")

        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric(
            "Strategy",
            "Active" if is_active else "Inactive",
        )
        col2.metric("Total Pairs", status.get("total_pairs", 0))
        col3.metric("Active Pairs", status.get("active_pairs", 0))
        col4.metric("Total P&L", f"${status.get('total_pnl', 0):,.2f}")
        col5.metric("Last Update", _fmt_time(last_update))

        # Control buttons
        bcol1, bcol2, bcol3, _ = st.columns([1, 1, 1, 5])
        with bcol1:
            if st.button("Start Strategy", type="primary"):
                r = api._make_request("POST", "/api/strategies/pairs/start")
                st.success(r.get("message", "Started"))
                st.cache_data.clear()
        with bcol2:
            if st.button("Stop Strategy"):
                r = api._make_request("POST", "/api/strategies/pairs/stop")
                st.info(r.get("message", "Stopped"))
                st.cache_data.clear()
        with bcol3:
            if st.button("Emergency Stop", type="secondary"):
                if st.session_state.get("confirm_estop"):
                    r = api._make_request(
                        "POST", "/api/strategies/pairs/emergency-stop"
                    )
                    st.error(r.get("message", "Emergency stop sent"))
                    st.session_state["confirm_estop"] = False
                    st.cache_data.clear()
                else:
                    st.session_state["confirm_estop"] = True
                    st.warning("Click again to confirm emergency stop")
    else:
        st.error("Could not reach API server. Is FastAPI running on port 8001?")

    # ---- Risk Controls Banner ----
    risk = fetch_risk_state()
    if "error" not in risk:
        cb_active = risk.get("circuit_breaker_active", False)
        peak = risk.get("peak_equity")
        threshold = risk.get("drawdown_threshold", 0.05)
        triggered_at = risk.get("circuit_breaker_triggered_at")

        if cb_active:
            st.error(
                f"Circuit Breaker ACTIVE — all new entries blocked. "
                f"Triggered: {triggered_at or 'unknown'}"
            )

        with st.expander("Risk Controls", expanded=cb_active):
            rc1, rc2, rc3, rc4 = st.columns(4)
            rc1.metric(
                "Circuit Breaker",
                "ACTIVE" if cb_active else "CLEAR",
            )
            rc2.metric(
                "Peak Equity",
                f"${peak:,.2f}" if peak else "—",
            )
            rc3.metric(
                "Drawdown Threshold",
                f"{threshold * 100:.1f}%",
            )
            with rc4:
                if cb_active:
                    if st.button("Reset Circuit Breaker", type="primary"):
                        api._make_request(
                            "POST",
                            "/api/strategies/pairs/risk/reset-circuit-breaker",
                        )
                        st.success("Circuit breaker reset")
                        st.cache_data.clear()
                new_threshold = st.number_input(
                    "Update threshold (%)",
                    min_value=1.0,
                    max_value=50.0,
                    value=float(threshold * 100),
                    step=0.5,
                    key="risk_threshold_input",
                )
                if st.button("Save Threshold"):
                    api._make_request(
                        "PUT",
                        "/api/strategies/pairs/risk/threshold",
                        json={"threshold": new_threshold / 100},
                    )
                    st.success(f"Threshold updated to {new_threshold:.1f}%")
                    st.cache_data.clear()

    st.divider()

    # ---- Active Pairs Grid ----
    st.subheader("Active Pairs")
    pairs = fetch_active_pairs()

    if not pairs:
        st.info(
            "No active pairs found. Run `scripts/discover_pairs.py` and register pairs."
        )
        return

    # Column headers
    h1, h2, h3, h4, h5 = st.columns([2, 1, 1, 1, 3])
    h1.markdown("**Pair**")
    h2.markdown("**Status**")
    h3.markdown("**Z-Score**")
    h4.markdown("**Unrealized P&L**")
    h5.markdown("**Z-Score (last 48 pts)**")
    st.divider()

    for p in pairs:
        pair_id = int(p["id"])
        z = p.get("z_score")
        pnl = p.get("pnl", 0.0)

        # P&L delta vs previous load
        prev_key = f"prev_pnl_{pair_id}"
        prev_pnl = st.session_state.get(prev_key)
        pnl_delta = pnl - prev_pnl if prev_pnl is not None else None
        st.session_state[prev_key] = pnl

        # Z-score colour label
        if z is None:
            z_label = "—"
            z_color = ""
        elif abs(z) > 2.0:
            z_label = f"**:red[{z:.3f}]**"
            z_color = "red"
        elif abs(z) > 1.5:
            z_label = f"**:orange[{z:.3f}]**"
            z_color = "orange"
        else:
            z_label = f"{z:.3f}"
            z_color = ""

        status_icon = "🔵" if p["status"] == "in_trade" else "⚪"

        c1, c2, c3, c4, c5 = st.columns([2, 1, 1, 1, 3])
        c1.markdown(
            f"**{p['name']}**  \n<small>corr {p.get('correlation', 0):.3f} · {p.get('days_held') or 0}d held</small>",
            unsafe_allow_html=True,
        )
        c2.markdown(f"{status_icon} {p['status']}")
        c3.markdown(z_label)
        c4.metric(
            label="P&L",
            value=f"${pnl:,.2f}",
            delta=f"${pnl_delta:+,.2f}" if pnl_delta is not None else None,
            delta_color="normal",
        )

        spark_data = fetch_pair_sparkline(pair_id)
        if "error" not in spark_data:
            pts = spark_data.get("data", [])
            if pts:
                z_vals = [d["z"] for d in pts]
                spark_fig = _render_sparkline(z_vals)
                c5.plotly_chart(
                    spark_fig,
                    use_container_width=True,
                    config={"displayModeBar": False},
                )
            else:
                c5.caption("No spread data yet")
        else:
            c5.caption("—")

    st.divider()

    # ---- Z-Score Chart for selected pair ----
    st.subheader("Z-Score Chart")
    pair_names = [p["name"] for p in pairs]
    selected_name = st.selectbox("Select pair", pair_names)
    selected = next(p for p in pairs if p["name"] == selected_name)
    pair_id = int(selected["id"])

    days = st.slider("History (days)", 7, 90, 30)
    history_data = fetch_pair_history(pair_id, days)

    if "error" not in history_data:
        history = history_data.get("history", [])
        entry_thr = history_data.get("entry_threshold", 2.0)
        exit_thr = history_data.get("exit_threshold", 0.5)

        if history:
            hist_df = pd.DataFrame(history)
            hist_df["timestamp"] = pd.to_datetime(hist_df["timestamp"], unit="ms")
            hist_df = hist_df.dropna(subset=["z_score"])

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(
                    x=hist_df["timestamp"],
                    y=hist_df["z_score"],
                    mode="lines",
                    name="Z-Score",
                    line=dict(color="#1f77b4", width=1.5),
                )
            )
            for level, color, dash, label in [
                (entry_thr, "red", "dash", f"+{entry_thr} Entry"),
                (-entry_thr, "red", "dash", f"-{entry_thr} Entry"),
                (exit_thr, "green", "dot", f"+{exit_thr} Exit"),
                (-exit_thr, "green", "dot", f"-{exit_thr} Exit"),
                (0, "gray", "dot", "Zero"),
            ]:
                fig.add_hline(
                    y=level,
                    line_color=color,
                    line_dash=dash,
                    annotation_text=label,
                    annotation_position="right",
                )

            fig.update_layout(
                xaxis_title="Date",
                yaxis_title="Z-Score",
                height=360,
                template="none",
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=0, r=60, t=30, b=0),
                legend=dict(orientation="h"),
            )
            st.plotly_chart(fig, use_container_width=True, config=PLOTLY_CONFIG)
        else:
            st.info("No spread history yet. Strategy must run at least one cycle.")

    st.divider()

    # ---- Performance Summary ----
    st.subheader("Performance Summary")
    perf = fetch_performance()

    if "error" not in perf:
        pc1, pc2, pc3, pc4, pc5 = st.columns(5)
        pc1.metric("Total P&L", f"${perf.get('total_pnl', 0):,.2f}")
        pc2.metric("Sharpe Ratio", f"{perf.get('sharpe_ratio', 0):.3f}")
        pc3.metric("Max Drawdown", f"{perf.get('max_drawdown', 0):.2f}%")
        pc4.metric("Win Rate", f"{perf.get('win_rate', 0)*100:.1f}%")
        pc5.metric("Avg Hold Time", f"{perf.get('avg_hold_time', 0):.1f}h")

    st.divider()

    # ---- Pair details panel ----
    with st.expander(f"Pair Details — {selected_name}"):
        details = fetch_pair_details(pair_id)
        if "error" not in details:
            dc1, dc2, dc3, dc4 = st.columns(4)
            dc1.metric("Hedge Ratio", f"{details.get('hedge_ratio', 0):.4f}")
            dc2.metric("Half-Life", f"{details.get('half_life', '—')}h")
            dc3.metric(
                "Cointegration p", f"{details.get('cointegration_pvalue', 0):.4f}"
            )
            dc4.metric("Correlation", f"{details.get('correlation', 0):.3f}")

            open_trade = details.get("open_trade")
            if open_trade:
                st.markdown("**Open Trade**")
                st.json(open_trade)

            last_sig = details.get("last_signal")
            if last_sig:
                st.markdown(
                    f"**Last Signal:** `{last_sig.get('type')}` "
                    f"z={last_sig.get('z_score', 0):.3f}  "
                    f"@ {last_sig.get('timestamp', '')}"
                )


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fmt_time(ts_str):
    try:
        dt = datetime.fromisoformat(str(ts_str).replace("Z", "+00:00"))
        return dt.strftime("%H:%M:%S")
    except Exception:
        return str(ts_str)[:19] if ts_str else "—"


# ---------------------------------------------------------------------------

if __name__ == "__main__" or True:
    main()
