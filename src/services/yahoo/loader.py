"""
Yahoo Finance Data Loader

Loads market data and fundamentals from Yahoo Finance into the database.
"""

import asyncio
import math
from datetime import date
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy.dialects.postgresql import insert

from src.services.data_ingestion.symbols import SymbolService
from src.shared.database.base import db_transaction
from src.shared.database.models.company_info import CompanyInfo
from src.shared.database.models.company_officers import CompanyOfficer
from src.shared.database.models.financial_statements import FinancialStatement
from src.shared.database.models.institutional_holders import InstitutionalHolder
from src.shared.database.models.key_statistics import KeyStatistics
from src.shared.database.models.market_data import MarketData
from src.shared.database.models.symbols import Symbol

from .client import YahooClient
from .exceptions import YahooAPIError


def safe_float_conversion(
    value: Any, max_value: float = 999999999.99
) -> Optional[float]:
    """
    Safely convert a value to float, handling infinity and NaN cases.

    Args:
        value: The value to convert
        max_value: Maximum allowed value (default: 999999999.99 to fit NUMERIC(10,2))

    Returns:
        Converted float value or None if invalid/infinite
    """
    if value is None:
        return None

    try:
        float_val = float(value)

        # Check for infinity or NaN
        if math.isinf(float_val) or math.isnan(float_val):
            logger.warning(
                f"Encountered invalid numeric value: {value}, converting to None"
            )
            return None

        # Check if value exceeds database precision limits
        if abs(float_val) > max_value:
            logger.warning(
                f"Value {float_val} exceeds maximum allowed value "
                f"{max_value}, converting to None"
            )
            return None

        return float_val

    except (ValueError, TypeError) as e:
        logger.warning(
            f"Failed to convert value {value} to float: {e}, converting to None"
        )
        return None


class YahooDataLoader:
    """Load data from Yahoo Finance into database"""

    def __init__(
        self,
        batch_size: int = 100,
        delay_between_requests: float = 0.5,
        data_source: str = "yahoo",
    ):
        """
        Initialize the Yahoo data loader

        Args:
            batch_size: Number of records to process in each batch
            delay_between_requests: Delay between requests (seconds)
            data_source: Data source identifier
        """
        self.client = YahooClient()
        self.batch_size = batch_size
        self.delay_between_requests = delay_between_requests
        self.data_source = data_source
        self.symbol_service = SymbolService()

    async def _update_symbol_status(
        self, 
        symbol: str, 
        status: str, 
        error_message: Optional[str] = None
    ) -> None:
        """Update symbol data ingestion status"""
        try:
            await self.symbol_service.update_symbol_data_status(
                symbol=symbol,
                date=date.today(),
                data_source=self.data_source,
                status=status,
                error_message=error_message,
            )
        except Exception as e:
            # Make this non-blocking - log warning but don't fail the main process
            logger.warning(f"Failed to update symbol status for {symbol}: {e}")

    async def load_market_data(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        interval: str = "1d",
    ) -> int:
        """
        Load OHLCV market data for a symbol

        Args:
            symbol: Stock symbol
            start_date: Start date for data
            end_date: End date for data
            interval: Data interval ('1d', '1h', '1m', etc.)

        Returns:
            Number of records loaded
        """
        symbol = symbol.upper()
        logger.info(f"Loading market data for {symbol} from Yahoo Finance")

        try:
            # Fetch data from Yahoo
            bars = await self.client.get_historical_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
                interval=interval,
            )

            if not bars:
                logger.warning(f"No market data found for {symbol}")
                return 0

            # Convert to database records
            records = []
            for bar in bars:
                record = MarketData(
                    symbol=symbol,
                    timestamp=bar.timestamp,
                    data_source=self.data_source,
                    open=bar.open,
                    high=bar.high,
                    low=bar.low,
                    close=bar.close,
                    volume=bar.volume,
                )
                records.append(record)

            # Insert into database
            inserted_count = await self._batch_insert_market_data(records)

            logger.info(f"Loaded {inserted_count} market data records for {symbol}")
            return inserted_count

        except YahooAPIError as e:
            logger.error(f"Yahoo API error for {symbol}: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to load market data for {symbol}: {e}")
            raise

    async def load_company_info(self, symbol: str) -> bool:
        """
        Load company information

        Args:
            symbol: Stock symbol

        Returns:
            True if successful
        """
        # Validate input
        if not symbol or symbol.strip() == "":
            raise ValueError("Symbol cannot be empty or None")

        symbol = symbol.upper()
        logger.info(f"Loading company info for {symbol} from Yahoo Finance")

        try:
            # Fetch company info from Yahoo
            company_data = await self.client.get_company_info(symbol)

            # Create or update database record
            with db_transaction() as session:
                # Use merge for upsert (insert or update)
                company_info = CompanyInfo(
                    symbol=symbol,
                    name=company_data.name,
                    sector=company_data.sector,
                    industry=company_data.industry,
                    description=company_data.description,
                    website=company_data.website,
                    phone=company_data.phone,
                    address=company_data.address,
                    city=company_data.city,
                    state=company_data.state,
                    zip=company_data.zip,
                    country=company_data.country,
                    employees=company_data.employees,
                    market_cap=company_data.market_cap,
                    currency=company_data.currency,
                    exchange=company_data.exchange,
                    quote_type=company_data.quote_type,
                    data_source=self.data_source,
                    additional_data=company_data.additional_data,
                )

                # Merge will update if exists, insert if new
                session.merge(company_info)
                session.commit()

            logger.info(f"Successfully loaded company info for {symbol}")
            return True

        except YahooAPIError:
            # Re-raise YahooAPIError as-is
            raise
        except Exception as e:
            logger.error(f"Failed to load company info for {symbol}: {e}")
            raise YahooAPIError(f"Failed to load company info for {symbol}: {e}")

    async def load_key_statistics(
        self, symbol: str, stats_date: Optional[date] = None
    ) -> bool:
        """
        Load key financial statistics for a symbol

        Args:
            symbol: Stock symbol
            stats_date: Date for the statistics (defaults to today)

        Returns:
            True if successful
        """
        symbol = symbol.upper()
        stats_date = stats_date or date.today()
        logger.info(f"Loading key statistics for {symbol} from Yahoo Finance")

        try:
            # Fetch key statistics from Yahoo
            stats_data = await self.client.get_key_statistics(symbol)

            # Create or update database record using upsert
            with db_transaction() as session:
                # Use PostgreSQL INSERT ... ON CONFLICT for upsert
                stmt = insert(KeyStatistics).values(
                    symbol=symbol,
                    date=stats_date,
                    data_source=self.data_source,
                    # Valuation metrics
                    market_cap=stats_data.market_cap,
                    enterprise_value=stats_data.enterprise_value,
                    trailing_pe=safe_float_conversion(stats_data.trailing_pe),
                    forward_pe=safe_float_conversion(stats_data.forward_pe),
                    peg_ratio=safe_float_conversion(stats_data.peg_ratio),
                    price_to_book=safe_float_conversion(stats_data.price_to_book),
                    price_to_sales=safe_float_conversion(stats_data.price_to_sales),
                    enterprise_to_revenue=safe_float_conversion(
                        stats_data.enterprise_to_revenue
                    ),
                    enterprise_to_ebitda=safe_float_conversion(
                        stats_data.enterprise_to_ebitda
                    ),
                    # Profitability metrics
                    profit_margin=safe_float_conversion(stats_data.profit_margin),
                    operating_margin=safe_float_conversion(stats_data.operating_margin),
                    return_on_assets=safe_float_conversion(stats_data.return_on_assets),
                    return_on_equity=safe_float_conversion(stats_data.return_on_equity),
                    gross_margin=safe_float_conversion(stats_data.gross_margin),
                    ebitda_margin=safe_float_conversion(stats_data.ebitda_margin),
                    # Financial health
                    revenue=stats_data.revenue,
                    revenue_per_share=safe_float_conversion(
                        stats_data.revenue_per_share
                    ),
                    earnings_per_share=safe_float_conversion(
                        stats_data.earnings_per_share
                    ),
                    total_cash=stats_data.total_cash,
                    total_debt=stats_data.total_debt,
                    debt_to_equity=safe_float_conversion(stats_data.debt_to_equity),
                    current_ratio=safe_float_conversion(stats_data.current_ratio),
                    quick_ratio=safe_float_conversion(stats_data.quick_ratio),
                    free_cash_flow=stats_data.free_cash_flow,
                    operating_cash_flow=stats_data.operating_cash_flow,
                    # Growth metrics
                    revenue_growth=safe_float_conversion(stats_data.revenue_growth),
                    earnings_growth=safe_float_conversion(stats_data.earnings_growth),
                    # Trading metrics
                    beta=safe_float_conversion(stats_data.beta),
                    fifty_two_week_high=safe_float_conversion(
                        stats_data.fifty_two_week_high
                    ),
                    fifty_two_week_low=safe_float_conversion(
                        stats_data.fifty_two_week_low
                    ),
                    fifty_day_average=safe_float_conversion(
                        stats_data.fifty_day_average
                    ),
                    two_hundred_day_average=safe_float_conversion(
                        stats_data.two_hundred_day_average
                    ),
                    average_volume=stats_data.average_volume,
                    # Dividend metrics
                    dividend_yield=safe_float_conversion(stats_data.dividend_yield),
                    dividend_rate=safe_float_conversion(stats_data.dividend_rate),
                    payout_ratio=safe_float_conversion(stats_data.payout_ratio),
                    # Share information
                    shares_outstanding=stats_data.shares_outstanding,
                    float_shares=stats_data.float_shares,
                    shares_short=stats_data.shares_short,
                    short_ratio=safe_float_conversion(stats_data.short_ratio),
                    held_percent_insiders=safe_float_conversion(
                        stats_data.held_percent_insiders
                    ),
                    held_percent_institutions=safe_float_conversion(
                        stats_data.held_percent_institutions
                    ),
                )

                # Update on conflict (upsert)
                stmt = stmt.on_conflict_do_update(
                    index_elements=["symbol", "date", "data_source"],
                    set_={
                        # Valuation metrics
                        "market_cap": stmt.excluded.market_cap,
                        "enterprise_value": stmt.excluded.enterprise_value,
                        "trailing_pe": stmt.excluded.trailing_pe,
                        "forward_pe": stmt.excluded.forward_pe,
                        "peg_ratio": stmt.excluded.peg_ratio,
                        "price_to_book": stmt.excluded.price_to_book,
                        "price_to_sales": stmt.excluded.price_to_sales,
                        "enterprise_to_revenue": stmt.excluded.enterprise_to_revenue,
                        "enterprise_to_ebitda": stmt.excluded.enterprise_to_ebitda,
                        # Profitability metrics
                        "profit_margin": stmt.excluded.profit_margin,
                        "operating_margin": stmt.excluded.operating_margin,
                        "return_on_assets": stmt.excluded.return_on_assets,
                        "return_on_equity": stmt.excluded.return_on_equity,
                        "gross_margin": stmt.excluded.gross_margin,
                        "ebitda_margin": stmt.excluded.ebitda_margin,
                        # Financial health
                        "revenue": stmt.excluded.revenue,
                        "revenue_per_share": stmt.excluded.revenue_per_share,
                        "earnings_per_share": stmt.excluded.earnings_per_share,
                        "total_cash": stmt.excluded.total_cash,
                        "total_debt": stmt.excluded.total_debt,
                        "debt_to_equity": stmt.excluded.debt_to_equity,
                        "current_ratio": stmt.excluded.current_ratio,
                        "quick_ratio": stmt.excluded.quick_ratio,
                        "free_cash_flow": stmt.excluded.free_cash_flow,
                        "operating_cash_flow": stmt.excluded.operating_cash_flow,
                        # Growth metrics
                        "revenue_growth": stmt.excluded.revenue_growth,
                        "earnings_growth": stmt.excluded.earnings_growth,
                        # Trading metrics
                        "beta": stmt.excluded.beta,
                        "fifty_two_week_high": stmt.excluded.fifty_two_week_high,
                        "fifty_two_week_low": stmt.excluded.fifty_two_week_low,
                        "fifty_day_average": stmt.excluded.fifty_day_average,
                        "two_hundred_day_average": (
                            stmt.excluded.two_hundred_day_average
                        ),
                        "average_volume": stmt.excluded.average_volume,
                        # Dividend metrics
                        "dividend_yield": stmt.excluded.dividend_yield,
                        "dividend_rate": stmt.excluded.dividend_rate,
                        "payout_ratio": stmt.excluded.payout_ratio,
                        # Share information
                        "shares_outstanding": stmt.excluded.shares_outstanding,
                        "float_shares": stmt.excluded.float_shares,
                        "shares_short": stmt.excluded.shares_short,
                        "short_ratio": stmt.excluded.short_ratio,
                        "held_percent_insiders": stmt.excluded.held_percent_insiders,
                        "held_percent_institutions": (
                            stmt.excluded.held_percent_institutions
                        ),
                        # Update metadata
                        "updated_at": stmt.excluded.updated_at,
                    },
                )

                session.execute(stmt)
                session.commit()

            logger.info(f"Successfully loaded key statistics for {symbol}")
            return True

        except Exception as e:
            logger.error(f"Failed to load key statistics for {symbol}: {e}")
            return False

    async def load_institutional_holders(self, symbol: str) -> int:
        """
        Load institutional holders for a symbol

        Args:
            symbol: Stock symbol

        Returns:
            Number of holders loaded
        """
        symbol = symbol.upper()
        logger.info(f"Loading institutional holders for {symbol} from Yahoo Finance")

        try:
            # Fetch institutional holders from Yahoo
            holders_data = await self.client.get_institutional_holders(symbol)

            if not holders_data:
                logger.warning(f"No institutional holders found for {symbol}")
                return 0

            # Insert into database using upsert
            loaded_count = 0

            with db_transaction() as session:
                for holder in holders_data:
                    stmt = insert(InstitutionalHolder).values(
                        symbol=symbol,
                        date_reported=holder.date_reported,
                        holder_name=holder.holder_name,
                        shares=holder.shares,
                        value=holder.value,
                        percent_held=(
                            float(holder.percent_held) if holder.percent_held else None
                        ),
                        data_source=self.data_source,
                    )

                    # Update on conflict
                    stmt = stmt.on_conflict_do_update(
                        index_elements=["symbol", "holder_name", "date_reported"],
                        set_={
                            "shares": stmt.excluded.shares,
                            "value": stmt.excluded.value,
                            "percent_held": stmt.excluded.percent_held,
                            "updated_at": stmt.excluded.updated_at,
                        },
                    )

                    session.execute(stmt)
                    loaded_count += 1

                session.commit()

            logger.info(
                f"Successfully loaded {loaded_count} institutional holders for {symbol}"
            )
            return loaded_count

        except Exception as e:
            logger.error(f"Failed to load institutional holders for {symbol}: {e}")
            return 0

    async def load_dividends(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> int:
        """
        Load dividend history

        Args:
            symbol: Stock symbol
            start_date: Start date
            end_date: End date

        Returns:
            Number of dividends loaded
        """
        # Note: This requires the dividends table to be created
        # We'll implement this after database migration
        logger.info(f"Dividend loading not yet implemented for {symbol}")
        return 0

    async def load_splits(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> int:
        """
        Load stock split history

        Args:
            symbol: Stock symbol
            start_date: Start date
            end_date: End date

        Returns:
            Number of splits loaded
        """
        # Note: This requires the stock_splits table to be created
        # We'll implement this after database migration
        logger.info(f"Split loading not yet implemented for {symbol}")
        return 0

    async def load_financial_statements(
        self, symbol: str, include_annual: bool = True, include_quarterly: bool = True
    ) -> List[Any]:
        """
        Load financial statements for a symbol

        Args:
            symbol: Stock symbol
            include_annual: Whether to load annual statements
            include_quarterly: Whether to load quarterly statements

        Returns:
            List of financial statements
        """
        statements = []

        try:
            # Load income statements
            if include_annual:
                income_annual = await self.client.get_financial_statements(
                    symbol, "income", "annual"
                )
                statements.extend(income_annual)

            if include_quarterly:
                income_quarterly = await self.client.get_financial_statements(
                    symbol, "income", "quarterly"
                )
                statements.extend(income_quarterly)

            # Load balance sheets
            if include_annual:
                balance_annual = await self.client.get_financial_statements(
                    symbol, "balance_sheet", "annual"
                )
                statements.extend(balance_annual)

            if include_quarterly:
                balance_quarterly = await self.client.get_financial_statements(
                    symbol, "balance_sheet", "quarterly"
                )
                statements.extend(balance_quarterly)

            # Load cash flow statements
            if include_annual:
                cashflow_annual = await self.client.get_financial_statements(
                    symbol, "cash_flow", "annual"
                )
                statements.extend(cashflow_annual)

            if include_quarterly:
                cashflow_quarterly = await self.client.get_financial_statements(
                    symbol, "cash_flow", "quarterly"
                )
                statements.extend(cashflow_quarterly)

            # Store in database
            with db_transaction() as session:
                for stmt_data in statements:
                    # Calculate fiscal year and quarter from period_end
                    fiscal_year = None
                    fiscal_quarter = None

                    if stmt_data.period_end:
                        # Detect fiscal year pattern for this company
                        fiscal_year, fiscal_quarter = self._detect_fiscal_year_quarter(
                            symbol, stmt_data.period_end
                        )

                    # Use upsert to handle duplicates
                    stmt = FinancialStatement(
                        symbol=symbol,
                        period_end=stmt_data.period_end,
                        statement_type=stmt_data.statement_type,
                        period_type=stmt_data.period_type,
                        fiscal_year=fiscal_year,
                        fiscal_quarter=fiscal_quarter,
                        data=stmt_data.data,
                    )

                    # Populate common metrics from JSONB data
                    stmt.populate_common_metrics()

                    # Use upsert with ON CONFLICT DO UPDATE

                    stmt_dict = {
                        "symbol": stmt.symbol,
                        "period_end": stmt.period_end,
                        "statement_type": stmt.statement_type,
                        "period_type": stmt.period_type,
                        "fiscal_year": stmt.fiscal_year,
                        "fiscal_quarter": stmt.fiscal_quarter,
                        "data": stmt.data,
                        "total_revenue": stmt.total_revenue,
                        "net_income": stmt.net_income,
                        "gross_profit": stmt.gross_profit,
                        "operating_income": stmt.operating_income,
                        "ebitda": stmt.ebitda,
                        "total_assets": stmt.total_assets,
                        "total_liabilities": stmt.total_liabilities,
                        "total_equity": stmt.total_equity,
                        "cash_and_equivalents": stmt.cash_and_equivalents,
                        "total_debt": stmt.total_debt,
                        "operating_cash_flow": stmt.operating_cash_flow,
                        "free_cash_flow": stmt.free_cash_flow,
                        "basic_eps": stmt.basic_eps,
                        "diluted_eps": stmt.diluted_eps,
                        "book_value_per_share": stmt.book_value_per_share,
                        "data_source": "yahoo",
                        "updated_at": stmt.updated_at,
                    }

                    insert_stmt = insert(FinancialStatement).values(**stmt_dict)
                    upsert_stmt = insert_stmt.on_conflict_do_update(
                        index_elements=[
                            "symbol",
                            "period_end",
                            "statement_type",
                            "period_type",
                        ],
                        set_={
                            "fiscal_year": insert_stmt.excluded.fiscal_year,
                            "fiscal_quarter": insert_stmt.excluded.fiscal_quarter,
                            "data": insert_stmt.excluded.data,
                            "total_revenue": insert_stmt.excluded.total_revenue,
                            "net_income": insert_stmt.excluded.net_income,
                            "gross_profit": insert_stmt.excluded.gross_profit,
                            "operating_income": (insert_stmt.excluded.operating_income),
                            "ebitda": insert_stmt.excluded.ebitda,
                            "total_assets": insert_stmt.excluded.total_assets,
                            "total_liabilities": (
                                insert_stmt.excluded.total_liabilities
                            ),
                            "total_equity": insert_stmt.excluded.total_equity,
                            "cash_and_equivalents": (
                                insert_stmt.excluded.cash_and_equivalents
                            ),
                            "total_debt": insert_stmt.excluded.total_debt,
                            "operating_cash_flow": (
                                insert_stmt.excluded.operating_cash_flow
                            ),
                            "free_cash_flow": insert_stmt.excluded.free_cash_flow,
                            "basic_eps": insert_stmt.excluded.basic_eps,
                            "diluted_eps": insert_stmt.excluded.diluted_eps,
                            "book_value_per_share": (
                                insert_stmt.excluded.book_value_per_share
                            ),
                            "data_source": insert_stmt.excluded.data_source,
                            "updated_at": insert_stmt.excluded.updated_at,
                        },
                    )

                    session.execute(upsert_stmt)

                session.commit()

            logger.info(f"Loaded {len(statements)} financial statements for {symbol}")
            return statements

        except Exception as e:
            logger.error(f"Failed to load financial statements for {symbol}: {e}")
            raise YahooAPIError(
                f"Failed to load financial statements for {symbol}: {str(e)}"
            )

    async def load_company_officers(self, symbol: str) -> List[Any]:
        """
        Load company officers for a symbol

        Args:
            symbol: Stock symbol

        Returns:
            List of company officers
        """
        symbol = symbol.upper().strip()
        if not symbol:
            raise ValueError("Symbol cannot be empty")

        try:
            logger.info(f"Loading company officers for {symbol}")
            officers_data = await self.client.get_company_officers(symbol)

            if not officers_data:
                logger.info(f"No officers data available for {symbol}")
                return []

            # Store in database using session.merge for each officer
            stored_count = 0
            with db_transaction() as session:
                for i, officer_data in enumerate(officers_data):
                    try:
                        # Validate officer data before storing
                        if not officer_data.name or not officer_data.name.strip():
                            logger.warning(f"Skipping officer {i+1} for {symbol}: empty name")
                            continue

                        officer_record = CompanyOfficer(
                            symbol=symbol,
                            name=officer_data.name.strip(),
                            title=officer_data.title.strip() if officer_data.title else None,
                            age=officer_data.age,
                            year_born=officer_data.year_born,
                            fiscal_year=officer_data.fiscal_year,
                            total_pay=officer_data.total_pay,
                            exercised_value=officer_data.exercised_value,
                            unexercised_value=officer_data.unexercised_value,
                            data_source='yahoo',
                        )

                        session.merge(officer_record)
                        stored_count += 1

                    except Exception as e:
                        logger.warning(f"Failed to store officer {i+1} for {symbol}: {e}")
                        continue

                session.commit()

            logger.info(f"Successfully loaded {stored_count}/{len(officers_data)} company officers for {symbol}")
            return officers_data

        except Exception as e:
            logger.error(f"Failed to load company officers for {symbol}: {e}")
            raise YahooAPIError(
                f"Failed to load company officers for {symbol}: {str(e)}"
            )

    async def load_all_data(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        include_fundamentals: bool = False,
        include_key_statistics: bool = False,
        include_institutional_holders: bool = False,
        include_financial_statements: bool = False,
        include_company_officers: bool = False,
        include_dividends: bool = False,
        include_splits: bool = False,
    ) -> Dict[str, int]:
        """
        Load all available data for a symbol

        Args:
            symbol: Stock symbol
            start_date: Start date for time-series data
            end_date: End date for time-series data
            include_fundamentals: Load company fundamentals
            include_key_statistics: Load key financial statistics
            include_institutional_holders: Load institutional holders
            include_financial_statements: Load financial statements
                (income, balance sheet, cash flow)
            include_company_officers: Load company officers and executives
            include_dividends: Load dividend history
            include_splits: Load split history

        Returns:
            Dictionary with counts of loaded records
        """
        symbol = symbol.upper()
        logger.info(f"Loading all data for {symbol} from Yahoo Finance")

        results = {
            "market_data": 0,
            "company_info": 0,
            "key_statistics": 0,
            "institutional_holders": 0,
            "financial_statements": 0,
            "company_officers": 0,
            "dividends": 0,
            "splits": 0,
        }

        try:
            # Load market data
            results["market_data"] = await self.load_market_data(
                symbol=symbol,
                start_date=start_date,
                end_date=end_date,
            )

            # Load fundamentals if requested
            if include_fundamentals:
                success = await self.load_company_info(symbol)
                results["company_info"] = 1 if success else 0

            # Load key statistics if requested
            if include_key_statistics:
                success = await self.load_key_statistics(symbol)
                results["key_statistics"] = 1 if success else 0

            # Load institutional holders if requested
            if include_institutional_holders:
                results["institutional_holders"] = (
                    await self.load_institutional_holders(symbol)
                )

            # Load financial statements if requested
            if include_financial_statements:
                statements = await self.load_financial_statements(symbol)
                results["financial_statements"] = len(statements)

            # Load company officers if requested
            if include_company_officers:
                officers = await self.load_company_officers(symbol)
                results["company_officers"] = len(officers)

            # Load dividends if requested
            if include_dividends:
                results["dividends"] = await self.load_dividends(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                )

            # Load splits if requested
            if include_splits:
                results["splits"] = await self.load_splits(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                )

            logger.info(f"Completed loading all data for {symbol}: {results}")
            return results

        except Exception as e:
            logger.error(f"Failed to load all data for {symbol}: {e}")
            raise

    async def load_all_symbols_data(
        self,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        interval: str = "1h",
        max_symbols: Optional[int] = None,
        include_fundamentals: bool = False,
        include_key_statistics: bool = False,
        include_institutional_holders: bool = False,
        include_financial_statements: bool = False,
        include_company_officers: bool = False,
    ) -> Dict[str, Any]:
        """
        Load market data for all active symbols

        Args:
            start_date: Start date for data
            end_date: End date for data
            interval: Data interval ('1h', '1d', etc.)
            max_symbols: Maximum number of symbols to process
            include_fundamentals: Load fundamentals data
            include_key_statistics: Load key statistics
            include_institutional_holders: Load institutional holders

        Returns:
            Dictionary with loading statistics
        """
        logger.info("Loading data for all active symbols from Yahoo Finance")

        # Get active symbols
        symbols = await self._get_active_symbols()
        if max_symbols:
            symbols = symbols[:max_symbols]

        logger.info(f"Processing {len(symbols)} symbols")

        stats: Dict[str, Any] = {
            "total_symbols": len(symbols),
            "successful": 0,
            "failed": 0,
            "total_records": 0,
            "errors": [],
        }

        for i, symbol in enumerate(symbols, 1):
            logger.info(f"Processing symbol {i}/{len(symbols)}: {symbol}")

            try:
                # Load market data
                records_count = await self.load_market_data(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    interval=interval,
                )
                stats["total_records"] += records_count

                # Load fundamentals if requested
                if include_fundamentals:
                    await self.load_company_info(symbol)

                # Load key statistics if requested
                if include_key_statistics:
                    await self.load_key_statistics(symbol)

                # Load institutional holders if requested
                if include_institutional_holders:
                    await self.load_institutional_holders(symbol)

                # Load financial statements if requested
                if include_financial_statements:
                    await self.load_financial_statements(symbol)

                # Load company officers if requested
                if include_company_officers:
                    await self.load_company_officers(symbol)

                stats["successful"] += 1
                
                # Update status for successful data loading
                await self._update_symbol_status(symbol, "success")

                # Add delay between requests
                if i < len(symbols):
                    await asyncio.sleep(self.delay_between_requests)

            except Exception as e:
                stats["failed"] += 1
                error_msg = f"Symbol {symbol}: {str(e)}"
                stats["errors"].append(error_msg)
                logger.error(error_msg)
                
                # Update status for failed data loading
                await self._update_symbol_status(symbol, "failed", error_msg)
                continue

        logger.info(f"Completed loading data. Stats: {stats}")
        return stats

    async def get_all_symbols(self) -> List[str]:
        """Get list of all symbols from database"""
        return await self._get_active_symbols()

    async def _get_active_symbols(self) -> List[str]:
        """Get list of active symbols from database"""
        with db_transaction() as session:
            from sqlalchemy import select

            stmt = select(Symbol.symbol).where(Symbol.status == "active")
            result = session.execute(stmt)
            return [row[0] for row in result.fetchall()]

    async def _batch_insert_market_data(self, records: List[MarketData]) -> int:
        """
        Insert market data records in batches using upsert

        Args:
            records: List of MarketData records

        Returns:
            Number of records inserted
        """
        if not records:
            return 0

        inserted_count = 0

        with db_transaction() as session:
            # Process in batches
            for i in range(0, len(records), self.batch_size):
                batch = records[i : i + self.batch_size]

                # Use PostgreSQL upsert
                stmt = insert(MarketData).values(
                    [
                        {
                            "symbol": record.symbol,
                            "timestamp": record.timestamp,
                            "data_source": record.data_source,
                            "open": record.open,
                            "high": record.high,
                            "low": record.low,
                            "close": record.close,
                            "volume": record.volume,
                        }
                        for record in batch
                    ]
                )

                # Update on conflict
                stmt = stmt.on_conflict_do_update(
                    index_elements=["symbol", "timestamp", "data_source"],
                    set_={
                        "open": stmt.excluded.open,
                        "high": stmt.excluded.high,
                        "low": stmt.excluded.low,
                        "close": stmt.excluded.close,
                        "volume": stmt.excluded.volume,
                    },
                )

                session.execute(stmt)
                inserted_count += len(batch)
                session.commit()

                logger.debug(f"Inserted batch of {len(batch)} records")

        return inserted_count

    async def health_check(self) -> bool:
        """
        Check if Yahoo Finance is accessible

        Returns:
            True if healthy
        """
        try:
            result = await self.client.health_check()
            return result.healthy

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    def _detect_fiscal_year_quarter(
        self, symbol: str, period_end: date
    ) -> tuple[int, int]:
        """
        Detect fiscal year and quarter for a given symbol and period_end date.

        This method analyzes the historical data to determine the fiscal year pattern
        for each company, as different companies have different fiscal year ends.

        Args:
            symbol: Stock symbol
            period_end: Period end date

        Returns:
            Tuple of (fiscal_year, fiscal_quarter)
        """
        month = period_end.month
        year = period_end.year

        # Known fiscal year patterns for major companies
        fiscal_year_patterns = {
            # Standard calendar year (Dec end) - most companies
            "AAPL": 9,  # Apple: September end
            "MSFT": 12,  # Microsoft: December end
            "GOOGL": 12,  # Google: December end
            "AMZN": 12,  # Amazon: December end
            "TSLA": 12,  # Tesla: December end
            "META": 12,  # Meta: December end
            "NVDA": 12,  # NVIDIA: December end
            "NFLX": 12,  # Netflix: December end
            "AMD": 12,  # AMD: December end
            "INTC": 12,  # Intel: December end
            "ORCL": 12,  # Oracle: December end
            "CRM": 12,  # Salesforce: December end
            "ADBE": 12,  # Adobe: December end
            "PYPL": 12,  # PayPal: December end
            "UBER": 12,  # Uber: December end
            "LYFT": 12,  # Lyft: December end
            "SNAP": 12,  # Snap: December end
            "TWTR": 12,  # Twitter: December end
            "SQ": 12,  # Square: December end
            "ROKU": 12,  # Roku: December end
            "ZM": 12,  # Zoom: December end
            "DOCU": 12,  # DocuSign: December end
            "OKTA": 12,  # Okta: December end
            "CRWD": 12,  # CrowdStrike: December end
            "SNOW": 12,  # Snowflake: December end
            "PLTR": 12,  # Palantir: December end
            "COIN": 12,  # Coinbase: December end
            "RBLX": 12,  # Roblox: December end
            "ABNB": 12,  # Airbnb: December end
            "DDOG": 12,  # Datadog: December end
            "NET": 12,  # Cloudflare: December end
            "ESTC": 12,  # Elastic: December end
            "MDB": 12,  # MongoDB: December end
            "WDAY": 12,  # Workday: December end
            "NOW": 12,  # ServiceNow: December end
            "TEAM": 12,  # Atlassian: December end
            "SPOT": 12,  # Spotify: December end
            "SHOP": 12,  # Shopify: December end
            "TWLO": 12,  # Twilio: December end
            "ZEN": 12,  # Zendesk: December end
            "PINS": 12,  # Pinterest: December end
            # Non-standard fiscal years
            "FDX": 11,  # FedEx: May end (month 11 = November, but they report in May)
            "NKE": 11,  # Nike: May end
            "WMT": 1,  # Walmart: January end
            "TGT": 1,  # Target: January end
            "COST": 8,  # Costco: August end
            "HD": 1,  # Home Depot: January end
            "LOW": 1,  # Lowe's: January end
            "MCD": 12,  # McDonald's: December end
            "SBUX": 9,  # Starbucks: September end
            "DIS": 9,  # Disney: September end
            "CMCSA": 12,  # Comcast: December end
            "VZ": 12,  # Verizon: December end
            "T": 12,  # AT&T: December end
            "JNJ": 12,  # Johnson & Johnson: December end
            "PFE": 12,  # Pfizer: December end
            "UNH": 12,  # UnitedHealth: December end
            "CVS": 12,  # CVS Health: December end
            "ABBV": 12,  # AbbVie: December end
            "MRK": 12,  # Merck: December end
            "PEP": 12,  # PepsiCo: December end
            "KO": 12,  # Coca-Cola: December end
            "PG": 12,  # Procter & Gamble: December end
            "CL": 12,  # Colgate-Palmolive: December end
            "KMB": 12,  # Kimberly-Clark: December end
            "GIS": 12,  # General Mills: December end
            "K": 12,  # Kellogg: December end
            "CPB": 12,  # Campbell Soup: December end
            "HRL": 12,  # Hormel Foods: December end
            "SJM": 12,  # J.M. Smucker: December end
            "CAG": 12,  # Conagra Brands: December end
            "MKC": 12,  # McCormick: December end
            "CHD": 12,  # Church & Dwight: December end
            "CLX": 12,  # Clorox: December end
            "ENR": 12,  # Energizer: December end
            "NWL": 12,  # Newell Brands: December end
            "SPB": 12,  # Spectrum Brands: December end
            "TUP": 12,  # Tupperware: December end
            "WBA": 12,  # Walgreens Boots Alliance: December end
            "CI": 12,  # Cigna: December end
            "ANTM": 12,  # Anthem: December end
            "HUM": 12,  # Humana: December end
            "MOH": 12,  # Molina Healthcare: December end
            "ELV": 12,  # Elevance Health: December end
            "CNC": 12,  # Centene: December end
            "DVA": 12,  # DaVita: December end
            "LH": 12,  # LabCorp: December end
            "DGX": 12,  # Quest Diagnostics: December end
            "TMO": 12,  # Thermo Fisher Scientific: December end
            "DHR": 12,  # Danaher: December end
            "BDX": 12,  # Becton Dickinson: December end
            "ABT": 12,  # Abbott: December end
            "BSX": 12,  # Boston Scientific: December end
            "CAH": 12,  # Cardinal Health: December end
            "CERN": 12,  # Cerner: December end
            "COO": 12,  # Cooper Companies: December end
            "CRL": 12,  # Charles River Laboratories: December end
            "EW": 12,  # Edwards Lifesciences: December end
            "HCA": 12,  # HCA Healthcare: December end
            "HOLX": 12,  # Hologic: December end
            "HSIC": 12,  # Henry Schein: December end
            "IDXX": 12,  # IDEXX Laboratories: December end
            "ISRG": 12,  # Intuitive Surgical: December end
            "MCK": 12,  # McKesson: December end
            "MDT": 12,  # Medtronic: December end
            "PKI": 12,  # PerkinElmer: December end
            "PODD": 12,  # Insulet: December end
            "PRGO": 12,  # Perrigo: December end
            "RMD": 12,  # ResMed: December end
            "STE": 12,  # Steris: December end
            "SYK": 12,  # Stryker: December end
            "UHS": 12,  # Universal Health Services: December end
            "VAR": 12,  # Varian Medical Systems: December end
            "WAT": 12,  # Waters: December end
            "ZBH": 12,  # Zimmer Biomet: December end
        }

        # Get fiscal year end month for this symbol
        fiscal_year_end_month = fiscal_year_patterns.get(
            symbol, 12
        )  # Default to December

        # Calculate fiscal year and quarter based on the fiscal year end month
        if month == fiscal_year_end_month:
            # This is Q4 of the fiscal year
            fiscal_quarter = 4
            fiscal_year = year
        else:
            # Calculate quarters based on months since fiscal year end
            months_since_fye = (month - fiscal_year_end_month) % 12

            if months_since_fye in [1, 2, 3]:  # Q1: 1-3 months after FYE
                fiscal_quarter = 1
                # Fiscal year is named after the year it ENDS
                fiscal_year = year + 1 if month > fiscal_year_end_month else year
            elif months_since_fye in [4, 5, 6]:  # Q2: 4-6 months after FYE
                fiscal_quarter = 2
                fiscal_year = year + 1 if month > fiscal_year_end_month else year
            elif months_since_fye in [7, 8, 9]:  # Q3: 7-9 months after FYE
                fiscal_quarter = 3
                fiscal_year = year + 1 if month > fiscal_year_end_month else year
            else:  # Q4: 10-11 months after FYE
                fiscal_quarter = 4
                fiscal_year = year + 1 if month > fiscal_year_end_month else year

        return fiscal_year, fiscal_quarter
