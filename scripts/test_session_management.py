#!/usr/bin/env python3
"""
Test Session Management with Real Database
Verifies that the database base infrastructure works with PostgreSQL
"""

import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent))

from dotenv import load_dotenv
from sqlalchemy import BigInteger, Column, DateTime, Numeric, String, text
from sqlalchemy.exc import IntegrityError, OperationalError

# Load environment variables
load_dotenv()

from src.config.database import get_engine
from src.shared.database.base import Base, db_readonly_session, db_transaction
from src.shared.database.mixins import ReprMixin, SerializerMixin, TimestampMixin


# Create a simple test model
class TestMarketData(Base, TimestampMixin, SerializerMixin, ReprMixin):
    """Test model for market data"""

    __tablename__ = "test_market_data"
    __table_args__ = {"schema": "data_ingestion"}

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    symbol = Column(String(20), nullable=False)
    timestamp = Column(DateTime(timezone=True), nullable=False)
    close_price = Column(Numeric(15, 4), nullable=False)
    volume = Column(BigInteger)


def test_database_connection():
    """Test basic database connection"""
    print("=" * 60)
    print("TEST 1: Database Connection")
    print("=" * 60)

    try:
        engine = get_engine("trading")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            if row and row[0] == 1:
                print("[PASS] Database connection successful")
                return True
            else:
                print("[FAIL] Database connection failed - unexpected result")
                return False
    except Exception as e:
        print(f"[FAIL] Database connection failed: {e}")
        return False


def test_schema_access():
    """Test access to data_ingestion schema"""
    print("\n" + "=" * 60)
    print("TEST 2: Schema Access")
    print("=" * 60)

    try:
        engine = get_engine("trading")
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                SELECT schema_name 
                FROM information_schema.schemata 
                WHERE schema_name = 'data_ingestion'
            """
                )
            )
            row = result.fetchone()
            if row:
                print(f"[PASS] Schema 'data_ingestion' is accessible")
                return True
            else:
                print("[FAIL] Schema 'data_ingestion' not found")
                return False
    except Exception as e:
        print(f"[FAIL] Schema access failed: {e}")
        return False


def test_create_test_table():
    """Create test table"""
    print("\n" + "=" * 60)
    print("TEST 3: Create Test Table")
    print("=" * 60)

    try:
        engine = get_engine("trading")

        # Drop table if exists
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS data_ingestion.test_market_data"))
            conn.commit()

        # Create table using SQLAlchemy
        Base.metadata.create_all(engine, tables=[TestMarketData.__table__])

        # Verify table exists
        with engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'data_ingestion' 
                AND table_name = 'test_market_data'
            """
                )
            )
            row = result.fetchone()
            if row:
                print("[PASS] Test table created successfully")
                return True
            else:
                print("[FAIL] Test table not found after creation")
                return False
    except Exception as e:
        print(f"[FAIL] Table creation failed: {e}")
        return False


def test_transaction_insert():
    """Test insert using db_transaction"""
    print("\n" + "=" * 60)
    print("TEST 4: Transaction Insert")
    print("=" * 60)

    try:
        test_data = TestMarketData(
            symbol="AAPL",
            timestamp=datetime.now(timezone.utc),
            close_price=Decimal("150.25"),
            volume=1000000,
        )

        with db_transaction() as session:
            session.add(test_data)
            session.flush()  # Flush to get the ID
            # Extract data before session closes
            inserted_id = test_data.id
            symbol = test_data.symbol
            price = test_data.close_price
            volume = test_data.volume

        print(f"[PASS] Record inserted successfully with ID: {inserted_id}")
        print(f"   Symbol: {symbol}")
        print(f"   Price: ${price}")
        print(f"   Volume: {volume:,}")
        return True

    except Exception as e:
        print(f"[FAIL] Insert failed: {e}")
        return False


def test_readonly_query():
    """Test query using db_readonly_session"""
    print("\n" + "=" * 60)
    print("TEST 5: Read-Only Query")
    print("=" * 60)

    try:
        with db_readonly_session() as session:
            records = session.query(TestMarketData).all()

        print(f"[PASS] Query executed successfully")
        print(f"   Found {len(records)} record(s)")

        for record in records:
            print(f"   - {record.symbol} @ ${record.close_price} (ID: {record.id})")

        return True

    except Exception as e:
        print(f"[FAIL] Query failed: {e}")
        return False


def test_serialization():
    """Test model serialization"""
    print("\n" + "=" * 60)
    print("TEST 6: Model Serialization")
    print("=" * 60)

    try:
        with db_readonly_session() as session:
            record = session.query(TestMarketData).first()

        if record:
            # Test to_dict
            record_dict = record.to_dict()
            print(f"[PASS] Serialization to dict successful")
            print(f"   Keys: {list(record_dict.keys())}")
            print(f"   Symbol: {record_dict['symbol']}")
            print(f"   Price: {record_dict['close_price']}")

            # Test __repr__
            repr_str = repr(record)
            print(f"[PASS] __repr__ works: {repr_str}")

            return True
        else:
            print("[FAIL] No record found to serialize")
            return False

    except Exception as e:
        print(f"[FAIL] Serialization failed: {e}")
        return False


def test_transaction_update():
    """Test update using db_transaction"""
    print("\n" + "=" * 60)
    print("TEST 7: Transaction Update")
    print("=" * 60)

    try:
        # Update the first record
        with db_transaction() as session:
            record = session.query(TestMarketData).first()
            if record:
                old_price = record.close_price
                record.close_price = Decimal("151.50")
                new_price = record.close_price

        print(f"[PASS] Record updated successfully")
        print(f"   Old Price: ${old_price}")
        print(f"   New Price: ${new_price}")
        return True

    except Exception as e:
        print(f"[FAIL] Update failed: {e}")
        return False


def test_transaction_rollback():
    """Test transaction rollback on error"""
    print("\n" + "=" * 60)
    print("TEST 8: Transaction Rollback")
    print("=" * 60)

    try:
        # Count records before
        with db_readonly_session() as session:
            count_before = session.query(TestMarketData).count()

        # Attempt to insert with error
        try:
            with db_transaction() as session:
                test_data = TestMarketData(
                    symbol="GOOGL",
                    timestamp=datetime.now(timezone.utc),
                    close_price=Decimal("2800.00"),
                    volume=500000,
                )
                session.add(test_data)
                session.flush()

                # Simulate error
                raise ValueError("Simulated error to test rollback")
        except ValueError:
            pass  # Expected error

        # Count records after
        with db_readonly_session() as session:
            count_after = session.query(TestMarketData).count()

        if count_before == count_after:
            print(f"[PASS] Transaction rolled back successfully")
            print(f"   Records before: {count_before}")
            print(f"   Records after: {count_after}")
            return True
        else:
            print(f"[FAIL] Transaction not rolled back properly")
            print(f"   Records before: {count_before}")
            print(f"   Records after: {count_after}")
            return False

    except Exception as e:
        print(f"[FAIL] Rollback test failed: {e}")
        return False


def test_duplicate_constraint():
    """Test duplicate constraint handling"""
    print("\n" + "=" * 60)
    print("TEST 9: Duplicate Constraint Handling")
    print("=" * 60)

    try:
        # Get timestamp from existing record
        with db_readonly_session() as session:
            existing_record = session.query(TestMarketData).first()
            if not existing_record:
                print("[WARN]  No existing record to test duplicate constraint")
                return True

            test_timestamp = existing_record.timestamp
            test_symbol = existing_record.symbol

        # Try to insert duplicate (if you have unique constraint)
        try:
            with db_transaction() as session:
                duplicate_data = TestMarketData(
                    symbol=test_symbol,
                    timestamp=test_timestamp,
                    close_price=Decimal("999.99"),
                    volume=1,
                )
                session.add(duplicate_data)
        except IntegrityError as e:
            print(f"[PASS] Duplicate constraint caught correctly")
            print(f"   Error: {str(e)[:100]}...")
            return True

        print("[WARN]  No duplicate constraint violation (constraint may not exist)")
        return True

    except Exception as e:
        print(f"[FAIL] Duplicate constraint test failed: {e}")
        return False


def test_complex_query():
    """Test complex query with filtering and ordering"""
    print("\n" + "=" * 60)
    print("TEST 10: Complex Query")
    print("=" * 60)

    try:
        with db_readonly_session() as session:
            # Query with filtering and ordering
            records = (
                session.query(TestMarketData)
                .filter(TestMarketData.symbol == "AAPL")
                .order_by(TestMarketData.timestamp.desc())
                .limit(5)
                .all()
            )

        print(f"[PASS] Complex query executed successfully")
        print(f"   Found {len(records)} record(s)")

        for record in records:
            print(f"   - {record.symbol}: ${record.close_price} at {record.timestamp}")

        return True

    except Exception as e:
        print(f"[FAIL] Complex query failed: {e}")
        return False


def cleanup_test_table():
    """Clean up test table"""
    print("\n" + "=" * 60)
    print("CLEANUP: Removing Test Table")
    print("=" * 60)

    try:
        engine = get_engine("trading")
        with engine.connect() as conn:
            conn.execute(text("DROP TABLE IF EXISTS data_ingestion.test_market_data"))
            conn.commit()

        print("[PASS] Test table removed successfully")
        return True

    except Exception as e:
        print(f"[FAIL] Cleanup failed: {e}")
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("SESSION MANAGEMENT INTEGRATION TESTS")
    print("=" * 60)
    print()

    tests = [
        ("Database Connection", test_database_connection),
        ("Schema Access", test_schema_access),
        ("Create Test Table", test_create_test_table),
        ("Transaction Insert", test_transaction_insert),
        ("Read-Only Query", test_readonly_query),
        ("Model Serialization", test_serialization),
        ("Transaction Update", test_transaction_update),
        ("Transaction Rollback", test_transaction_rollback),
        ("Duplicate Constraint", test_duplicate_constraint),
        ("Complex Query", test_complex_query),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"\n[FAIL] Unexpected error in {test_name}: {e}")
            failed += 1

    # Cleanup
    cleanup_test_table()

    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    print(f"Total Tests: {len(tests)}")
    print(f"[PASS] Passed: {passed}")
    print(f"[FAIL] Failed: {failed}")
    print(f"Success Rate: {(passed/len(tests)*100):.1f}%")
    print("=" * 60)

    if failed == 0:
        print("\n[SUCCESS] All tests passed! Session management is working correctly.")
        return True
    else:
        print(f"\n[WARN]  {failed} test(s) failed. Please review the errors above.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
