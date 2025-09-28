"""
Main entry point for the Trading System web application.
"""
import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from src.web.api.routes import router

app = FastAPI(
    title="Trading System",
    description="A production-grade algorithmic trading system",
    version="1.0.0"
)

# Include API routes
app.include_router(router)

# Mount static files
app.mount("/static", StaticFiles(directory="src/web/static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="src/web/templates")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8001)
