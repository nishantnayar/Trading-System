"""
Test loading institutional holders
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from loguru import logger
from sqlalchemy import select

from src.services.yahoo.loader import YahooDataLoader
from src.shared.database.base import db_transaction
from src.shared.database.models.institutional_holders import InstitutionalHolder
from src.shared.logging import setup_logging


async def test_load_institutional_holders():
    """Test loading institutional holders for AAPL"""
    setup_logging()

    logger.info("=" * 80)
    logger.info("Testing Institutional Holders Loader")
    logger.info("=" * 80)

    symbol = "AAPL"

    # Step 1: Check if table exists
    logger.info("\nStep 1: Checking if institutional_holders table exists...")
    try:
        with db_transaction() as session:
            result = session.execute(select(InstitutionalHolder).limit(1))
            logger.info("✓ Table exists and is accessible")
    except Exception as e:
        logger.error(f"✗ Table check failed: {e}")
        logger.error("Please run the migration first:")
        logger.error(
            "  psql -U username -d trading_system -f scripts/10_create_institutional_holders_table.sql"
        )
        return False

    # Step 2: Load institutional holders
    logger.info(f"\nStep 2: Loading institutional holders for {symbol}...")
    loader = YahooDataLoader()

    try:
        count = await loader.load_institutional_holders(symbol)

        if count > 0:
            logger.info(
                f"✓ Successfully loaded {count} institutional holders for {symbol}"
            )
        else:
            logger.warning(f"⚠ No institutional holders found for {symbol}")
            return False

    except Exception as e:
        logger.error(f"✗ Error loading institutional holders: {e}")
        import traceback

        traceback.print_exc()
        return False

    # Step 3: Verify data was saved
    logger.info(f"\nStep 3: Verifying data was saved to database...")
    try:
        with db_transaction() as session:
            holders = (
                session.query(InstitutionalHolder)
                .filter_by(symbol=symbol)
                .order_by(InstitutionalHolder.shares.desc())
                .limit(10)
                .all()
            )

            if holders:
                logger.info(f"✓ Found {len(holders)} institutional holders in database")
                logger.info(f"\nTop 10 Institutional Holders for {symbol}:")
                logger.info("-" * 80)

                for i, holder in enumerate(holders, 1):
                    logger.info(
                        f"{i:2d}. {holder.holder_name[:45]:45s} | "
                        f"Shares: {holder.shares_display:>12s} | "
                        f"Value: {holder.value_display:>12s} | "
                        f"% Held: {holder.percent_held_display:>8s}"
                    )

                logger.info(f"\nTotal holders loaded: {count}")
            else:
                logger.error(f"✗ No data found in database for {symbol}")
                return False

    except Exception as e:
        logger.error(f"✗ Error querying database: {e}")
        import traceback

        traceback.print_exc()
        return False

    logger.info("\n" + "=" * 80)
    logger.info("✓ All tests passed!")
    logger.info("=" * 80)

    return True


if __name__ == "__main__":
    result = asyncio.run(test_load_institutional_holders())
    sys.exit(0 if result else 1)
