# Streamlit UI

This directory contains the Streamlit user interface for the Trading System.

## Overview

The Streamlit UI provides a modern, multipage interface for the trading system with:
- **Portfolio Management**: Real-time portfolio tracking and performance metrics
- **Market Analysis**: Interactive charts with technical indicators using Plotly
- **Stock Screener**: AI-powered stock screening with natural language queries (Ollama integration)
- **System Information**: Team details and system architecture
- **Settings**: User preferences and session state management

## Files

- `streamlit_app.py` - Main Streamlit application with multipage navigation
- `run_streamlit.py` - Script to run the Streamlit app with correct settings
- `pages/` - Individual page modules (Portfolio, Analysis, Screener, Author, Settings)
- `services/llm_service.py` - LLM service for AI-powered features (Ollama integration)
- `utils/` - Utility functions including technical indicators
- `api_client.py` - API client for backend communication
- `styles.css` - Custom CSS styling

## Running the UI

```bash
# Option 1: Direct command
streamlit run streamlit_ui/streamlit_app.py --server.address localhost --server.port 8501

# Option 2: Using the run script (from project root)
python streamlit_ui/run_streamlit.py

# Option 3: Using streamlit command (from project root)
streamlit run streamlit_ui/streamlit_app.py
```

## Access

Once running, access the UI at: http://localhost:8501

## Features

### Pages

1. **Portfolio** - Real-time portfolio tracking and performance metrics
2. **Analysis** - Interactive market analysis with Plotly charts and technical indicators
3. **Screener** - AI-powered stock screening with natural language queries (requires Ollama)
4. **Author** - System information and architecture details
5. **Settings** - User preferences and session state management

### AI Features (Optional)

The Stock Screener includes AI-powered natural language query support:
- Requires Ollama to be installed and running
- Recommended model: `phi3`
- Test connection: `python scripts/test_ollama.py`
- See [Stock Screener Guide](../docs/user-guide/stock-screener.md) for details

## Session State

The UI uses Streamlit session state to maintain data persistence across pages:
- Selected symbols and timeframes
- User preferences
- Cached portfolio data
- Filter settings

## Dependencies

- `streamlit` - Web framework
- `plotly` - Interactive charts
- `ollama` - LLM integration (optional, for AI features)
- `pandas` - Data processing
- `loguru` - Logging

## Troubleshooting

See the main [Troubleshooting Guide](../docs/troubleshooting.md) for common issues.

For AI features:
- Ensure Ollama is installed and running
- Install a model: `ollama pull phi3`
- Test connection: `python scripts/test_ollama.py`
