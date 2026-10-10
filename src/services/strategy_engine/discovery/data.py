"""
Price and symbol loaders for discovery.
"""

from typing import Dict, List

from sqlalchemy import select

from src.shared.database.base import db_readonly_session
from src.shared.database.models.symbols import Symbol
from src.shared.market_data import get_close_panel


def get_active_symbols() -> List[Dict]:
    """Fetch all active symbols with sector info from DB."""
    with db_readonly_session() as session:
        stmt = (
            select(Symbol.symbol, Symbol.sector, Symbol.name)
            .where(Symbol.status == "active")
            .order_by(Symbol.symbol)
        )
        rows = session.execute(stmt).fetchall()
    return [{"symbol": r.symbol, "sector": r.sector, "name": r.name} for r in rows]


# Discovery historically called this get_hourly_closes; it is the shared loader.
get_hourly_closes = get_close_panel
