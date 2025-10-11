"""
Alpaca Trading API Client
"""

import logging
import os
from typing import Any, Dict, List, Optional

from alpaca_trade_api import REST
from alpaca_trade_api.rest import APIError

from .exceptions import AlpacaAPIError, AlpacaAuthenticationError, AlpacaConnectionError

logger = logging.getLogger(__name__)


class AlpacaClient:
    """Alpaca Trading API Client for paper trading"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        base_url: Optional[str] = None,
        is_paper: bool = True,
    ):
        """
        Initialize Alpaca client

        Args:
            api_key: Alpaca API key
            secret_key: Alpaca secret key
            base_url: Alpaca API base URL
            is_paper: Whether to use paper trading
        """
        self.api_key = api_key or os.getenv("ALPACA_API_KEY")
        self.secret_key = secret_key or os.getenv("ALPACA_SECRET_KEY")
        self.is_paper = is_paper

        if is_paper:
            self.base_url = base_url or "https://paper-api.alpaca.markets"
        else:
            self.base_url = base_url or "https://api.alpaca.markets"

        if not self.api_key or not self.secret_key:
            raise AlpacaAuthenticationError("Alpaca API credentials not provided")

        try:
            self.client = REST(
                key_id=self.api_key,
                secret_key=self.secret_key,
                base_url=self.base_url,
                api_version="v2",
            )
            logger.info(
                f"Alpaca client initialized for {'paper' if is_paper else 'live'} trading"
            )
        except Exception as e:
            raise AlpacaConnectionError(f"Failed to initialize Alpaca client: {str(e)}")

    async def get_account(self) -> Dict[str, Any]:
        """Get account information"""
        try:
            account = self.client.get_account()
            return {
                "id": account.id,
                "account_number": account.account_number,
                "status": account.status,
                "currency": account.currency,
                "buying_power": float(account.buying_power),
                "cash": float(account.cash),
                "portfolio_value": float(account.portfolio_value),
                "equity": float(account.equity),
                "last_equity": float(account.last_equity),
                "created_at": (
                    account.created_at.isoformat() if account.created_at else None
                ),
                "trading_blocked": account.trading_blocked,
                "transfers_blocked": account.transfers_blocked,
                "account_blocked": account.account_blocked,
                "shorting_enabled": account.shorting_enabled,
                "multiplier": float(account.multiplier),
                "long_market_value": float(account.long_market_value),
                "short_market_value": float(account.short_market_value),
                "initial_margin": float(account.initial_margin),
                "maintenance_margin": float(account.maintenance_margin),
                "daytrade_count": account.daytrade_count,
                "pattern_day_trader": account.pattern_day_trader,
            }
        except APIError as e:
            raise AlpacaAPIError(f"Failed to get account: {str(e)}")
        except Exception as e:
            raise AlpacaConnectionError(f"Connection error: {str(e)}")

    async def get_positions(self) -> List[Dict[str, Any]]:
        """Get all positions"""
        try:
            positions = self.client.list_positions()
            return [
                {
                    "asset_id": position.asset_id,
                    "symbol": position.symbol,
                    "exchange": position.exchange,
                    "asset_class": position.asset_class,
                    "qty": float(position.qty),
                    "side": position.side,
                    "market_value": float(position.market_value),
                    "cost_basis": float(position.cost_basis),
                    "unrealized_pl": float(position.unrealized_pl),
                    "unrealized_plpc": float(position.unrealized_plpc),
                    "unrealized_intraday_pl": float(position.unrealized_intraday_pl),
                    "unrealized_intraday_plpc": float(
                        position.unrealized_intraday_plpc
                    ),
                    "current_price": float(position.current_price),
                    "lastday_price": float(position.lastday_price),
                    "change_today": float(position.change_today),
                    "avg_entry_price": float(position.avg_entry_price),
                }
                for position in positions
            ]
        except APIError as e:
            raise AlpacaAPIError(f"Failed to get positions: {str(e)}")
        except Exception as e:
            raise AlpacaConnectionError(f"Connection error: {str(e)}")

    async def get_orders(
        self, status: str = "open", limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get orders"""
        try:
            orders = self.client.list_orders(status=status, limit=limit)
            return [
                {
                    "id": order.id,
                    "client_order_id": order.client_order_id,
                    "created_at": (
                        order.created_at.isoformat() if order.created_at else None
                    ),
                    "updated_at": (
                        order.updated_at.isoformat() if order.updated_at else None
                    ),
                    "submitted_at": (
                        order.submitted_at.isoformat() if order.submitted_at else None
                    ),
                    "filled_at": (
                        order.filled_at.isoformat() if order.filled_at else None
                    ),
                    "expired_at": (
                        order.expired_at.isoformat() if order.expired_at else None
                    ),
                    "canceled_at": (
                        order.canceled_at.isoformat() if order.canceled_at else None
                    ),
                    "failed_at": (
                        order.failed_at.isoformat() if order.failed_at else None
                    ),
                    "replaced_at": (
                        order.replaced_at.isoformat() if order.replaced_at else None
                    ),
                    "replaced_by": order.replaced_by,
                    "replaces": order.replaces,
                    "asset_id": order.asset_id,
                    "symbol": order.symbol,
                    "asset_class": order.asset_class,
                    "notional": float(order.notional) if order.notional else None,
                    "qty": float(order.qty) if order.qty else None,
                    "filled_qty": float(order.filled_qty) if order.filled_qty else None,
                    "filled_avg_price": (
                        float(order.filled_avg_price)
                        if order.filled_avg_price
                        else None
                    ),
                    "order_class": order.order_class,
                    "order_type": order.order_type,
                    "type": order.type,
                    "side": order.side,
                    "time_in_force": order.time_in_force,
                    "limit_price": (
                        float(order.limit_price) if order.limit_price else None
                    ),
                    "stop_price": float(order.stop_price) if order.stop_price else None,
                    "status": order.status,
                    "extended_hours": order.extended_hours,
                    "legs": order.legs,
                    "trail_percent": (
                        float(order.trail_percent) if order.trail_percent else None
                    ),
                    "trail_price": (
                        float(order.trail_price) if order.trail_price else None
                    ),
                    "hwm": float(order.hwm) if order.hwm else None,
                }
                for order in orders
            ]
        except APIError as e:
            raise AlpacaAPIError(f"Failed to get orders: {str(e)}")
        except Exception as e:
            raise AlpacaConnectionError(f"Connection error: {str(e)}")

    async def get_clock(self) -> Dict[str, Any]:
        """Get market clock"""
        try:
            clock = self.client.get_clock()
            return {
                "timestamp": clock.timestamp.isoformat() if clock.timestamp else None,
                "is_open": clock.is_open,
                "next_open": clock.next_open.isoformat() if clock.next_open else None,
                "next_close": (
                    clock.next_close.isoformat() if clock.next_close else None
                ),
            }
        except APIError as e:
            raise AlpacaAPIError(f"Failed to get clock: {str(e)}")
        except Exception as e:
            raise AlpacaConnectionError(f"Connection error: {str(e)}")

    async def close_position(self, symbol: str) -> Dict[str, Any]:
        """Close a position"""
        try:
            result = self.client.close_position(symbol)
            return {
                "id": result.id,
                "client_order_id": result.client_order_id,
                "created_at": (
                    result.created_at.isoformat() if result.created_at else None
                ),
                "symbol": result.symbol,
                "qty": float(result.qty) if result.qty else None,
                "side": result.side,
                "status": result.status,
            }
        except APIError as e:
            raise AlpacaAPIError(f"Failed to close position {symbol}: {str(e)}")
        except Exception as e:
            raise AlpacaConnectionError(f"Connection error: {str(e)}")

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an order"""
        try:
            self.client.cancel_order(order_id)
            return True
        except APIError as e:
            raise AlpacaAPIError(f"Failed to cancel order {order_id}: {str(e)}")
        except Exception as e:
            raise AlpacaConnectionError(f"Connection error: {str(e)}")

    async def place_order(
        self,
        symbol: str,
        qty: int,
        side: str,
        order_type: str = "market",
        time_in_force: str = "day",
        limit_price: Optional[float] = None,
        stop_price: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Place an order"""
        try:
            order = self.client.submit_order(
                symbol=symbol,
                qty=qty,
                side=side,
                type=order_type,
                time_in_force=time_in_force,
                limit_price=limit_price,
                stop_price=stop_price,
            )
            return {
                "id": order.id,
                "client_order_id": order.client_order_id,
                "created_at": (
                    order.created_at.isoformat() if order.created_at else None
                ),
                "symbol": order.symbol,
                "qty": float(order.qty) if order.qty else None,
                "side": order.side,
                "order_type": order.order_type,
                "status": order.status,
            }
        except APIError as e:
            raise AlpacaAPIError(f"Failed to place order: {str(e)}")
        except Exception as e:
            raise AlpacaConnectionError(f"Connection error: {str(e)}")
