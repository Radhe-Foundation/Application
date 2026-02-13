"""
Vernika - Database Connection Module
Industry-Level Human Resource Management System

This module handles database connection management, session creation,
and engine configuration for SQLAlchemy.

Supports: SQLite, PostgreSQL (Supabase, self-hosted)
"""

import logging
from contextlib import contextmanager
from typing import Generator, Optional

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker, declarative_base

from config import (
    DATABASE_URL,
    DATABASE_TYPE,
    DB_POOL_SIZE,
    DB_MAX_OVERFLOW,
    DB_POOL_RECYCLE,
    DB_ECHO,
    SECRET_KEY
)

# Configure logging
logger = logging.getLogger(__name__)

# Create the declarative base class for models
Base = declarative_base()

# Global engine instance
_engine: Optional[Engine] = None
_session_factory: Optional[sessionmaker] = None


def get_engine() -> Engine:
    """
    Get or create the database engine.

    Returns:
        SQLAlchemy Engine instance
    """
    global _engine

    if _engine is None:
        # Build connection arguments
        connect_args = {}

        if "sqlite" in DATABASE_URL:
            # SQLite-specific settings
            connect_args = {"check_same_thread": False}
        elif "postgresql" in DATABASE_URL:
            # PostgreSQL-specific settings
            connect_args = {
                "connect_timeout": 10,
                "keepalives_idle": 30,
                "keepalives_interval": 5,
                "keepalives_count": 5,
            }

        _engine = create_engine(
            DATABASE_URL,
            echo=DB_ECHO,
            pool_size=DB_POOL_SIZE,
            max_overflow=DB_MAX_OVERFLOW,
            pool_recycle=DB_POOL_RECYCLE,
            pool_pre_ping=True,  # Enable connection health checks
            connect_args=connect_args
        )

        # Set up database-specific listeners
        if "sqlite" in DATABASE_URL:
            _setup_sqlite_listeners(_engine)
        elif "postgresql" in DATABASE_URL:
            _setup_postgresql_listeners(_engine)

        logger.info(
            f"Database engine created: {DATABASE_TYPE} ({DATABASE_URL[:50]}...)")

    return _engine


def _setup_sqlite_listeners(engine: Engine) -> None:
    """
    Set up SQLite-specific event listeners for foreign keys and WAL mode.

    Args:
        engine: SQLAlchemy Engine instance
    """
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        """
        Set SQLite pragmas on new connections.
        - Enable foreign key support
        - Set journal mode to WAL for better concurrency
        """
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=-64000")  # 64MB cache
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()


def _setup_postgresql_listeners(engine: Engine) -> None:
    """
    Set up PostgreSQL-specific event listeners.

    Args:
        engine: SQLAlchemy Engine instance
    """
    @event.listens_for(engine, "connect")
    def set_pg_session(dbapi_connection, connection_record):
        """
        Set PostgreSQL session settings for better performance.
        """
        cursor = dbapi_connection.cursor()
        # Enable extended query protocol for better performance
        cursor.execute("SET statement_timeout = '30s'")
        cursor.close()


def get_session_factory() -> sessionmaker:
    """
    Get or create the session factory.

    Returns:
        sessionmaker instance
    """
    global _session_factory

    if _session_factory is None:
        _session_factory = sessionmaker(
            bind=get_engine(),
            autocommit=False,
            autoflush=False,
            expire_on_commit=False
        )
        logger.info("Session factory created")

    return _session_factory


def get_db() -> Generator[Session, None, None]:
    """
    Get a database session as a generator.
    Designed for use with FastAPI dependency injection pattern.

    Yields:
        SQLAlchemy Session instance
    """
    session_factory = get_session_factory()
    session = session_factory()

    try:
        yield session
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Context manager for database session.
    Automatically handles commit/rollback and cleanup.

    Usage:
        with get_session() as session:
            session.query(User).all()

    Yields:
        SQLAlchemy Session instance
    """
    session_factory = get_session_factory()
    session = session_factory()

    try:
        yield session
        session.commit()
        logger.debug("Session committed successfully")
    except Exception as e:
        session.rollback()
        logger.error(f"Session rolled back due to error: {e}")
        raise
    finally:
        session.close()
        logger.debug("Session closed")


def get_db_session() -> Session:
    """
    Get a new database session (non-context manager).
    Caller is responsible for closing the session.

    Returns:
        SQLAlchemy Session instance
    """
    session_factory = get_session_factory()
    return session_factory()


def init_db() -> None:
    """
    Initialize the database by creating all tables.
    This function creates tables based on all imported models.
    """
    import database.models  # Import all models

    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")


def drop_db() -> None:
    """
    Drop all tables from the database.
    WARNING: This will delete all data!
    """
    Base.metadata.drop_all(bind=get_engine())
    logger.warning("All database tables dropped")


def close_db_connection() -> None:
    """
    Close the database connection and dispose of the engine.
    Call this when shutting down the application.
    """
    global _engine, _session_factory

    if _engine is not None:
        _engine.dispose()
        _engine = None
        logger.info("Database engine disposed")

    if _session_factory is not None:
        _session_factory = None
        logger.info("Session factory cleared")


def check_db_connection() -> bool:
    """
    Check if the database connection is healthy.

    Returns:
        True if connection is healthy, False otherwise
    """
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False


def get_db_info() -> dict:
    """
    Get database information for debugging.

    Returns:
        Dictionary with database info
    """
    engine = get_engine()
    pool_info = "N/A"
    checked_out = "N/A"
    try:
        pool = getattr(engine, 'pool', None)
        if pool is not None:
            pool_info = str(getattr(pool, 'size', lambda: "N/A")())
            checked_out = str(getattr(pool, 'checkedout', lambda: "N/A")())
    except Exception as e:
        logger.warning(f"Could not get pool info: {e}")

    return {
        "url": str(engine.url),
        "dialect": engine.dialect.name,
        "pool_size": pool_info,
        "pool_checked_out": checked_out
    }


class TransactionManager:
    """
    Context manager for handling database transactions.
    Provides more control over transaction behavior.
    """

    def __init__(self, session: Optional[Session] = None):
        """
        Initialize transaction manager.

        Args:
            session: Optional existing session to use
        """
        self._session: Optional[Session] = session
        self._owns_session = session is None

    def __enter__(self) -> Session:
        """
        Enter transaction context.

        Returns:
            SQLAlchemy Session instance
        """
        if self._session is None:
            self._session = get_db_session()

        return self._session

    def __exit__(self, exc_type, exc_val, exc_tb):
        """
        Exit transaction context, handling commits/rollbacks.
        """
        if self._session is None:
            return

        if exc_type is not None:
            # An exception occurred
            self._session.rollback()
            logger.error(f"Transaction rolled back due to: {exc_val}")
        else:
            # No exception
            try:
                self._session.commit()
                logger.debug("Transaction committed")
            except Exception as e:
                self._session.rollback()
                logger.error(f"Commit failed, rolled back: {e}")
                raise

        if self._owns_session:
            self._session.close()
            self._session = None


def begin_nested_session() -> Session:
    """
    Begin a nested session for savepoints.

    Returns:
        New nested session
    """
    session = get_db_session()
    session.begin_nested()
    return session


# Convenience function for quick queries
def query(*args, **kwargs):
    """
    Quick query function for simple database operations.

    Returns:
        Query object
    """
    with get_session() as session:
        return session.query(*args, **kwargs)
