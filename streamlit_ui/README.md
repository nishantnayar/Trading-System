# Streamlit UI

This directory contains the Streamlit user interface for the Trading System.

## Overview

The Streamlit UI provides a professional, multipage trading dashboard styled with a paper/ink design system (Playfair Display headings, DM Sans body, DM Mono for all numeric values). All data is sourced live from the FastAPI backend — no hardcoded or simulated values.

## Files

- `streamlit_app.py` — Home dashboard (market clock, account summary, positions, open orders)
- `run_streamlit.py` — Launch script; writes `~/.streamlit/config.toml` with the correct theme
- `pages/` — Numbered page modules controlling sidebar order
- `api_client.py` — HTTP client for all FastAPI backend calls
- `css_config.py` — Design system constants and CSS variable generation
- `styles.css` — Global stylesheet (fonts, layout, cards, tables, charts, market banners)

## Running the UI

```bash
# Recommended: uses run script to configure theme before launch (from project root)
python streamlit_ui/run_streamlit.py

# Direct command (from project root)
streamlit run streamlit_ui/streamlit_app.py --server.address localhost --server.port 8501
```

## Access

Once running, access the UI at: http://localhost:8501

The FastAPI backend must be running on port 8001:
```bash
python -m src.web.main
```

## Pages

Pages are numbered to enforce sidebar order. Streamlit strips the numeric prefix from the display name.

| File | Sidebar Label | Description |
|------|--------------|-------------|
| `streamlit_app.py` | Dashboard | Home — market clock, account metrics, positions, open orders |
| `pages/1_Portfolio.py` | Portfolio | Full account summary, position management, order management, trade history, order placement |
| `pages/2_Analysis.py` | Analysis | Candlestick charts with volume and technical indicators (SMA, EMA, RSI, MACD, Bollinger Bands) |
| `pages/3_Screener.py` | Screener | AI-powered stock screening via Ollama; traditional filter mode also available |
| `pages/4_Pairs_Trading.py` | Pairs Trading | Live pairs strategy monitoring — z-score chart, active pairs table, performance summary |
| `pages/5_Backtest_Review.py` | Backtest Review | Backtest runner with pass/fail gates, equity curve, trade log, pair stock analysis |
| `pages/6_Settings.py` | Settings | API connection status, analysis preferences (symbol/timeframe), system info |
| `pages/7_About.py` | About | System overview, technology stack, contact information |

## Design System

All pages share a consistent visual language defined in `css_config.py` and `styles.css`:

- **Palette**: `#FAFAF8` (background), `#1a1a1a` (ink), `#F5F4F0` (warm hover), `#2A7A4B` (profit), `#C0392B` (loss), `#D97706` (warning/amber)
- **Fonts**: Playfair Display (h1/h2), DM Sans (body/labels), DM Mono (prices/metrics/tables)
- **Charts**: Plotly with transparent backgrounds to blend with page background
- **Cards**: 1px border `rgba(26,26,26,0.08)`, 4px border-radius, no drop shadows

## AI Features (Optional)

The Stock Screener page supports natural language queries via Ollama:
- Requires Ollama running locally with the `phi3` model
- Test connection: `python scripts/test_ollama.py`
- See [Stock Screener Guide](../docs/user-guide/stock-screener.md) for details

## Session State

Cross-page persistent state is intentionally minimal:
- `selected_symbol` — carried from Settings to Analysis page
- `selected_timeframe` — carried from Settings to Analysis page

## Dependencies

- `streamlit` — web framework
- `plotly` — interactive financial charts
- `pandas` — data processing
- `ollama` — LLM integration (optional, for Screener AI mode)

## Troubleshooting

See the main [Troubleshooting Guide](../docs/troubleshooting.md) for common issues.

For AI features:
- Ensure Ollama is installed and running: `ollama serve`
- Install a model: `ollama pull phi3`
- Test connection: `python scripts/test_ollama.py`
