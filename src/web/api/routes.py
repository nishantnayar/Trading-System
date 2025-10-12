"""
FastAPI routes for the trading system web interface.
"""

from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="src/web/templates")


@router.get("/health")
async def health_check() -> JSONResponse:
    """Health check endpoint for monitoring"""
    return JSONResponse(
        content={
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "trading-system",
        }
    )


@router.get("/", response_class=HTMLResponse)
async def landing_page(request: Request) -> HTMLResponse:
    """Main landing page for the trading system."""
    return templates.TemplateResponse(
        "landing.html",
        {
            "request": request,
            "page_title": "Trading System",
            "current_time": datetime.now().strftime("%B %d, %Y at %H:%M:%S"),
        },
    )


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard_page(request: Request) -> HTMLResponse:
    """Trading dashboard page."""
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "page_title": "Dashboard - Trading System",
            "current_time": datetime.now().strftime("%B %d, %Y at %H:%M:%S"),
        },
    )


@router.get("/trading", response_class=HTMLResponse)
async def trading_page(request: Request) -> HTMLResponse:
    """Trading interface page."""
    return templates.TemplateResponse(
        "trading.html",
        {
            "request": request,
            "page_title": "Trading - Trading System",
            "current_time": datetime.now().strftime("%B %d, %Y at %H:%M:%S"),
        },
    )


@router.get("/strategies", response_class=HTMLResponse)
async def strategies_page(request: Request) -> HTMLResponse:
    """Trading strategies page."""
    return templates.TemplateResponse(
        "strategies.html",
        {
            "request": request,
            "page_title": "Strategies - Trading System",
            "current_time": datetime.now().strftime("%B %d, %Y at %H:%M:%S"),
        },
    )


@router.get("/analysis", response_class=HTMLResponse)
async def analysis_page(request: Request) -> HTMLResponse:
    """Market analysis page with interactive charts."""
    return templates.TemplateResponse(
        "analysis.html",
        {
            "request": request,
            "page_title": "Market Analysis - Trading System",
            "current_time": datetime.now().strftime("%B %d, %Y at %H:%M:%S"),
        },
    )


@router.get("/profile", response_class=HTMLResponse)
async def profile_page(request: Request) -> HTMLResponse:
    """Author profile page."""
    return templates.TemplateResponse(
        "profile.html",
        {
            "request": request,
            "page_title": "Profile - Trading System",
            "current_time": datetime.now().strftime("%B %d, %Y at %H:%M:%S"),
        },
    )
