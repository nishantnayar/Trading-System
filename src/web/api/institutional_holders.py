"""
API routes for institutional holders data
"""

from typing import Dict, List

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

            # Calculate percentages if missing by getting shares outstanding
            has_percentages = any(h.get("percent_held") is not None for h in holders)
            if holders and not has_percentages:
                holders = await _calculate_missing_percentages(symbol, holders)

            return {
                "success": True,
                "symbol": symbol,
                "count": len(holders),
                "holders": holders,
            }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch institutional holders: {str(e)}",
        )


@router.get("")
async def list_available_symbols() -> dict:
    """
    Get list of symbols with institutional holders data

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


async def _calculate_missing_percentages(
    symbol: str, holders: List[Dict]
) -> List[Dict]:
    """
    Calculate missing percentage holdings using shares outstanding data
    """
    try:
        # Try to get shares outstanding from key statistics
        with db_transaction() as session:
            from src.shared.database.models.key_statistics import KeyStatistics

            query = (
                select(KeyStatistics.shares_outstanding)
                .where(KeyStatistics.symbol == symbol)
                .order_by(KeyStatistics.date.desc())
                .limit(1)
            )

            result = session.execute(query).scalar()

            if result is not None and result > 0:
                shares_outstanding = float(result)

                # Calculate percentages for each holder
                for holder in holders:
                    shares = holder.get("shares")
                    if shares is not None and shares > 0:
                        percentage = (holder["shares"] / shares_outstanding) * 100
                        holder["percent_held"] = percentage
                        holder["percent_held_display"] = f"{percentage:.2f}%"
                    else:
                        holder["percent_held"] = 0.0
                        holder["percent_held_display"] = "0.00%"
            else:
                # Fallback: use relative percentages based on total shares
                total_institutional_shares = sum(
                    h.get("shares", 0) for h in holders if h.get("shares")
                )

                if total_institutional_shares and total_institutional_shares > 0:
                    for holder in holders:
                        shares = holder.get("shares")
                        if shares is not None and shares > 0:
                            percentage = (
                                holder["shares"] / total_institutional_shares
                            ) * 100
                            holder["percent_held"] = percentage
                            holder["percent_held_display"] = f"{percentage:.2f}%"
                        else:
                            holder["percent_held"] = 0.0
                            holder["percent_held_display"] = "0.00%"
                else:
                    # No shares data available
                    for holder in holders:
                        holder["percent_held"] = 0.0
                        holder["percent_held_display"] = "N/A"

    except Exception:
        # If calculation fails, set all to N/A
        for holder in holders:
            holder["percent_held"] = 0.0
            holder["percent_held_display"] = "N/A"

    return holders
