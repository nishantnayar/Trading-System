"""
Data Quality Monitor — last ingestion timestamps and stale data alerts.
"""

import os
import sys
from datetime import datetime

import pandas as pd
import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from api_client import get_api_client  # noqa: E402

st.set_page_config(
    page_title="Data Quality Monitor",
    page_icon="🔍",
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


def _status_html(status: str) -> str:
    colors = {"success": "#2A7A4B", "failed": "#C0392B", "partial": "#D68910"}
    color = colors.get(status, "#6b6b6b")
    return (
        f'<span style=\'color:{color};font-family:"DM Sans",sans-serif;'
        f"font-weight:500;font-size:0.82rem;'>{status}</span>"
    )


def _stale_html(is_stale: bool) -> str:
    if is_stale:
        return (
            '<span style=\'color:#C0392B;font-family:"DM Sans",sans-serif;'
            "font-weight:500;font-size:0.82rem;'>stale</span>"
        )
    return (
        '<span style=\'color:#2A7A4B;font-family:"DM Sans",sans-serif;'
        "font-weight:500;font-size:0.82rem;'>fresh</span>"
    )


def _metric_card(label: str, value: str, sub: str = "", color: str = "#1a1a1a") -> str:
    return (
        f"<div class='metric-container'>"
        f'<div style=\'font-family:"DM Sans",sans-serif;font-size:0.72rem;'
        f"text-transform:uppercase;letter-spacing:0.07em;color:#6b6b6b;"
        f"margin-bottom:0.3rem;'>{label}</div>"
        f'<div style=\'font-family:"DM Sans",sans-serif;font-size:1.5rem;'
        f"font-weight:600;color:{color};'>{value}</div>"
        + (
            f'<div style=\'font-family:"DM Mono",monospace;font-size:0.72rem;'
            f"color:#9e9e9e;margin-top:0.2rem;'>{sub}</div>"
            if sub
            else ""
        )
        + "</div>"
    )


def _format_dt(iso_str: str | None) -> str:
    if not iso_str:
        return "—"
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except Exception:
        return iso_str


def main() -> None:
    load_css()
    st.markdown("<h1>Data Quality Monitor</h1>", unsafe_allow_html=True)

    api = get_api_client()

    if st.button("↻ Refresh", key="refresh_btn"):
        st.cache_data.clear()
        st.rerun()

    # ── Summary metrics ───────────────────────────────────────────────────────
    summary = api.get_data_quality_summary()

    if "error" in summary:
        st.error("Could not load data quality summary. Is the API running?")
        return

    total = summary.get("total_symbols", 0)
    stale = summary.get("stale_symbols", 0)
    ok = summary.get("ok_symbols", 0)
    last_ingest = _format_dt(summary.get("last_ingestion_at"))

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(_metric_card("Tracked Symbols", str(total)), unsafe_allow_html=True)
    with c2:
        st.markdown(
            _metric_card("Up to Date", str(ok), color="#2A7A4B"), unsafe_allow_html=True
        )
    with c3:
        color = "#C0392B" if stale > 0 else "#6b6b6b"
        st.markdown(
            _metric_card("Stale", str(stale), color=color), unsafe_allow_html=True
        )
    with c4:
        st.markdown(
            _metric_card(
                "Last Ingestion",
                last_ingest[:10] if last_ingest != "—" else "—",
                sub=last_ingest[11:] if last_ingest != "—" else "",
            ),
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ── Alerts ────────────────────────────────────────────────────────────────
    alerts = api.get_data_quality_alerts()

    if alerts:
        st.markdown(
            f"<h2>Alerts <span style='color:#C0392B;font-size:1rem;font-weight:500'>"
            f"({len(alerts)} issue{'s' if len(alerts) != 1 else ''})</span></h2>",
            unsafe_allow_html=True,
        )
        alert_df = (
            pd.DataFrame(alerts)[
                ["symbol", "last_date", "days_since_last_bar", "record_count"]
            ]
            .rename(
                columns={
                    "symbol": "Symbol",
                    "last_date": "Last Bar",
                    "days_since_last_bar": "Days Stale",
                    "record_count": "Records",
                }
            )
            .sort_values("Days Stale", ascending=False)
        )
        st.dataframe(
            alert_df,
            width="stretch",
            hide_index=True,
            column_config={
                "Days Stale": st.column_config.NumberColumn(format="%d days"),
                "Records": st.column_config.NumberColumn(format="%d"),
            },
        )
        st.markdown("---")
    else:
        st.success("All symbols are up to date.")
        st.markdown("---")

    # ── Full ingestion status table ───────────────────────────────────────────
    st.markdown("<h2>All Ingestion Series</h2>", unsafe_allow_html=True)

    statuses = api.get_ingestion_status()

    if not statuses:
        st.info("No market data found for yahoo. Trigger a data ingestion flow first.")
        return

    df = pd.DataFrame(statuses)

    # Filter
    stale_filter = st.selectbox("Freshness", ["All", "Stale only", "Fresh only"])
    if stale_filter == "Stale only":
        filtered = df[df["is_stale"]]
    elif stale_filter == "Fresh only":
        filtered = df[~df["is_stale"]]
    else:
        filtered = df

    display = (
        filtered[
            ["symbol", "last_date", "days_since_last_bar", "record_count", "is_stale"]
        ]
        .rename(
            columns={
                "symbol": "Symbol",
                "last_date": "Last Bar",
                "days_since_last_bar": "Days Stale",
                "record_count": "Records",
                "is_stale": "Stale?",
            }
        )
        .sort_values(["Days Stale", "Symbol"], ascending=[False, True])
    )

    st.dataframe(
        display,
        width="stretch",
        hide_index=True,
        column_config={
            "Days Stale": st.column_config.NumberColumn(format="%d days"),
            "Records": st.column_config.NumberColumn(format="%d"),
            "Stale?": st.column_config.CheckboxColumn(),
        },
    )

    st.markdown(
        f'<div style=\'font-family:"DM Mono",monospace;font-size:0.72rem;color:#9e9e9e;'
        f"margin-top:0.5rem;'>Showing {len(display)} of {len(df)} series · "
        f"Stale threshold: >2 days since last successful load</div>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
