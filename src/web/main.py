"""
Main FastAPI application for the trading system web interface.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from fastapi.templating import Jinja2Templates  # noqa: E402

from src.web.api.alpaca_routes import router as alpaca_router  # noqa: E402
from src.web.api.market_data import router as market_data_router  # noqa: E402
from src.web.api.routes import router  # noqa: E402

app = FastAPI(
    title="Trading System",
    description="A production-grade algorithmic trading system",
    version="1.0.0",
)

# Include API routes
app.include_router(router)
app.include_router(alpaca_router)
app.include_router(market_data_router)

# Mount static files
app.mount("/static", StaticFiles(directory="src/web/static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="src/web/templates")

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8001)
