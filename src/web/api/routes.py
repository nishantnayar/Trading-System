"""
Root routes for the trading system API (health check and index).

Feature routers are registered directly in src/web/main.py.
"""

from datetime import datetime

from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter()


@router.get("/health")
async def health_check() -> JSONResponse:
    """Health check endpoint for monitoring"""
    return JSONResponse(
        content={
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "trading-system-api",
            "ui": "streamlit",
            "ui_url": "http://localhost:8501",
        }
    )


@router.get("/")
async def root() -> JSONResponse:
    """Root endpoint - points at the API documentation"""
    return JSONResponse(
        content={
            "message": "Trading System API",
            "version": "1.0.0",
            "docs": "/docs",
            "ui": "streamlit",
            "ui_url": "http://localhost:8501",
        }
    )
