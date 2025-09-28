#!/usr/bin/env python3
"""
Database Connection Verification Script
Quick verification of database connections and basic functionality.
Use this for troubleshooting and quick checks.

For comprehensive testing, use: python scripts/run_tests.py unit
"""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add src to path for imports
sys.path.append(str(Path(__file__).parent.parent / "src"))

from sqlalchemy import text

from config.database import get_database_config, get_engine, get_prefect_engine


def test_trading_database():
    """Test connection to trading_system database"""
    print("Testing trading_system database connection...")

    try:
        engine = get_engine("trading")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            if row and row[0] == 1:
                print("trading_system database connection successful")
                return True
            else:
                print("trading_system database connection failed - unexpected result")
                return False
    except Exception as e:
        print(f"trading_system database connection failed: {e}")
        return False


def test_prefect_database():
    """Test connection to Prefect database"""
    print("Testing Prefect database connection...")

    try:
        engine = get_prefect_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            if row and row[0] == 1:
                print("Prefect database connection successful")
                return True
            else:
                print("Prefect database connection failed - unexpected result")
                return False
    except Exception as e:
        print(f"Prefect database connection failed: {e}")
        return False


def test_service_schemas():
    """Test service-specific schema access"""
    print("Testing service-specific schemas...")

    config = get_database_config()
    schemas = config.schemas

    for service, schema in schemas.items():
        try:
            engine = config.get_service_engine(service)
            with engine.connect() as conn:
                # Test if we can query the schema
                result = conn.execute(
                    text(
                        f"SELECT schema_name FROM information_schema.schemata WHERE schema_name = '{schema}'"
                    )
                )
                row = result.fetchone()
                if row:
                    print(f"Schema '{schema}' for service '{service}' is accessible")
                else:
                    print(f"Schema '{schema}' for service '{service}' not found")
                    return False
        except Exception as e:
            print(f"Error accessing schema '{schema}' for service '{service}': {e}")
            return False

    return True


def test_connection_pools():
    """Test connection pool configuration"""
    print("Testing connection pool configuration...")

    try:
        config = get_database_config()

        # Test trading database pool
        trading_engine = get_engine("trading")
        pool = trading_engine.pool
        print(
            f"Trading database pool: size={pool.size()}, checked_out={pool.checkedout()}"
        )

        # Test prefect database pool
        prefect_engine = get_prefect_engine()
        pool = prefect_engine.pool
        print(
            f"Prefect database pool: size={pool.size()}, checked_out={pool.checkedout()}"
        )

        return True
    except Exception as e:
        print(f"Connection pool test failed: {e}")
        return False


def main():
    """Main verification function"""
    print("Database Connection Verification")
    print("=" * 50)
    print("Quick verification of database connections and basic functionality.")
    print("For comprehensive testing, use: python scripts/run_tests.py unit")
    print("=" * 50)

    # Check if required environment variables are set
    required_vars = ["POSTGRES_HOST", "POSTGRES_USER", "POSTGRES_PASSWORD"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]

    if missing_vars:
        print(f"Missing required environment variables: {', '.join(missing_vars)}")
        print("Please set these variables in your .env file or environment")
        return False

    tests = [
        ("Trading Database", test_trading_database),
        ("Prefect Database", test_prefect_database),
        ("Service Schemas", test_service_schemas),
        ("Connection Pools", test_connection_pools),
    ]

    passed = 0
    total = len(tests)

    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        if test_func():
            passed += 1
        else:
            print(f"{test_name} test failed")

    print(f"\nVerification Results: {passed}/{total} checks passed")

    if passed == total:
        print("SUCCESS: All database connections verified!")
        print("Database is ready for use.")
        return True
    else:
        print("ERROR: Some database connections failed!")
        print("Please check your database configuration and try again.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
