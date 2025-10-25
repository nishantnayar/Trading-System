"""
FastAPI routes for the trading system API.
This is now a pure API server - the UI has been moved to Streamlit.
"""

from datetime import datetime

from fastapi import APIRouter
from fastapi.responses import JSONResponse

# Import API routers
from .pairs_trading import router as pairs_trading_router

router = APIRouter()

# Include API routers
router.include_router(pairs_trading_router)


@router.get("/health")
async def health_check() -> JSONResponse:
    """Health check endpoint for monitoring"""
    return JSONResponse(
        content={
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "trading-system-api",
            "ui": "streamlit",
            "ui_url": "http://localhost:8501"
        }
    )


@router.get("/")
async def root() -> JSONResponse:
    """Root endpoint - redirects to API documentation"""
    return JSONResponse(
        content={
            "message": "Trading System API",
            "version": "1.0.0",
            "docs": "/docs",
            "ui": "streamlit",
            "ui_url": "http://localhost:8501"
        }
    )