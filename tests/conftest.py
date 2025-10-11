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
