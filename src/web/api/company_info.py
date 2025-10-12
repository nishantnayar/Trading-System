"""
Company Info API endpoints for trading dashboard
"""

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import distinct, func, select

from src.shared.database.base import db_transaction
from src.shared.database.models.company_info import CompanyInfo

router = APIRouter(prefix="/api/company-info", tags=["company-info"])


class CompanyInfoResponse(BaseModel):
    """Company information response model"""

    symbol: str
    name: Optional[str]
    sector: Optional[str]
    industry: Optional[str]
    description: Optional[str]
    website: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    city: Optional[str]
    state: Optional[str]
    zip: Optional[str]
    country: Optional[str]
    employees: Optional[int]
    market_cap: Optional[int]
    market_cap_billions: Optional[float]
    currency: Optional[str]
    exchange: Optional[str]
    quote_type: Optional[str]
    data_source: str


@router.get("/filters/sectors", response_model=List[str])
async def get_sectors() -> List[str]:
    """Get list of unique sectors"""
    try:
        with db_transaction() as session:
            query = (
                select(CompanyInfo.sector)
                .where(CompanyInfo.sector.isnot(None))
                .distinct()
                .order_by(CompanyInfo.sector)
            )

            result = session.execute(query)
            sectors = [row[0] for row in result.fetchall() if row[0]]

            return sectors

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get sectors: {str(e)}")


@router.get("/filters/industries", response_model=List[str])
async def get_industries(
    sector: Optional[str] = Query(
        default=None, description="Filter industries by sector"
    )
) -> List[str]:
    """Get list of unique industries, optionally filtered by sector"""
    try:
        with db_transaction() as session:
            query = select(CompanyInfo.industry).where(CompanyInfo.industry.isnot(None))

            # Add sector filter if provided
            if sector:
                query = query.where(CompanyInfo.sector == sector)

            query = query.distinct().order_by(CompanyInfo.industry)

            result = session.execute(query)
            industries = [row[0] for row in result.fetchall() if row[0]]

            return industries

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get industries: {str(e)}"
        )


@router.get("/filters/symbols", response_model=List[str])
async def get_symbols_by_filter(
    sector: Optional[str] = Query(default=None, description="Filter by sector"),
    industry: Optional[str] = Query(default=None, description="Filter by industry"),
) -> List[str]:
    """Get list of symbols filtered by sector and/or industry"""
    try:
        with db_transaction() as session:
            query = select(CompanyInfo.symbol)

            # Add filters if provided
            if sector:
                query = query.where(CompanyInfo.sector == sector)
            if industry:
                query = query.where(CompanyInfo.industry == industry)

            query = query.order_by(CompanyInfo.symbol)

            result = session.execute(query)
            symbols = [row[0] for row in result.fetchall()]

            return symbols

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get symbols: {str(e)}")


@router.get("/{symbol}", response_model=CompanyInfoResponse)
async def get_company_info(symbol: str) -> CompanyInfoResponse:
    """Get company information for a specific symbol"""
    try:
        symbol = symbol.upper()

        with db_transaction() as session:
            company = session.scalar(
                select(CompanyInfo).where(CompanyInfo.symbol == symbol)
            )

            if not company:
                raise HTTPException(
                    status_code=404, detail=f"No company info found for symbol {symbol}"
                )

            return CompanyInfoResponse(
                symbol=str(company.symbol),
                name=company.name,
                sector=company.sector,
                industry=company.industry,
                description=company.description,
                website=company.website,
                phone=company.phone,
                address=company.address,
                city=company.city,
                state=company.state,
                zip=company.zip,
                country=company.country,
                employees=company.employees,
                market_cap=company.market_cap,
                market_cap_billions=company.market_cap_billions,
                currency=company.currency,
                exchange=company.exchange,
                quote_type=company.quote_type,
                data_source=str(company.data_source),
            )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get company info for {symbol}: {str(e)}",
        )
