"""
FastAPI routes for the trading system web interface.
"""

from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="src/web/templates")


@router.get("/", response_class=HTMLResponse)
async def landing_page(request: Request):
    """Main landing page for the trading system."""
    return templates.TemplateResponse(
        "landing.html",
        {
            "request": request,
            "page_title": "Trading System",
            "current_time": datetime.now().strftime("%B %d, %Y at %H:%M:%S"),
        },
    )
