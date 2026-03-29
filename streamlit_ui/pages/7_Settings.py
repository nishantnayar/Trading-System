"""
Settings — System Configuration
API connection status and analysis preferences.
"""

import json
import os
import sys
from datetime import datetime

import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from api_client import get_api_client  # noqa: E402

_PREFS_FILE = os.path.join(
    os.path.dirname(__file__), "..", "..", "config", "analysis_prefs.json"
)
_PREFS_DEFAULTS = {"symbol": "AAPL", "timeframe": "1M"}


def _load_prefs() -> dict:
    try:
        with open(_PREFS_FILE) as f:
            data = json.load(f)
        return {**_PREFS_DEFAULTS, **data}
    except Exception:
        return dict(_PREFS_DEFAULTS)


def _save_prefs(symbol: str, timeframe: str) -> None:
    try:
        os.makedirs(os.path.dirname(_PREFS_FILE), exist_ok=True)
        with open(_PREFS_FILE, "w") as f:
            json.dump({"symbol": symbol, "timeframe": timeframe}, f)
    except Exception:
        pass


st.set_page_config(
    page_title="Settings",
    page_icon="⚙️",
    layout="wide",
)


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


def _status_badge(ok: bool, ok_label: str, fail_label: str) -> str:
    if ok:
        return (
            f'<span style=\'color:#2A7A4B;font-family:"DM Sans",sans-serif;'
            f"font-weight:500;'>{ok_label}</span>"
        )
    return (
        f'<span style=\'color:#C0392B;font-family:"DM Sans",sans-serif;'
        f"font-weight:500;'>{fail_label}</span>"
    )


def main() -> None:
    load_css()

    st.markdown("<h1>Settings</h1>", unsafe_allow_html=True)

    api = get_api_client()

    # ── Section 1: Connection Status ──────────────────────────────────────────
    st.markdown("<h2>Connection Status</h2>", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)

    with c1:
        health = api.health_check()
        api_ok = "error" not in health
        st.markdown(
            f"<div class='metric-container'>"
            f'<div style=\'font-family:"DM Sans",sans-serif;font-size:0.72rem;'
            f"text-transform:uppercase;letter-spacing:0.07em;color:#6b6b6b;"
            f"margin-bottom:0.3rem;'>API Server</div>"
            f"{_status_badge(api_ok, '● Connected', '● Unreachable')}"
            f'<div style=\'font-family:"DM Mono",monospace;font-size:0.75rem;'
            f"color:#9e9e9e;margin-top:0.2rem;'>"
            f"{os.getenv('API_BASE_URL', 'http://localhost:8001')}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    with c2:
        account = api.get_alpaca_account()
        alpaca_ok = "error" not in account
        acct_num = account.get("account_number", "") if alpaca_ok else ""
        mode = "Paper Trading" if alpaca_ok else "—"
        st.markdown(
            f"<div class='metric-container'>"
            f'<div style=\'font-family:"DM Sans",sans-serif;font-size:0.72rem;'
            f"text-transform:uppercase;letter-spacing:0.07em;color:#6b6b6b;"
            f"margin-bottom:0.3rem;'>Alpaca</div>"
            f"{_status_badge(alpaca_ok, '● Connected', '● Unreachable')}"
            f'<div style=\'font-family:"DM Mono",monospace;font-size:0.75rem;'
            f"color:#9e9e9e;margin-top:0.2rem;'>"
            f"{acct_num or '—'} · {mode}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    with c3:
        clock = api.get_market_clock()
        clock_ok = "error" not in clock
        is_open = clock.get("is_open", False) if clock_ok else False
        st.markdown(
            f"<div class='metric-container'>"
            f'<div style=\'font-family:"DM Sans",sans-serif;font-size:0.72rem;'
            f"text-transform:uppercase;letter-spacing:0.07em;color:#6b6b6b;"
            f"margin-bottom:0.3rem;'>Market</div>"
            f"{_status_badge(is_open, '● Open', '● Closed')}"
            f'<div style=\'font-family:"DM Mono",monospace;font-size:0.75rem;'
            f"color:#9e9e9e;margin-top:0.2rem;'>"
            f"{'Real-time via Alpaca' if clock_ok else 'Clock unavailable'}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

    if st.button("↻ Recheck connections", key="recheck_btn"):
        st.cache_data.clear()
        st.rerun()

    st.markdown("---")

    # ── Section 2: Analysis Preferences ──────────────────────────────────────
    st.markdown("<h2>Analysis Preferences</h2>", unsafe_allow_html=True)
    st.markdown(
        "<p style='color:#6b6b6b;font-size:0.88rem;margin-bottom:1rem;'>"
        "These defaults pre-fill the Analysis page each session.</p>",
        unsafe_allow_html=True,
    )

    prefs = _load_prefs()

    # Seed session state from persisted prefs (only on first load)
    if "selected_symbol" not in st.session_state:
        st.session_state.selected_symbol = prefs["symbol"]
    if "selected_timeframe" not in st.session_state:
        st.session_state.selected_timeframe = prefs["timeframe"]

    p1, p2 = st.columns(2)
    with p1:
        new_sym = (
            st.text_input(
                "Default Symbol",
                value=st.session_state.selected_symbol,
                help="Pre-filled symbol in the Analysis page",
            )
            .upper()
            .strip()
        )
        if new_sym and new_sym != st.session_state.selected_symbol:
            st.session_state.selected_symbol = new_sym
            _save_prefs(new_sym, st.session_state.selected_timeframe)
            st.success(f"Default symbol saved as {new_sym}")

    with p2:
        timeframes = ["1D", "1W", "1M", "3M", "6M", "1Y"]
        current_idx = (
            timeframes.index(st.session_state.selected_timeframe)
            if st.session_state.selected_timeframe in timeframes
            else 2
        )
        new_tf = st.selectbox(
            "Default Timeframe",
            timeframes,
            index=current_idx,
            help="Pre-filled timeframe in the Analysis page",
        )
        if new_tf != st.session_state.selected_timeframe:
            st.session_state.selected_timeframe = new_tf
            _save_prefs(st.session_state.selected_symbol, new_tf)
            st.success(f"Default timeframe saved as {new_tf}")

    st.markdown("---")

    # ── Section 3: System Info ────────────────────────────────────────────────
    st.markdown("<h2>System Info</h2>", unsafe_allow_html=True)

    s1, s2 = st.columns(2)
    with s1:
        api_url = os.getenv("API_BASE_URL", "http://localhost:8001")
        st.markdown(
            f'<div style=\'font-family:"DM Sans",sans-serif;font-size:0.88rem;'
            f"line-height:1.9;color:#1a1a1a;'>"
            f"<span style='color:#6b6b6b;'>API URL&emsp;</span>"
            f"<span style='font-family:\"DM Mono\",monospace;'>{api_url}</span><br>"
            f"<span style='color:#6b6b6b;'>Session started&emsp;</span>"
            f"<span style='font-family:\"DM Mono\",monospace;'>"
            f"{datetime.now().strftime('%Y-%m-%d %H:%M')}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with s2:
        import streamlit as _st

        st.markdown(
            f'<div style=\'font-family:"DM Sans",sans-serif;font-size:0.88rem;'
            f"line-height:1.9;color:#1a1a1a;'>"
            f"<span style='color:#6b6b6b;'>Streamlit&emsp;</span>"
            f"<span style='font-family:\"DM Mono\",monospace;'>"
            f"{_st.__version__}</span><br>"
            f"<span style='color:#6b6b6b;'>Python&emsp;</span>"
            f"<span style='font-family:\"DM Mono\",monospace;'>"
            f"{sys.version.split()[0]}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )


if __name__ == "__main__":
    main()
