"""
API routes for financial statements data
"""

from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from src.shared.database.base import db_transaction
from src.shared.database.models.financial_statements import FinancialStatement

router = APIRouter(prefix="/api/financial-statements", tags=["financial-statements"])


@router.get("/{symbol}")
async def get_financial_statements(
    symbol: str,
    statement_type: Optional[str] = Query(
        None, description="Type: income, balance_sheet, cash_flow"
    ),
    period_type: Optional[str] = Query(None, description="Type: annual, quarterly"),
    limit: int = Query(10, description="Number of statements to return"),
) -> dict:
    """
    Get financial statements for a symbol

    Args:
        symbol: Stock symbol
        statement_type: Type of statement (income, balance_sheet, cash_flow)
        period_type: Period type (annual, quarterly)
        limit: Maximum number of statements to return

    Returns:
        List of financial statements
    """
    symbol = symbol.upper()

    try:
        with db_transaction() as session:
            # Build query
            query = select(FinancialStatement).where(
                FinancialStatement.symbol == symbol
            )

            if statement_type:
                query = query.where(FinancialStatement.statement_type == statement_type)

            if period_type:
                query = query.where(FinancialStatement.period_type == period_type)

            # Order by period end (most recent first)
            query = query.order_by(FinancialStatement.period_end.desc()).limit(limit)

            results = session.execute(query).scalars().all()

            if not results:
                return {
                    "success": True,
                    "symbol": symbol,
                    "count": 0,
                    "statements": [],
                    "message": "No financial statements data available",
                }

            statements = [stmt.to_dict() for stmt in results]

            return {
                "success": True,
                "symbol": symbol,
                "count": len(statements),
                "statements": statements,
            }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch financial statements: {str(e)}"
        )


@router.get("/{symbol}/latest")
async def get_latest_financial_statements(symbol: str) -> dict:
    """
    Get the latest financial statements for each type

    Args:
        symbol: Stock symbol

    Returns:
        Latest statements for each type and period
    """
    symbol = symbol.upper()

    try:
        with db_transaction() as session:
            # Get latest annual statements
            annual_query = (
                select(FinancialStatement)
                .where(FinancialStatement.symbol == symbol)
                .where(FinancialStatement.period_type == "annual")
                .order_by(FinancialStatement.period_end.desc())
            )

            # Get latest quarterly statements
            quarterly_query = (
                select(FinancialStatement)
                .where(FinancialStatement.symbol == symbol)
                .where(FinancialStatement.period_type == "quarterly")
                .order_by(FinancialStatement.period_end.desc())
            )

            annual_results = session.execute(annual_query).scalars().all()
            quarterly_results = session.execute(quarterly_query).scalars().all()

            # Group by statement type
            annual_by_type = {}
            quarterly_by_type = {}

            for stmt in annual_results:
                if stmt.statement_type not in annual_by_type:
                    annual_by_type[stmt.statement_type] = stmt.to_dict()

            for stmt in quarterly_results:
                if stmt.statement_type not in quarterly_by_type:
                    quarterly_by_type[stmt.statement_type] = stmt.to_dict()

            return {
                "success": True,
                "symbol": symbol,
                "annual": annual_by_type,
                "quarterly": quarterly_by_type,
            }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch latest financial statements: {str(e)}",
        )


@router.get("/{symbol}/line-item/{line_item}")
async def get_line_item_history(
    symbol: str,
    line_item: str,
    statement_type: str = Query(
        ..., description="Type: income, balance_sheet, cash_flow"
    ),
    period_type: str = Query("annual", description="Type: annual, quarterly"),
    limit: int = Query(20, description="Number of periods to return"),
) -> dict:
    """
    Get historical data for a specific line item

    Args:
        symbol: Stock symbol
        line_item: Financial statement line item (e.g., 'Total Revenue', 'Net Income')
        statement_type: Type of statement
        period_type: Period type
        limit: Number of periods to return

    Returns:
        Historical line item data
    """
    symbol = symbol.upper()

    try:
        with db_transaction() as session:
            query = (
                select(FinancialStatement)
                .where(FinancialStatement.symbol == symbol)
                .where(FinancialStatement.statement_type == statement_type)
                .where(FinancialStatement.period_type == period_type)
                .order_by(FinancialStatement.period_end.desc())
                .limit(limit)
            )

            results = session.execute(query).scalars().all()

            if not results:
                return {
                    "success": True,
                    "symbol": symbol,
                    "line_item": line_item,
                    "count": 0,
                    "data": [],
                    "message": f"No data available for {line_item}",
                }

            # Extract line item data
            line_item_data = []
            for stmt in results:
                value = stmt.get_line_item(line_item)
                if value is not None:
                    line_item_data.append(
                        {
                            "period_end": stmt.period_end.isoformat(),
                            "fiscal_year": stmt.fiscal_year,
                            "fiscal_quarter": stmt.fiscal_quarter,
                            "value": value,
                            "formatted_value": stmt.get_formatted_line_item(
                                line_item, "currency"
                            ),
                        }
                    )

            return {
                "success": True,
                "symbol": symbol,
                "line_item": line_item,
                "statement_type": statement_type,
                "period_type": period_type,
                "count": len(line_item_data),
                "data": line_item_data,
            }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch line item history: {str(e)}"
        )


@router.get("")
async def list_available_symbols() -> dict:
    """
    Get list of symbols that have financial statements data

    Returns:
        List of symbols with statement counts
    """
    try:
        with db_transaction() as session:
            from sqlalchemy import func

            query = (
                select(
                    FinancialStatement.symbol,
                    FinancialStatement.statement_type,
                    FinancialStatement.period_type,
                    func.count(FinancialStatement.id).label("statement_count"),
                )
                .group_by(
                    FinancialStatement.symbol,
                    FinancialStatement.statement_type,
                    FinancialStatement.period_type,
                )
                .order_by(FinancialStatement.symbol)
            )

            results = session.execute(query).all()

            # Group by symbol
            symbols = {}
            for row in results:
                symbol = row[0]
                if symbol not in symbols:
                    symbols[symbol] = {
                        "symbol": symbol,
                        "statements": {},
                        "total_count": 0,
                    }

                stmt_type = row[1]
                period_type = row[2]
                count = row[3]

                if stmt_type not in symbols[symbol]["statements"]:
                    symbols[symbol]["statements"][stmt_type] = {}

                symbols[symbol]["statements"][stmt_type][period_type] = count
                symbols[symbol]["total_count"] += count

            return {
                "success": True,
                "count": len(symbols),
                "symbols": list(symbols.values()),
            }

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch symbols: {str(e)}"
        )
