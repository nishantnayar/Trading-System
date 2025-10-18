"""
API routes for key statistics data
"""

from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import select

from src.shared.database.base import db_transaction
from src.shared.database.models.key_statistics import KeyStatistics

router = APIRouter(prefix="/api/key-statistics", tags=["key-statistics"])


@router.get("/{symbol}")
async def get_key_statistics(
    symbol: str,
    stats_date: Optional[str] = Query(None, description="Statistics date (YYYY-MM-DD)"),
) -> dict:
    """
    Get key statistics for a symbol

    Args:
        symbol: Stock symbol
        stats_date: Optional date filter (defaults to latest)

    Returns:
        Key statistics data
    """
    symbol = symbol.upper()

    try:
        with db_transaction() as session:
            query = select(KeyStatistics).where(KeyStatistics.symbol == symbol)

            if stats_date and isinstance(stats_date, str):
                query = query.where(
                    KeyStatistics.date == date.fromisoformat(stats_date)
                )

            query = query.order_by(KeyStatistics.date.desc())

            result = session.execute(query).first()

            if not result:
                raise HTTPException(
                    status_code=404, detail=f"No key statistics found for {symbol}"
                )

            stats = result[0]

            return {
                "success": True,
                "symbol": stats.symbol,
                "date": stats.date.isoformat(),
                "data_source": stats.data_source,
                "data": {
                    # Valuation metrics
                    "valuation": {
                        "market_cap": stats.market_cap,
                        "market_cap_display": stats.market_cap_display,
                        "enterprise_value": stats.enterprise_value,
                        "trailing_pe": (
                            float(stats.trailing_pe) if stats.trailing_pe else None
                        ),
                        "forward_pe": (
                            float(stats.forward_pe) if stats.forward_pe else None
                        ),
                        "peg_ratio": (
                            float(stats.peg_ratio) if stats.peg_ratio else None
                        ),
                        "price_to_book": (
                            float(stats.price_to_book) if stats.price_to_book else None
                        ),
                        "price_to_sales": (
                            float(stats.price_to_sales)
                            if stats.price_to_sales
                            else None
                        ),
                        "enterprise_to_revenue": (
                            float(stats.enterprise_to_revenue)
                            if stats.enterprise_to_revenue
                            else None
                        ),
                        "enterprise_to_ebitda": (
                            float(stats.enterprise_to_ebitda)
                            if stats.enterprise_to_ebitda
                            else None
                        ),
                    },
                    # Profitability metrics
                    "profitability": {
                        "profit_margin": (
                            float(stats.profit_margin) if stats.profit_margin else None
                        ),
                        "profit_margin_display": stats.profit_margin_display,
                        "operating_margin": (
                            float(stats.operating_margin)
                            if stats.operating_margin
                            else None
                        ),
                        "return_on_assets": (
                            float(stats.return_on_assets)
                            if stats.return_on_assets
                            else None
                        ),
                        "return_on_equity": (
                            float(stats.return_on_equity)
                            if stats.return_on_equity
                            else None
                        ),
                        "roe_display": stats.roe_display,
                        "gross_margin": (
                            float(stats.gross_margin) if stats.gross_margin else None
                        ),
                        "ebitda_margin": (
                            float(stats.ebitda_margin) if stats.ebitda_margin else None
                        ),
                    },
                    # Financial health
                    "financial_health": {
                        "revenue": stats.revenue,
                        "revenue_per_share": (
                            float(stats.revenue_per_share)
                            if stats.revenue_per_share
                            else None
                        ),
                        "earnings_per_share": (
                            float(stats.earnings_per_share)
                            if stats.earnings_per_share
                            else None
                        ),
                        "total_cash": stats.total_cash,
                        "total_debt": stats.total_debt,
                        "debt_to_equity": (
                            float(stats.debt_to_equity)
                            if stats.debt_to_equity
                            else None
                        ),
                        "debt_to_equity_display": stats.debt_to_equity_display,
                        "current_ratio": (
                            float(stats.current_ratio) if stats.current_ratio else None
                        ),
                        "quick_ratio": (
                            float(stats.quick_ratio) if stats.quick_ratio else None
                        ),
                        "free_cash_flow": stats.free_cash_flow,
                        "operating_cash_flow": stats.operating_cash_flow,
                    },
                    # Growth metrics
                    "growth": {
                        "revenue_growth": (
                            float(stats.revenue_growth)
                            if stats.revenue_growth
                            else None
                        ),
                        "earnings_growth": (
                            float(stats.earnings_growth)
                            if stats.earnings_growth
                            else None
                        ),
                    },
                    # Trading metrics
                    "trading": {
                        "beta": float(stats.beta) if stats.beta else None,
                        "fifty_two_week_high": (
                            float(stats.fifty_two_week_high)
                            if stats.fifty_two_week_high
                            else None
                        ),
                        "fifty_two_week_low": (
                            float(stats.fifty_two_week_low)
                            if stats.fifty_two_week_low
                            else None
                        ),
                        "fifty_day_average": (
                            float(stats.fifty_day_average)
                            if stats.fifty_day_average
                            else None
                        ),
                        "two_hundred_day_average": (
                            float(stats.two_hundred_day_average)
                            if stats.two_hundred_day_average
                            else None
                        ),
                        "average_volume": stats.average_volume,
                    },
                    # Dividend metrics
                    "dividends": {
                        "dividend_yield": (
                            float(stats.dividend_yield)
                            if stats.dividend_yield
                            else None
                        ),
                        "dividend_yield_display": stats.dividend_yield_display,
                        "dividend_rate": (
                            float(stats.dividend_rate) if stats.dividend_rate else None
                        ),
                        "payout_ratio": (
                            float(stats.payout_ratio) if stats.payout_ratio else None
                        ),
                    },
                    # Share information
                    "shares": {
                        "shares_outstanding": stats.shares_outstanding,
                        "float_shares": stats.float_shares,
                        "shares_short": stats.shares_short,
                        "short_ratio": (
                            float(stats.short_ratio) if stats.short_ratio else None
                        ),
                        "held_percent_insiders": (
                            float(stats.held_percent_insiders)
                            if stats.held_percent_insiders
                            else None
                        ),
                        "held_percent_institutions": (
                            float(stats.held_percent_institutions)
                            if stats.held_percent_institutions
                            else None
                        ),
                    },
                },
                "updated_at": (
                    stats.updated_at.isoformat() if stats.updated_at else None
                ),
            }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch key statistics: {str(e)}"
        )


@router.get("")
async def list_available_symbols() -> dict:
    """
    Get list of symbols that have key statistics data

    Returns:
        List of symbols with their latest statistics date
    """
    try:
        with db_transaction() as session:
            query = (
                select(KeyStatistics.symbol, KeyStatistics.date)
                .order_by(KeyStatistics.symbol, KeyStatistics.date.desc())
                .distinct(KeyStatistics.symbol)
            )

            results = session.execute(query).all()

            symbols = [
                {"symbol": row[0], "latest_date": row[1].isoformat()} for row in results
            ]

            return {"success": True, "count": len(symbols), "symbols": symbols}

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch symbols: {str(e)}"
        )
