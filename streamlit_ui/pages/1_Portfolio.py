"""
Portfolio — Positions, Orders, Trades & Order Entry
Real data from Alpaca paper-trading account.
"""

import os
import sys

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from api_client import get_api_client  # noqa: E402

# ── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Portfolio",
    page_icon="💼",
    layout="wide",
)

PLOTLY_CONFIG = {
    "displayModeBar": False,
    "displaylogo": False,
}


# ── CSS ───────────────────────────────────────────────────────────────────────


def load_css() -> None:
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


# ── Formatters ────────────────────────────────────────────────────────────────


def _d(v, decimals: int = 2) -> str:
    try:
        return f"${float(v):,.{decimals}f}"
    except Exception:
        return "—"


def _pct(v, decimals: int = 2) -> str:
    try:
        f = float(v) * 100
        sign = "+" if f >= 0 else ""
        return f"{sign}{f:.{decimals}f}%"
    except Exception:
        return "—"


def _pct_raw(v, decimals: int = 2) -> str:
    """Percentage already in % units (not decimal)."""
    try:
        f = float(v)
        sign = "+" if f >= 0 else ""
        return f"{sign}{f:.{decimals}f}%"
    except Exception:
        return "—"


def _pnl_color(v) -> str:
    try:
        return "#2A7A4B" if float(v) >= 0 else "#C0392B"
    except Exception:
        return "#6b6b6b"


def _fmt_dt(s: str) -> str:
    if not s:
        return "—"
    return s[:16].replace("T", " ")


# ── Allocation pie ────────────────────────────────────────────────────────────


def render_allocation(positions: list) -> None:
    if not positions:
        st.markdown(
            "<p style='color:#9e9e9e;font-size:0.88rem;'>No positions to chart.</p>",
            unsafe_allow_html=True,
        )
        return

    labels = [p.get("symbol", "") for p in positions]
    values = [abs(float(p.get("market_value", 0))) for p in positions]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=labels,
                values=values,
                hole=0.42,
                textinfo="label+percent",
                hovertemplate="<b>%{label}</b><br>$%{value:,.2f}<extra></extra>",
                marker=dict(
                    colors=[
                        "#1a1a1a",
                        "#6b6b6b",
                        "#9e9e9e",
                        "#c8c8c8",
                        "#e0e0dc",
                        "#2A7A4B",
                        "#C0392B",
                        "#D97706",
                    ],
                ),
            )
        ]
    )
    fig.update_layout(
        margin=dict(t=10, b=10, l=10, r=10),
        height=280,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        showlegend=True,
        legend=dict(
            font=dict(family="DM Sans", size=11, color="#6b6b6b"),
            bgcolor="rgba(0,0,0,0)",
        ),
    )
    st.plotly_chart(fig, config=PLOTLY_CONFIG)


# ── Positions table ───────────────────────────────────────────────────────────


def render_positions(positions: list, api) -> None:
    st.markdown("<h2>Positions</h2>", unsafe_allow_html=True)

    if not positions:
        st.markdown(
            "<p style='color:#9e9e9e;font-size:0.88rem;padding:0.6rem 0;'>"
            "No open positions.</p>",
            unsafe_allow_html=True,
        )
        return

    # Build display rows
    rows = []
    for p in positions:
        unrl = float(p.get("unrealized_pl", 0))
        unrl_pct = float(p.get("unrealized_plpc", 0)) * 100
        intraday_pct = float(p.get("unrealized_intraday_plpc", 0)) * 100
        rows.append(
            {
                "Symbol": p.get("symbol", ""),
                "Side": p.get("side", "").upper(),
                "Qty": int(float(p.get("qty", 0))),
                "Avg Entry": _d(p.get("avg_entry_price", 0)),
                "Price": _d(p.get("current_price", 0)),
                "Mkt Value": _d(p.get("market_value", 0)),
                "Unrlzd P&L": (
                    f"{'+'if unrl >= 0 else ''}{_d(unrl)}"
                    f" ({'+'if unrl_pct >= 0 else ''}{unrl_pct:.2f}%)"
                ),
                "Today": _pct_raw(intraday_pct),
            }
        )

    df = pd.DataFrame(rows)
    st.dataframe(df, width="stretch", hide_index=True)

    # Per-position close buttons
    st.markdown("<h3>Close a Position</h3>", unsafe_allow_html=True)
    syms = [p.get("symbol", "") for p in positions]
    col1, col2 = st.columns([2, 1])
    with col1:
        selected = st.selectbox("Select symbol", syms, key="close_sym_select")
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("Close Position", key="close_pos_btn", type="primary"):
            st.session_state["_confirm_close"] = selected

    if st.session_state.get("_confirm_close"):
        sym = st.session_state["_confirm_close"]
        st.warning(
            f"Close **all shares** of **{sym}**? This will submit a market sell order."
        )
        c1, c2, _ = st.columns([1, 1, 4])
        with c1:
            if st.button("Confirm", key="confirm_close_yes"):
                result = api.close_position(sym)
                if "error" not in str(result):
                    st.success(f"Close order submitted for {sym}.")
                else:
                    st.error(f"Error: {result}")
                del st.session_state["_confirm_close"]
                st.rerun()
        with c2:
            if st.button("Cancel", key="confirm_close_no"):
                del st.session_state["_confirm_close"]
                st.rerun()


# ── Open orders ───────────────────────────────────────────────────────────────


def render_orders(orders: list, api) -> None:
    if not orders:
        st.info("No open orders.")
        return

    rows = []
    for o in orders:
        rows.append(
            {
                "Symbol": o.get("symbol", ""),
                "Side": (o.get("side") or "").upper(),
                "Type": o.get("order_type") or o.get("type", ""),
                "Qty": o.get("qty", ""),
                "Limit $": _d(o["limit_price"]) if o.get("limit_price") else "—",
                "Status": o.get("status", ""),
                "Submitted": _fmt_dt(o.get("submitted_at", "")),
                "ID": o.get("id", ""),
            }
        )

    df = pd.DataFrame(rows)
    display_df = df.drop(columns=["ID"])
    st.dataframe(display_df, width="stretch", hide_index=True)

    st.markdown("<h3>Cancel an Order</h3>", unsafe_allow_html=True)
    order_options = {
        f"{o.get('symbol')} {(o.get('side') or '').upper()} {o.get('qty')} "
        f"({o.get('id', '')[:8]})": o.get("id", "")
        for o in orders
    }
    if order_options:
        selected_label = st.selectbox(
            "Select order", list(order_options.keys()), key="cancel_order_sel"
        )
        if st.button("Cancel Order", key="cancel_order_btn"):
            oid = order_options[selected_label]
            result = api.cancel_order(oid)
            if "error" not in str(result):
                st.success("Order cancelled.")
                st.rerun()
            else:
                st.error(f"Error: {result}")


# ── Recent trades ─────────────────────────────────────────────────────────────


def render_trades(trades: list) -> None:
    if not trades:
        st.info("No recent trades.")
        return

    rows = []
    for t in trades:
        rows.append(
            {
                "Symbol": t.get("symbol", ""),
                "Side": (t.get("side") or "").upper(),
                "Qty": t.get("filled_qty") or t.get("qty", ""),
                "Fill Price": _d(t.get("filled_avg_price", 0)),
                "Type": t.get("order_type") or t.get("type", ""),
                "Filled At": _fmt_dt(t.get("filled_at", "")),
            }
        )

    df = pd.DataFrame(rows)
    st.dataframe(df, width="stretch", hide_index=True)


# ── Place order form ──────────────────────────────────────────────────────────


def render_place_order(api) -> None:
    with st.form("place_order_form", clear_on_submit=True):
        c1, c2, c3 = st.columns(3)
        with c1:
            symbol = st.text_input("Symbol", placeholder="e.g. AAPL").upper().strip()
            side = st.selectbox("Side", ["buy", "sell"])
        with c2:
            qty = st.number_input("Quantity (shares)", min_value=1, value=1, step=1)
            order_type = st.selectbox("Order Type", ["market", "limit"])
        with c3:
            limit_price = None
            if order_type == "limit":
                limit_price = st.number_input(
                    "Limit Price ($)", min_value=0.01, value=100.0, step=0.01
                )
            else:
                st.markdown(
                    "<div style='padding-top:1.4rem;color:#9e9e9e;"
                    "font-size:0.82rem;'>Fill at market price</div>",
                    unsafe_allow_html=True,
                )

        submitted = st.form_submit_button("Submit Order", type="primary")

    if submitted:
        if not symbol:
            st.error("Symbol is required.")
        else:
            result = api.place_order(
                symbol=symbol,
                qty=int(qty),
                side=side,
                order_type=order_type,
                limit_price=limit_price if order_type == "limit" else None,
            )
            if "error" not in str(result).lower():
                st.success(
                    f"Order submitted: {side.upper()} {qty} {symbol}"
                    f"{' @ $'+str(limit_price) if limit_price else ' (market)'}."
                )
            else:
                st.error(f"Order failed: {result}")


# ── Main ──────────────────────────────────────────────────────────────────────


def main() -> None:
    load_css()

    api = get_api_client()

    account = api.get_alpaca_account()
    positions = api.get_alpaca_positions()
    orders = api.get_alpaca_orders(status="open")
    trades = api.get_alpaca_trades(limit=20)

    # ── Page title ──
    st.markdown("<h1>Portfolio</h1>", unsafe_allow_html=True)

    # ── Account summary ──
    if "error" not in account:
        equity = float(account.get("equity", 0))
        last_equity = float(account.get("last_equity", equity))
        day_pnl = equity - last_equity
        day_pct = (day_pnl / last_equity * 100) if last_equity else 0
        long_mv = float(account.get("long_market_value", 0))

        c1, c2, c3, c4, c5 = st.columns(5)
        c1.metric("Equity", _d(equity))
        c2.metric("Cash", _d(account.get("cash", 0)))
        c3.metric("Buying Power", _d(account.get("buying_power", 0)))
        c4.metric("Long Mkt Value", _d(long_mv))
        sign = "+" if day_pnl >= 0 else ""
        c5.metric(
            "Today's P&L",
            _d(day_pnl),
            f"{sign}{day_pct:.2f}%",
        )
    else:
        st.error("Cannot reach API — is it running on port 8001?")

    st.markdown("---")

    # ── Positions + allocation side by side ──
    pos_col, pie_col = st.columns([3, 1])
    with pos_col:
        render_positions(positions, api)
    with pie_col:
        st.markdown("<h2>Allocation</h2>", unsafe_allow_html=True)
        render_allocation(positions)

    st.markdown("---")

    # ── Tabs: orders / trades / place order ──
    tab_orders, tab_trades, tab_new = st.tabs(
        ["Open Orders", "Recent Trades", "Place Order"]
    )

    with tab_orders:
        render_orders(orders, api)

    with tab_trades:
        render_trades(trades)

    with tab_new:
        render_place_order(api)

    # ── Refresh ──
    st.markdown("---")
    if st.button("↻ Refresh", key="portfolio_refresh"):
        st.cache_data.clear()
        st.rerun()


if __name__ == "__main__":
    main()
