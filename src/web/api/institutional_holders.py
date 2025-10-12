"""
API routes for institutional holders data
"""

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from src.shared.database.base import db_transaction
from src.shared.database.models.institutional_holders import InstitutionalHolder

router = APIRouter(prefix="/api/institutional-holders", tags=["institutional-holders"])


@router.get("/{symbol}")
async def get_institutional_holders(
    symbol: str,
    limit: int = Query(10, description="Number of top holders to return"),
) -> dict:
    """
    Get institutional holders for a symbol

    Args:
        symbol: Stock symbol
        limit: Maximum number of holders to return (default: 10)

    Returns:
        List of institutional holders
    """
    symbol = symbol.upper()

    try:
        with db_transaction() as session:
            # Get latest holders ordered by shares
            query = (
                select(InstitutionalHolder)
                .where(InstitutionalHolder.symbol == symbol)
                .order_by(InstitutionalHolder.shares.desc())
                .limit(limit)
            )

            results = session.execute(query).scalars().all()

            if not results:
                return {
                    "success": True,
                    "symbol": symbol,
                    "count": 0,
                    "holders": [],
                    "message": "No institutional holders data available",
                }

            holders = [holder.to_dict() for holder in results]

            return {
                "success": True,
                "symbol": symbol,
                "count": len(holders),
                "holders": holders,
            }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch institutional holders: {str(e)}"
        )


@router.get("")
async def list_available_symbols() -> dict:
    """
    Get list of symbols that have institutional holders data

    Returns:
        List of symbols with holder count
    """
    try:
        with db_transaction() as session:
            from sqlalchemy import func

            query = (
                select(
                    InstitutionalHolder.symbol,
                    func.count(InstitutionalHolder.id).label("holder_count"),
                )
                .group_by(InstitutionalHolder.symbol)
                .order_by(InstitutionalHolder.symbol)
            )

            results = session.execute(query).all()

            symbols = [{"symbol": row[0], "holder_count": row[1]} for row in results]

            return {"success": True, "count": len(symbols), "symbols": symbols}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch symbols: {str(e)}"
        )
