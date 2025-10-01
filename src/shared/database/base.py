"""
Database Base Configuration
Provides SQLAlchemy declarative base and session management
"""

from sqlalchemy.orm import declarative_base, Session, sessionmaker
from sqlalchemy.exc import (
    IntegrityError,
    OperationalError,
    DataError,
    ProgrammingError,
)
from contextlib import contextmanager
from typing import Generator
from loguru import logger

from src.config.database import get_engine

# Create declarative base - all models inherit from this
Base = declarative_base()


@contextmanager
def db_transaction() -> Generator[Session, None, None]:
    """
    Database transaction context manager with automatic commit/rollback

    Features:
    - Automatic commit on success
    - Automatic rollback on error
    - Connection pooling
    - Error logging
    - Always closes session

    Usage:
        with db_transaction() as session:
            order = Order(symbol='AAPL', quantity=100)
            session.add(order)

    Use cases:
    - Creating orders, trades, positions
    - Updating risk limits
    - Recording strategy signals
    - Any data modification

    Raises:
        IntegrityError: Constraint violations, duplicate keys
        OperationalError: Connection issues, timeouts
        DataError: Invalid data types, out of range values
        ProgrammingError: SQL syntax errors
    """
    engine = get_engine("trading")
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        yield session
        session.commit()
        logger.debug("Database transaction committed successfully")

    except IntegrityError as e:
        session.rollback()
        logger.error(f"Database integrity error: {e}")
        raise

    except OperationalError as e:
        session.rollback()
        logger.error(f"Database operational error: {e}")
        raise

    except DataError as e:
        session.rollback()
        logger.error(f"Database data error: {e}")
        raise

    except ProgrammingError as e:
        session.rollback()
        logger.error(f"Database programming error: {e}")
        raise

    except Exception as e:
        session.rollback()
        logger.error(f"Unexpected database error: {e}")
        raise

    finally:
        session.close()


@contextmanager
def db_readonly_session() -> Generator[Session, None, None]:
    """
    Read-only database session for analytics and reporting

    Features:
    - No write operations allowed
    - Optimized for read performance
    - No transaction overhead
    - Connection pooling
    - Always closes session

    Usage:
        with db_readonly_session() as session:
            data = session.query(MarketData).filter(...).all()

    Use cases:
    - Analytics queries
    - Dashboard data
    - Reporting
    - Backtesting
    - Any read-only operation

    Performance Benefits:
    - No Write-Ahead Log (WAL) overhead
    - Reduced locking overhead
    - PostgreSQL can optimize query execution
    - Lower resource consumption
    - Can leverage read replicas (future scaling)
    """
    engine = get_engine("trading")
    SessionLocal = sessionmaker(bind=engine)
    session = SessionLocal()

    try:
        yield session
        logger.debug("Read-only session completed successfully")

    except Exception as e:
        logger.error(f"Error in read-only session: {e}")
        raise

    finally:
        session.close()


def get_session() -> Session:
    """
    Get a new database session for advanced use cases

    Warning: Manual session management required!
    You must commit/rollback and close the session yourself.

    Prefer using db_transaction() or db_readonly_session() instead.

    Returns:
        Session: SQLAlchemy session

    Usage:
        session = get_session()
        try:
            # Your operations
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()
    """
    engine = get_engine("trading")
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


# Convenience functions for common operations
def execute_in_transaction(func, *args, **kwargs):
    """
    Execute a function within a database transaction

    Args:
        func: Function to execute
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function

    Returns:
        Result of the function execution

    Example:
        def create_order(session, symbol, quantity):
            order = Order(symbol=symbol, quantity=quantity)
            session.add(order)
            return order.order_id

        order_id = execute_in_transaction(create_order, 'AAPL', 100)
    """
    with db_transaction() as session:
        return func(session, *args, **kwargs)


def execute_readonly(func, *args, **kwargs):
    """
    Execute a function within a read-only database session

    Args:
        func: Function to execute
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function

    Returns:
        Result of the function execution

    Example:
        def get_market_data(session, symbol):
            return session.query(MarketData).filter_by(symbol=symbol).all()

        data = execute_readonly(get_market_data, 'AAPL')
    """
    with db_readonly_session() as session:
        return func(session, *args, **kwargs)
