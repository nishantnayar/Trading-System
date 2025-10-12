"""
Yahoo Finance Data Loader

Loads market data and fundamentals from Yahoo Finance into the database.
"""

import asyncio
from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from loguru import logger
from sqlalchemy.dialects.postgresql import insert

from src.shared.database.base import db_transaction
from src.shared.database.models.company_info import CompanyInfo
from src.shared.database.models.market_data import MarketData
from src.shared.database.models.symbols import Symbol

from .client import YahooClient
from .exceptions import YahooAPIError, YahooDataError


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
    ) -> Dict[str, Any]:
        """
        Load market data for all active symbols

        Args:
            start_date: Start date for data
            end_date: End date for data
            interval: Data interval ('1h', '1d', etc.)
            max_symbols: Maximum number of symbols to process
            include_fundamentals: Load fundamentals data

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
                records_count = await self.load_market_data(
                    symbol=symbol,
                    start_date=start_date,
                    end_date=end_date,
                    interval=interval,
                )

                stats["successful"] += 1
                stats["total_records"] += records_count

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
