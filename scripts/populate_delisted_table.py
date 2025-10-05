#!/usr/bin/env python3
"""
Populate delisted_symbols table from existing delisted symbols in symbols table

This script transfers delisted symbols from the main symbols table to the
dedicated delisted_symbols table for better historical tracking.
"""

import asyncio
import os
import sys
from datetime import date

# Add project root to path for imports
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.insert(0, project_root)

from loguru import logger

from src.services.data_ingestion.symbols import SymbolService
from src.shared.logging import setup_logging


async def populate_delisted_table():
    """Populate delisted_symbols table from existing delisted symbols"""
    symbol_service = SymbolService()

    logger.info("Starting delisted symbols table population...")

    # Get all delisted symbols from the main table
    from src.shared.database.base import db_transaction

    with db_transaction() as session:
        from sqlalchemy import select, text

        from src.shared.database.models.symbols import Symbol

        # Get delisted symbols
        stmt = select(Symbol).where(Symbol.status == "delisted")
        result = session.execute(stmt)
        delisted_symbols = result.scalars().all()

        logger.info(f"Found {len(delisted_symbols)} delisted symbols in main table")

        # Check existing delisted_symbols table
        existing_count = session.execute(
            text("SELECT COUNT(*) FROM data_ingestion.delisted_symbols")
        ).scalar()
        logger.info(f"Current delisted_symbols table has {existing_count} records")

        if existing_count > 0:
            logger.warning(
                "delisted_symbols table already has data. Skipping population."
            )
            return

        # Populate delisted_symbols table
        populated_count = 0
        for symbol_obj in delisted_symbols:
            symbol = symbol_obj.symbol

            # Check if already exists in delisted_symbols table
            existing = session.execute(
                text(
                    "SELECT COUNT(*) FROM data_ingestion.delisted_symbols WHERE symbol = :symbol"
                ),
                {"symbol": symbol},
            ).scalar()

            if existing == 0:
                # Insert into delisted_symbols table
                session.execute(
                    text(
                        """
                        INSERT INTO data_ingestion.delisted_symbols 
                        (symbol, delist_date, last_price, notes, created_at)
                        VALUES (:symbol, :delist_date, :last_price, :notes, :created_at)
                    """
                    ),
                    {
                        "symbol": symbol,
                        "delist_date": date.today(),
                        "last_price": None,
                        "notes": f"Migrated from symbols table on {date.today()}",
                        "created_at": symbol_obj.last_updated or symbol_obj.added_date,
                    },
                )
                populated_count += 1
                logger.info(f"Added {symbol} to delisted_symbols table")

        session.commit()
        logger.info(
            f"Successfully populated {populated_count} symbols into delisted_symbols table"
        )


async def main():
    """Main function"""
    setup_logging()

    try:
        await populate_delisted_table()
        logger.info("Delisted symbols table population completed successfully")
        return 0
    except Exception as e:
        logger.error(f"Failed to populate delisted symbols table: {e}")
        return 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
