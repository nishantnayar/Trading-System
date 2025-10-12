"""
Yahoo Finance Data Loader

Loads market data and fundamentals from Yahoo Finance into the database.
"""

import asyncio
from datetime import date
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy.dialects.postgresql import insert

from src.shared.database.base import db_transaction
from src.shared.database.models.company_info import CompanyInfo
from src.shared.database.models.institutional_holders import InstitutionalHolder
from src.shared.database.models.key_statistics import KeyStatistics
from src.shared.database.models.market_data import MarketData
from src.shared.database.models.symbols import Symbol

from .client import YahooClient
from .exceptions import YahooAPIError


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

        except Exception as e:
            logger.error(f"Failed to load company info for {symbol}: {e}")
            return False

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
                    trailing_pe=(
                        float(stats_data.trailing_pe)
                        if stats_data.trailing_pe
                        else None
                    ),
                    forward_pe=(
                        float(stats_data.forward_pe) if stats_data.forward_pe else None
                    ),
                    peg_ratio=(
                        float(stats_data.peg_ratio) if stats_data.peg_ratio else None
                    ),
                    price_to_book=(
                        float(stats_data.price_to_book)
                        if stats_data.price_to_book
                        else None
                    ),
                    price_to_sales=(
                        float(stats_data.price_to_sales)
                        if stats_data.price_to_sales
                        else None
                    ),
                    enterprise_to_revenue=(
                        float(stats_data.enterprise_to_revenue)
                        if stats_data.enterprise_to_revenue
                        else None
                    ),
                    enterprise_to_ebitda=(
                        float(stats_data.enterprise_to_ebitda)
                        if stats_data.enterprise_to_ebitda
                        else None
                    ),
                    # Profitability metrics
                    profit_margin=(
                        float(stats_data.profit_margin)
                        if stats_data.profit_margin
                        else None
                    ),
                    operating_margin=(
                        float(stats_data.operating_margin)
                        if stats_data.operating_margin
                        else None
                    ),
                    return_on_assets=(
                        float(stats_data.return_on_assets)
                        if stats_data.return_on_assets
                        else None
                    ),
                    return_on_equity=(
                        float(stats_data.return_on_equity)
                        if stats_data.return_on_equity
                        else None
                    ),
                    gross_margin=(
                        float(stats_data.gross_margin)
                        if stats_data.gross_margin
                        else None
                    ),
                    ebitda_margin=(
                        float(stats_data.ebitda_margin)
                        if stats_data.ebitda_margin
                        else None
                    ),
                    # Financial health
                    revenue=stats_data.revenue,
                    revenue_per_share=(
                        float(stats_data.revenue_per_share)
                        if stats_data.revenue_per_share
                        else None
                    ),
                    earnings_per_share=(
                        float(stats_data.earnings_per_share)
                        if stats_data.earnings_per_share
                        else None
                    ),
                    total_cash=stats_data.total_cash,
                    total_debt=stats_data.total_debt,
                    debt_to_equity=(
                        float(stats_data.debt_to_equity)
                        if stats_data.debt_to_equity
                        else None
                    ),
                    current_ratio=(
                        float(stats_data.current_ratio)
                        if stats_data.current_ratio
                        else None
                    ),
                    quick_ratio=(
                        float(stats_data.quick_ratio)
                        if stats_data.quick_ratio
                        else None
                    ),
                    free_cash_flow=stats_data.free_cash_flow,
                    operating_cash_flow=stats_data.operating_cash_flow,
                    # Growth metrics
                    revenue_growth=(
                        float(stats_data.revenue_growth)
                        if stats_data.revenue_growth
                        else None
                    ),
                    earnings_growth=(
                        float(stats_data.earnings_growth)
                        if stats_data.earnings_growth
                        else None
                    ),
                    # Trading metrics
                    beta=float(stats_data.beta) if stats_data.beta else None,
                    fifty_two_week_high=(
                        float(stats_data.fifty_two_week_high)
                        if stats_data.fifty_two_week_high
                        else None
                    ),
                    fifty_two_week_low=(
                        float(stats_data.fifty_two_week_low)
                        if stats_data.fifty_two_week_low
                        else None
                    ),
                    fifty_day_average=(
                        float(stats_data.fifty_day_average)
                        if stats_data.fifty_day_average
                        else None
                    ),
                    two_hundred_day_average=(
                        float(stats_data.two_hundred_day_average)
                        if stats_data.two_hundred_day_average
                        else None
                    ),
                    average_volume=stats_data.average_volume,
                    # Dividend metrics
                    dividend_yield=(
                        float(stats_data.dividend_yield)
                        if stats_data.dividend_yield
                        else None
                    ),
                    dividend_rate=(
                        float(stats_data.dividend_rate)
                        if stats_data.dividend_rate
                        else None
                    ),
                    payout_ratio=(
                        float(stats_data.payout_ratio)
                        if stats_data.payout_ratio
                        else None
                    ),
                    # Share information
                    shares_outstanding=stats_data.shares_outstanding,
                    float_shares=stats_data.float_shares,
                    shares_short=stats_data.shares_short,
                    short_ratio=(
                        float(stats_data.short_ratio)
                        if stats_data.short_ratio
                        else None
                    ),
                    held_percent_insiders=(
                        float(stats_data.held_percent_insiders)
                        if stats_data.held_percent_insiders
                        else None
                    ),
                    held_percent_institutions=(
                        float(stats_data.held_percent_institutions)
                        if stats_data.held_percent_institutions
                        else None
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
                        "two_hundred_day_average": stmt.excluded.two_hundred_day_average,
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
                        "held_percent_institutions": stmt.excluded.held_percent_institutions,
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

    async def load_all_data(
        self,
        symbol: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
        include_fundamentals: bool = False,
        include_key_statistics: bool = False,
        include_institutional_holders: bool = False,
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

                stats["successful"] += 1

                # Add delay between requests
                if i < len(symbols):
                    await asyncio.sleep(self.delay_between_requests)

            except Exception as e:
                stats["failed"] += 1
                error_msg = f"Symbol {symbol}: {str(e)}"
                stats["errors"].append(error_msg)
                logger.error(error_msg)
                continue

        logger.info(f"Completed loading data. Stats: {stats}")
        return stats

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
