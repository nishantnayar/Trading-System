"""
Alpaca Trading API Routes
"""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException

from src.config.settings import get_settings
from src.services.alpaca import AlpacaAPIError, AlpacaClient, AlpacaConnectionError

logger = logging.getLogger(__name__)
router = APIRouter(tags=["alpaca"])

# Global Alpaca client instance
_alpaca_client: Optional[AlpacaClient] = None


def get_alpaca_client() -> AlpacaClient:
    """Get or create Alpaca client instance"""
    global _alpaca_client

    if _alpaca_client is None:
        settings = get_settings()
        try:
            _alpaca_client = AlpacaClient(
                api_key=settings.alpaca_api_key,
                secret_key=settings.alpaca_secret_key,
                is_paper=True,
            )
        except Exception as e:
            logger.error(f"Failed to initialize Alpaca client: {e}")
            raise HTTPException(
                status_code=500, detail="Failed to initialize Alpaca client"
            )

    return _alpaca_client


@router.get("/config")
async def get_alpaca_config() -> Dict[str, Any]:
    """Get Alpaca configuration (without sensitive data)"""
    settings = get_settings()
    has_credentials = bool(settings.alpaca_api_key and settings.alpaca_secret_key)

    return {
        "is_paper": True,
        "base_url": "https://paper-api.alpaca.markets",
        "has_credentials": has_credentials,
        "demo_mode": not has_credentials,
    }


def get_demo_account() -> Dict[str, Any]:
    """Get demo account data"""
    return {
        "id": "demo-account-123",
        "account_number": "DEMO123456",
        "status": "ACTIVE",
        "currency": "USD",
        "buying_power": 10000.00,
        "cash": 5000.00,
        "portfolio_value": 25000.00,
        "equity": 25000.00,
        "last_equity": 24000.00,
        "created_at": "2024-01-01T00:00:00Z",
        "trading_blocked": False,
        "transfers_blocked": False,
        "account_blocked": False,
        "shorting_enabled": True,
        "multiplier": 4.0,
        "long_market_value": 20000.00,
        "short_market_value": 0.00,
        "initial_margin": 5000.00,
        "maintenance_margin": 2000.00,
        "daytrade_count": 0,
        "pattern_day_trader": False,
    }


def get_demo_positions() -> List[Dict[str, Any]]:
    """Get demo positions data"""
    return [
        {
            "asset_id": "demo-asset-1",
            "symbol": "AAPL",
            "exchange": "NASDAQ",
            "asset_class": "us_equity",
            "qty": 100.0,
            "side": "long",
            "market_value": 15000.00,
            "cost_basis": 14000.00,
            "unrealized_pl": 1000.00,
            "unrealized_plpc": 0.0714,
            "unrealized_intraday_pl": 150.00,
            "unrealized_intraday_plpc": 0.0107,
            "current_price": 150.00,
            "lastday_price": 148.50,
            "change_today": 1.50,
            "avg_entry_price": 140.00,
        },
        {
            "asset_id": "demo-asset-2",
            "symbol": "GOOGL",
            "exchange": "NASDAQ",
            "asset_class": "us_equity",
            "qty": 10.0,
            "side": "long",
            "market_value": 5000.00,
            "cost_basis": 4800.00,
            "unrealized_pl": 200.00,
            "unrealized_plpc": 0.0417,
            "unrealized_intraday_pl": 50.00,
            "unrealized_intraday_plpc": 0.0104,
            "current_price": 500.00,
            "lastday_price": 495.00,
            "change_today": 5.00,
            "avg_entry_price": 480.00,
        },
    ]


def get_demo_orders() -> List[Dict[str, Any]]:
    """Get demo orders data"""
    return [
        {
            "id": "demo-order-1",
            "client_order_id": "demo-client-1",
            "created_at": "2024-01-15T10:30:00Z",
            "updated_at": "2024-01-15T10:30:00Z",
            "submitted_at": "2024-01-15T10:30:00Z",
            "filled_at": None,
            "expired_at": None,
            "canceled_at": None,
            "failed_at": None,
            "replaced_at": None,
            "replaced_by": None,
            "replaces": None,
            "asset_id": "demo-asset-3",
            "symbol": "MSFT",
            "asset_class": "us_equity",
            "notional": None,
            "qty": 50.0,
            "filled_qty": 0.0,
            "filled_avg_price": None,
            "order_class": "simple",
            "order_type": "market",
            "type": "market",
            "side": "buy",
            "time_in_force": "day",
            "limit_price": None,
            "stop_price": None,
            "status": "pending",
            "extended_hours": False,
            "legs": None,
            "trail_percent": None,
            "trail_price": None,
            "hwm": None,
        }
    ]


def get_demo_trades() -> List[Dict[str, Any]]:
    """Get demo trades data"""
    return [
        {
            "id": "demo-trade-1",
            "symbol": "AAPL",
            "side": "buy",
            "qty": 12,
            "filled_qty": 12,
            "filled_avg_price": 201.14,
            "status": "filled",
            "created_at": "2024-01-01T09:30:00Z",
            "filled_at": "2024-01-01T09:30:15Z",
            "order_type": "market",
            "time_in_force": "day",
        },
        {
            "id": "demo-trade-2",
            "symbol": "MSFT",
            "side": "sell",
            "qty": 5,
            "filled_qty": 5,
            "filled_avg_price": 350.25,
            "status": "filled",
            "created_at": "2024-01-01T11:15:00Z",
            "filled_at": "2024-01-01T11:15:30Z",
            "order_type": "limit",
            "time_in_force": "day",
        },
    ]


def get_demo_clock() -> Dict[str, Any]:
    """Get demo clock data"""
    from datetime import datetime, timedelta

    now = datetime.now()
    return {
        "timestamp": now.isoformat(),
        "is_open": True,
        "next_open": (now + timedelta(days=1))
        .replace(hour=9, minute=30, second=0, microsecond=0)
        .isoformat(),
        "next_close": now.replace(
            hour=16, minute=0, second=0, microsecond=0
        ).isoformat(),
    }


@router.get("/account")
async def get_account(
    client: AlpacaClient = Depends(get_alpaca_client),
) -> Dict[str, Any]:
    """Get account information"""
    settings = get_settings()
    has_credentials = bool(settings.alpaca_api_key and settings.alpaca_secret_key)

    if not has_credentials:
        logger.info("No Alpaca credentials found, returning demo data")
        return get_demo_account()

    try:
        account = await client.get_account()
        return account
    except AlpacaAPIError as e:
        logger.error(f"Alpaca API error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except AlpacaConnectionError as e:
        logger.error(f"Alpaca connection error: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/positions")
async def get_positions(
    client: AlpacaClient = Depends(get_alpaca_client),
) -> list[Dict[str, Any]]:
    """Get all positions"""
    settings = get_settings()
    has_credentials = bool(settings.alpaca_api_key and settings.alpaca_secret_key)

    if not has_credentials:
        logger.info("No Alpaca credentials found, returning demo positions")
        return get_demo_positions()

    try:
        positions = await client.get_positions()
        return positions
    except AlpacaAPIError as e:
        logger.error(f"Alpaca API error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except AlpacaConnectionError as e:
        logger.error(f"Alpaca connection error: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/orders")
async def get_orders(
    status: str = "open",
    limit: int = 50,
    client: AlpacaClient = Depends(get_alpaca_client),
) -> list[Dict[str, Any]]:
    """Get orders"""
    settings = get_settings()
    has_credentials = bool(settings.alpaca_api_key and settings.alpaca_secret_key)

    if not has_credentials:
        logger.info("No Alpaca credentials found, returning demo orders")
        return get_demo_orders()

    try:
        orders = await client.get_orders(status=status, limit=limit)
        return orders
    except AlpacaAPIError as e:
        logger.error(f"Alpaca API error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except AlpacaConnectionError as e:
        logger.error(f"Alpaca connection error: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/trades")
async def get_recent_trades(
    limit: int = 20, client: AlpacaClient = Depends(get_alpaca_client)
) -> list[Dict[str, Any]]:
    """Get recent completed trades (filled orders)"""
    settings = get_settings()
    has_credentials = bool(settings.alpaca_api_key and settings.alpaca_secret_key)

    if not has_credentials:
        logger.info("No Alpaca credentials found, returning demo trades")
        return get_demo_trades()

    try:
        # Get filled orders (completed trades)
        orders = await client.get_orders(status="filled", limit=limit)
        return orders
    except AlpacaAPIError as e:
        logger.error(f"Alpaca API error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except AlpacaConnectionError as e:
        logger.error(f"Alpaca connection error: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/clock")
async def get_clock(
    client: AlpacaClient = Depends(get_alpaca_client),
) -> Dict[str, Any]:
    """Get market clock"""
    settings = get_settings()
    has_credentials = bool(settings.alpaca_api_key and settings.alpaca_secret_key)

    if not has_credentials:
        logger.info("No Alpaca credentials found, returning demo clock")
        return get_demo_clock()

    try:
        clock = await client.get_clock()
        return clock
    except AlpacaAPIError as e:
        logger.error(f"Alpaca API error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except AlpacaConnectionError as e:
        logger.error(f"Alpaca connection error: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/positions/{symbol}/close")
async def close_position(
    symbol: str, client: AlpacaClient = Depends(get_alpaca_client)
) -> Dict[str, Any]:
    """Close a position"""
    try:
        result = await client.close_position(symbol)
        return result
    except AlpacaAPIError as e:
        logger.error(f"Alpaca API error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except AlpacaConnectionError as e:
        logger.error(f"Alpaca connection error: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.delete("/orders/{order_id}")
async def cancel_order(
    order_id: str, client: AlpacaClient = Depends(get_alpaca_client)
) -> Dict[str, str]:
    """Cancel an order"""
    try:
        success = await client.cancel_order(order_id)
        if success:
            return {"message": "Order cancelled successfully"}
        else:
            raise HTTPException(status_code=400, detail="Failed to cancel order")
    except AlpacaAPIError as e:
        logger.error(f"Alpaca API error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except AlpacaConnectionError as e:
        logger.error(f"Alpaca connection error: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/orders")
async def place_order(
    symbol: str,
    qty: int,
    side: str,
    order_type: str = "market",
    time_in_force: str = "day",
    limit_price: Optional[float] = None,
    stop_price: Optional[float] = None,
    client: AlpacaClient = Depends(get_alpaca_client),
) -> Dict[str, Any]:
    """Place an order"""
    try:
        order = await client.place_order(
            symbol=symbol,
            qty=qty,
            side=side,
            order_type=order_type,
            time_in_force=time_in_force,
            limit_price=limit_price,
            stop_price=stop_price,
        )
        return order
    except AlpacaAPIError as e:
        logger.error(f"Alpaca API error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except AlpacaConnectionError as e:
        logger.error(f"Alpaca connection error: {e}")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
