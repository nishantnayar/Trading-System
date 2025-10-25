"""
Main FastAPI application for the trading system API.
This is now a pure API server - the UI has been moved to Streamlit.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI  # noqa: E402

from src.web.api.alpaca_routes import router as alpaca_router  # noqa: E402
from src.web.api.company_info import router as company_info_router  # noqa: E402
from src.web.api.company_officers import router as company_officers_router  # noqa: E402
from src.web.api.financial_statements import router as financial_statements_router  # noqa: E402
from src.web.api.institutional_holders import router as institutional_holders_router  # noqa: E402
from src.web.api.key_statistics import router as key_statistics_router  # noqa: E402
from src.web.api.market_data import router as market_data_router  # noqa: E402
from src.web.api.routes import router  # noqa: E402

app = FastAPI(
    title="Trading System API",
    description="A production-grade algorithmic trading system API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Include API routes
app.include_router(router)
app.include_router(alpaca_router)
app.include_router(market_data_router)
app.include_router(company_info_router)
app.include_router(company_officers_router)
app.include_router(financial_statements_router)
app.include_router(institutional_holders_router)
app.include_router(key_statistics_router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
