"""
Main entry point for the Trading System web application.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.web.api.alpaca_routes import router as alpaca_router
from src.web.api.company_info import router as company_info_router
from src.web.api.company_officers import router as company_officers_router
from src.web.api.financial_statements import router as financial_statements_router
from src.web.api.institutional_holders import router as institutional_holders_router
from src.web.api.key_statistics import router as key_statistics_router
from src.web.api.market_data import router as market_data_router
from src.web.api.routes import router

app = FastAPI(
    title="Trading System",
    description="A production-grade algorithmic trading system",
    version="1.0.0",
)

# Include API routes
app.include_router(router)
app.include_router(alpaca_router, prefix="/api/alpaca")
app.include_router(market_data_router)
app.include_router(company_info_router)
app.include_router(company_officers_router)
app.include_router(key_statistics_router)
app.include_router(institutional_holders_router)
app.include_router(financial_statements_router)

# Mount static files
app.mount("/static", StaticFiles(directory="src/web/static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="src/web/templates")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8002)
