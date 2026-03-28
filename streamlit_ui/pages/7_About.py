"""
About — Nishant Nayar & Trading System
"""

import os
import sys

import streamlit as st

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

st.set_page_config(
    page_title="About",
    page_icon="👤",
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


def main() -> None:
    load_css()

    st.markdown("<h1>About</h1>", unsafe_allow_html=True)

    # ── Bio ───────────────────────────────────────────────────────────────────
    left, right = st.columns([2, 1])

    with left:
        st.markdown(
            "<h2>Nishant Nayar</h2>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='color:#6b6b6b;font-size:0.85rem;"
            "text-transform:uppercase;letter-spacing:0.07em;"
            "margin-bottom:0.8rem;'>Vice President · Lead Solution Analyst</p>",
            unsafe_allow_html=True,
        )
        st.markdown(
            "<p style='font-size:0.92rem;line-height:1.7;max-width:640px;'>"
            "Data management professional with a proven track record of developing "
            "and executing strategic initiatives within Investment Banking, Commercial "
            "Banking, and Asset Management segments of financial services. Translates "
            "complex data challenges into actionable solutions by leveraging data "
            "governance best practices and applied data science techniques."
            "</p>",
            unsafe_allow_html=True,
        )

    with right:
        st.markdown(
            "<div style='padding:1.2rem;border:1px solid rgba(26,26,26,0.08);"
            "border-radius:4px;font-family:\"DM Sans\",sans-serif;"
            "font-size:0.85rem;line-height:2;'>"
            "<span style='color:#6b6b6b;'>Location</span><br>"
            "<span style='font-weight:500;'>Greater Chicago Area</span><br><br>"
            "<span style='color:#6b6b6b;'>Links</span><br>"
            "<a href='https://www.linkedin.com/in/nishantnayar/' "
            "style='color:#1a1a1a;' target='_blank'>LinkedIn</a> &nbsp;·&nbsp; "
            "<a href='https://github.com/nishantnayar' "
            "style='color:#1a1a1a;' target='_blank'>GitHub</a> &nbsp;·&nbsp; "
            "<a href='https://medium.com/@nishant-nayar' "
            "style='color:#1a1a1a;' target='_blank'>Medium</a><br>"
            "<a href='https://nishantnayar.vercel.app/' "
            "style='color:#1a1a1a;' target='_blank'>Portfolio</a>"
            "</div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ── About This Project ────────────────────────────────────────────────────
    st.markdown("<h2>About This Trading System</h2>", unsafe_allow_html=True)

    f1, f2 = st.columns(2)

    with f1:
        st.markdown(
            "<div class='card'>"
            "<h3>What It Does</h3>"
            "<ul style='font-size:0.88rem;line-height:1.9;padding-left:1.1rem;"
            "color:#1a1a1a;'>"
            "<li>Paper trading via Alpaca — live positions, orders, and account tracking</li>"
            "<li>Pairs trading strategy — cointegration-based signals, automated execution</li>"
            "<li>Strategy backtesting with gate criteria (Sharpe, drawdown, win rate)</li>"
            "<li>Stock screener with AI-powered natural language queries</li>"
            "<li>Technical analysis — candlestick charts, RSI, MACD, Bollinger Bands</li>"
            "<li>Fundamental data — financials, key statistics, institutional holders</li>"
            "</ul>"
            "</div>",
            unsafe_allow_html=True,
        )

    with f2:
        st.markdown(
            "<div class='card'>"
            "<h3>Tech Stack</h3>"
            "<ul style='font-size:0.88rem;line-height:1.9;padding-left:1.1rem;"
            "color:#1a1a1a;'>"
            "<li><strong>Backend</strong> — FastAPI, Python 3.11+</li>"
            "<li><strong>Frontend</strong> — Streamlit</li>"
            "<li><strong>Database</strong> — PostgreSQL + SQLAlchemy</li>"
            "<li><strong>Orchestration</strong> — Prefect</li>"
            "<li><strong>Trading</strong> — Alpaca Paper Trading API</li>"
            "<li><strong>Data</strong> — Yahoo Finance, Polygon.io</li>"
            "<li><strong>AI/ML</strong> — Local LLM (Phi-3) for screener queries</li>"
            "</ul>"
            "</div>",
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # ── Currently Exploring ───────────────────────────────────────────────────
    st.markdown("<h2>Currently Exploring</h2>", unsafe_allow_html=True)
    st.markdown(
        "<div style='font-size:0.88rem;line-height:1.9;'>"
        "<span style='font-family:\"DM Mono\",monospace;color:#6b6b6b;'>→</span>"
        "&nbsp; Kaggle's 5-Day AI Agents Intensive Course<br>"
        "<span style='font-family:\"DM Mono\",monospace;color:#6b6b6b;'>→</span>"
        "&nbsp; Quantum Computing"
        "</div>",
        unsafe_allow_html=True,
    )

    st.markdown("---")
    st.markdown(
        "<p style='font-family:\"DM Sans\",sans-serif;font-size:0.78rem;"
        "color:#9e9e9e;'>nishant.nayar@hotmail.com</p>",
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
