"""
Pytest configuration and fixtures for database testing
"""

from pathlib import Path

import pytest
from dotenv import load_dotenv
from sqlalchemy.orm import sessionmaker

# Load environment variables
load_dotenv()

# Add src to path
import sys  # noqa: E402

sys.path.append(str(Path(__file__).parent.parent / "src"))

from src.config.database import get_database_config  # noqa: E402


@pytest.fixture(scope="session")
def db_config():
    """Database configuration fixture"""
    return get_database_config()


@pytest.fixture(scope="session")
def trading_engine(db_config):
    """Trading database engine fixture"""
    return db_config.get_engine("trading")


@pytest.fixture(scope="session")
def prefect_engine(db_config):
    """Prefect database engine fixture"""
    return db_config.get_engine("prefect")


@pytest.fixture(scope="function")
def trading_session(trading_engine):
    """Trading database session fixture"""
    Session = sessionmaker(bind=trading_engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture(scope="function")
def prefect_session(prefect_engine):
    """Prefect database session fixture"""
    Session = sessionmaker(bind=prefect_engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture(scope="function")
def clean_trading_db(trading_engine):
    """Clean trading database for each test"""
    # This fixture can be used to clean up test data
    yield
    # Add cleanup logic here if needed


@pytest.fixture(scope="function")
def clean_prefect_db(prefect_engine):
    """Clean prefect database for each test"""
    # This fixture can be used to clean up test data
    yield
    # Add cleanup logic here if needed


@pytest.fixture(scope="function")
def setup_test_tables(trading_engine):
    """Setup required database tables for tests"""
    from sqlalchemy import text

    # Create the data_ingestion schema if it doesn't exist
    with trading_engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS data_ingestion"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS shared"))
        conn.commit()

    # Create the load_runs table
    create_load_runs_table = """
    CREATE TABLE IF NOT EXISTS data_ingestion.load_runs (
        id BIGSERIAL PRIMARY KEY,
        symbol VARCHAR(20) NOT NULL,
        data_source VARCHAR(20) NOT NULL,
        timespan VARCHAR(10) NOT NULL,
        multiplier INTEGER NOT NULL,
        last_run_date DATE NOT NULL,
        last_successful_date DATE NOT NULL,
        records_loaded INTEGER DEFAULT 0,
        status VARCHAR(20) DEFAULT 'success',
        error_message TEXT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

        CONSTRAINT unique_symbol_data_source_timespan UNIQUE (
            symbol, data_source, timespan, multiplier
        )
    );
    """

    # Create the market_data table
    create_market_data_table = """
    CREATE TABLE IF NOT EXISTS data_ingestion.market_data (
        id BIGSERIAL PRIMARY KEY,
        symbol VARCHAR(20) NOT NULL,
        timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
        data_source VARCHAR(20) NOT NULL DEFAULT 'yahoo',
        open DECIMAL(15,4),
        high DECIMAL(15,4),
        low DECIMAL(15,4),
        close DECIMAL(15,4),
        volume BIGINT,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        
        -- Constraints
        CONSTRAINT unique_symbol_timestamp_data_source UNIQUE (symbol, timestamp, data_source),
        CONSTRAINT positive_prices CHECK (open > 0 AND high > 0 AND low > 0 AND close > 0),
        CONSTRAINT valid_ohlc CHECK (high >= GREATEST(open, close) AND low <= LEAST(open, close))
    );
    """

    # Create the symbols table
    create_symbols_table = """
    CREATE TABLE IF NOT EXISTS data_ingestion.symbols (
        symbol VARCHAR(20) PRIMARY KEY,
        name VARCHAR(255),
        exchange VARCHAR(50),
        sector VARCHAR(100),
        industry VARCHAR(100),
        status VARCHAR(20) DEFAULT 'active',
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    """

    with trading_engine.connect() as conn:
        conn.execute(text(create_load_runs_table))
        conn.execute(text(create_market_data_table))
        conn.execute(text(create_symbols_table))
        conn.commit()

    yield

    # Cleanup - drop the tables after test
    with trading_engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS data_ingestion.load_runs CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS data_ingestion.market_data CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS data_ingestion.symbols CASCADE"))
        conn.commit()
