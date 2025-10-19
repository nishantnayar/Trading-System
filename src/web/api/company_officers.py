"""
API routes for company officers data
"""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from src.shared.database.base import db_transaction
from src.shared.database.models.company_officers import CompanyOfficer

router = APIRouter(prefix="/api/company-officers", tags=["company-officers"])


@router.get("/{symbol}")
async def get_company_officers(
    symbol: str,
    limit: int = Query(50, description="Number of officers to return"),
) -> dict:
    """
    Get company officers for a symbol

    Args:
        symbol: Stock symbol
        limit: Maximum number of officers to return (default: 50)

    Returns:
        List of company officers
    """
    symbol = symbol.upper()

    try:
        with db_transaction() as session:
            # Get officers ordered by total pay (highest first)
            query = (
                select(CompanyOfficer)
                .where(CompanyOfficer.symbol == symbol)
                .order_by(CompanyOfficer.total_pay.desc().nulls_last())
                .limit(limit)
            )

            results = session.execute(query).scalars().all()

            if not results:
                return {
                    "success": True,
                    "symbol": symbol,
                    "count": 0,
                    "officers": [],
                    "message": "No company officers data available",
                }

            officers = [officer.to_dict() for officer in results]

            return {
                "success": True,
                "symbol": symbol,
                "count": len(officers),
                "officers": officers,
            }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch company officers: {str(e)}"
        )


@router.get("/{symbol}/by-title")
async def get_officers_by_title(
    symbol: str,
    title_filter: Optional[str] = Query(
        None, description="Filter by title (e.g., 'CEO', 'CFO')"
    ),
) -> dict:
    """
    Get company officers grouped by title

    Args:
        symbol: Stock symbol
        title_filter: Optional title filter

    Returns:
        Officers grouped by title
    """
    symbol = symbol.upper()

    try:
        with db_transaction() as session:
            query = select(CompanyOfficer).where(CompanyOfficer.symbol == symbol)

            if title_filter:
                query = query.where(CompanyOfficer.title.ilike(f"%{title_filter}%"))

            query = query.order_by(
                CompanyOfficer.title, CompanyOfficer.total_pay.desc().nulls_last()
            )

            results = session.execute(query).scalars().all()

            if not results:
                return {
                    "success": True,
                    "symbol": symbol,
                    "count": 0,
                    "officers_by_title": {},
                    "message": "No company officers data available",
                }

            # Group by title
            officers_by_title: Dict[str, List[Dict[str, Any]]] = {}
            for officer in results:
                title = str(officer.title) if officer.title else "Unknown"
                if title not in officers_by_title:
                    officers_by_title[title] = []
                officers_by_title[title].append(officer.to_dict())

            return {
                "success": True,
                "symbol": symbol,
                "count": len(results),
                "officers_by_title": officers_by_title,
            }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch officers by title: {str(e)}"
        )


@router.get("/{symbol}/compensation")
async def get_compensation_summary(symbol: str) -> dict:
    """
    Get compensation summary for company officers

    Args:
        symbol: Stock symbol

    Returns:
        Compensation statistics
    """
    symbol = symbol.upper()

    try:
        with db_transaction() as session:
            from sqlalchemy import func

            # Get compensation statistics
            query = (
                select(
                    func.count(CompanyOfficer.id).label("total_officers"),
                    func.avg(CompanyOfficer.total_pay).label("avg_total_pay"),
                    func.max(CompanyOfficer.total_pay).label("max_total_pay"),
                    func.min(CompanyOfficer.total_pay).label("min_total_pay"),
                    func.sum(CompanyOfficer.total_pay).label("sum_total_pay"),
                )
                .where(CompanyOfficer.symbol == symbol)
                .where(CompanyOfficer.total_pay.isnot(None))
            )

            result = session.execute(query).first()

            if not result or result.total_officers == 0:
                return {
                    "success": True,
                    "symbol": symbol,
                    "message": "No compensation data available",
                }

            # Format compensation values (convert from cents to dollars)
            avg_pay = result.avg_total_pay / 100 if result.avg_total_pay else 0
            max_pay = result.max_total_pay / 100 if result.max_total_pay else 0
            min_pay = result.min_total_pay / 100 if result.min_total_pay else 0
            total_pay = result.sum_total_pay / 100 if result.sum_total_pay else 0

            return {
                "success": True,
                "symbol": symbol,
                "total_officers": result.total_officers,
                "compensation": {
                    "average": f"${avg_pay:,.0f}",
                    "highest": f"${max_pay:,.0f}",
                    "lowest": f"${min_pay:,.0f}",
                    "total": f"${total_pay:,.0f}",
                },
                "raw_values": {
                    "average": avg_pay,
                    "highest": max_pay,
                    "lowest": min_pay,
                    "total": total_pay,
                },
            }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch compensation summary: {str(e)}"
        )


@router.get("")
async def list_available_symbols() -> dict:
    """
    Get list of symbols that have company officers data

    Returns:
        List of symbols with officer counts
    """
    try:
        with db_transaction() as session:
            from sqlalchemy import func

            query = (
                select(
                    CompanyOfficer.symbol,
                    func.count(CompanyOfficer.id).label("officer_count"),
                )
                .group_by(CompanyOfficer.symbol)
                .order_by(CompanyOfficer.symbol)
            )

            results = session.execute(query).all()

            symbols = [{"symbol": row[0], "officer_count": row[1]} for row in results]

            return {"success": True, "count": len(symbols), "symbols": symbols}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch symbols: {str(e)}"
        )
