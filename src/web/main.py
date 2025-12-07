"""
Main FastAPI application for the trading system API.
This is now a pure API server - the UI has been moved to Streamlit.
"""

import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from contextlib import asynccontextmanager  # noqa: E402

from typing import Any, Callable  # noqa: E402

from fastapi import FastAPI, Request  # noqa: E402
from loguru import logger  # noqa: E402
from starlette.middleware.base import BaseHTTPMiddleware  # noqa: E402
from starlette.responses import Response  # noqa: E402

from src.shared.logging import setup_logging, shutdown_logging  # noqa: E402
from src.shared.logging.correlation import (  # noqa: E402
    correlation_context,
    generate_correlation_id,
)
from src.web.api.alpaca_routes import router as alpaca_router  # noqa: E402
from src.web.api.company_info import router as company_info_router  # noqa: E402
from src.web.api.company_officers import router as company_officers_router  # noqa: E402
from src.web.api.financial_statements import (  # noqa: E402
    router as financial_statements_router,
)
from src.web.api.institutional_holders import (  # noqa: E402
    router as institutional_holders_router,
)
from src.web.api.key_statistics import router as key_statistics_router  # noqa: E402
from src.web.api.market_data import router as market_data_router  # noqa: E402
from src.web.api.routes import router  # noqa: E402


# Correlation ID middleware for request tracking
class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add correlation ID to all requests"""

    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        # Get correlation ID from header or generate new one
        correlation_id = request.headers.get("X-Correlation-ID") or generate_correlation_id()
        
        # Set correlation ID in context for logging
        with correlation_context(correlation_id):
            response = await call_next(request)
            # Add correlation ID to response header
            response.headers["X-Correlation-ID"] = correlation_id
            return response


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    """Lifespan context manager for startup and shutdown events"""
    # Startup
    setup_logging(service_name="web")
    logger.info("Trading System API starting up")
    yield
    # Shutdown
    logger.info("Trading System API shutting down")
    shutdown_logging()


app = FastAPI(
    title="Trading System API",
    description="A production-grade algorithmic trading system API",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Add correlation ID middleware
app.add_middleware(CorrelationIDMiddleware)

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
