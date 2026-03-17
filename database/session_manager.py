"""
RadheFoundation - Database Session Manager
Fixed version with proper session handling and connection pooling

This module provides centralized database session management with:
- Automatic session cleanup
- Connection health monitoring
- Query performance tracking
"""

from database.connection import Base
import logging
import threading
import time
from contextlib import contextmanager
from typing import Generator, Optional, Callable
from functools import wraps

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from sqlalchemy.ext.declarative import declarative_base

from config import (
    DATABASE_URL,
    DATABASE_TYPE,
    DB_POOL_SIZE,
    DB_MAX_OVERFLOW,
    DB_POOL_RECYCLE,
    DB_POOL_TIMEOUT,
    DB_ECHO,
    SECRET_KEY
)

logger = logging.getLogger(__name__)

# Import Base from connection module to ensure all models are registered
# Create the declarative base class for models (imported from connection)
# Base = declarative_base()  # Commented out - using Base from connection.py
# Base.__table_args__ = {'extend_existing': True}

# Global engine and session factory
_engine: Optional[Engine] = None
_session_factory: Optional[scoped_session] = None

# Session tracking for debugging
_active_sessions = []
_session_lock = threading.Lock()


def get_engine() -> Engine:
    """
    Get or create the database engine with optimized settings.
    Uses connection pooling for better performance with 200+ users.
    """
    global _engine

    if _engine is None:
        # Build connection arguments for PostgreSQL
        connect_args = {
            "connect_timeout": 10,
            "keepalives_idle": 30,
            "keepalives_interval": 5,
            "keepalives_count": 5,
            "application_name": "RadheFoundation_HRA",
            "options": "-c statement_timeout=30000"  # 30 second timeout
        }

        # Create engine with optimized connection pooling for 200+ users
        _engine = create_engine(
            DATABASE_URL,
            echo=DB_ECHO,
            pool_size=DB_POOL_SIZE,  # 20 connections
            max_overflow=DB_MAX_OVERFLOW,  # 40 overflow connections
            pool_recycle=DB_POOL_RECYCLE,
            pool_timeout=DB_POOL_TIMEOUT,
            pool_pre_ping=True,  # Health check before using connection
            poolclass=QueuePool,
            connect_args=connect_args
        )

        # Set up PostgreSQL-specific optimizations
        _setup_postgresql_optimizations(_engine)

        logger.info(
            f"Database engine created: {DATABASE_TYPE} (pool_size={DB_POOL_SIZE}, max_overflow={DB_MAX_OVERFLOW})")

    return _engine


def _setup_postgresql_optimizations(engine: Engine) -> None:
    """Set up PostgreSQL-specific optimizations for better performance."""

    @event.listens_for(engine, "connect")
    def set_pg_session_optimizations(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        # Set statement timeout (30 seconds)
        cursor.execute("SET statement_timeout = '30s'")
        # Set timezone to UTC
        cursor.execute("SET timezone = 'UTC'")
        cursor.close()


def _setup_sqlite_listeners(engine: Engine) -> None:
    """Set up SQLite-specific event listeners for foreign keys and WAL mode."""
    @event.listens_for(engine, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA cache_size=-64000")
        cursor.execute("PRAGMA temp_store=MEMORY")
        cursor.close()


def _setup_postgresql_listeners(engine: Engine) -> None:
    """Set up PostgreSQL-specific event listeners."""
    @event.listens_for(engine, "connect")
    def set_pg_session(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("SET statement_timeout = '30s'")
        cursor.close()


def get_session_factory() -> scoped_session:
    """
    Get or create the scoped session factory.
    Thread-safe session management.
    """
    global _session_factory

    if _session_factory is None:
        # Create thread-local session factory
        factory = sessionmaker(
            bind=get_engine(),
            autocommit=False,
            autoflush=False,
            expire_on_commit=False
        )
        _session_factory = scoped_session(factory)
        logger.info("Scoped session factory created")

    return _session_factory


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """
    Context manager for database session with automatic cleanup.
    This is the RECOMMENDED way to use database sessions.

    Usage:
        with get_session() as session:
            results = session.query(Model).all()
        # Session automatically closed and returned to pool

    Returns:
        SQLAlchemy Session instance
    """
    session = get_session_factory()()
    session_id = id(session)

    # Track active sessions for debugging
    with _session_lock:
        _active_sessions.append(session_id)

    logger.debug(
        f"Session {session_id} opened. Active: {len(_active_sessions)}")

    try:
        yield session
        session.commit()
        logger.debug(f"Session {session_id} committed successfully")
    except Exception as e:
        session.rollback()
        logger.error(f"Session {session_id} rolled back due to error: {e}")
        raise
    finally:
        session.close()
        with _session_lock:
            if session_id in _active_sessions:
                _active_sessions.remove(session_id)
        logger.debug(
            f"Session {session_id} closed. Active: {len(_active_sessions)}")


def get_db_session() -> Session:
    """
    Get a new database session (non-context manager).
    IMPORTANT: Caller MUST close this session when done!
    Prefer using get_session() context manager instead.

    Returns:
        SQLAlchemy Session instance
    """
    try:
        session = get_session_factory()()
        # Track session for debugging
        session_id = id(session)
        logger.debug(
            f"Session {session_id} created. Active: {len(_active_sessions)}")
        return session
    except Exception as e:
        logger.error(f"Failed to create database session: {e}")
        raise


@contextmanager
def session_scope() -> Generator[Session, None, None]:
    """
    Alternative name for get_session() for clarity.
    Use this for explicit transaction boundaries.
    """
    return get_session()


def with_session(func: Callable) -> Callable:
    """
    Decorator to automatically manage session for a function.

    Usage:
        @with_session
        def get_user(session, user_id):
            return session.query(User).get(user_id)

    Args:
        func: Function that takes session as first argument after self

    Returns:
        Wrapped function with automatic session management
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        with get_session() as session:
            # Insert session as first argument if not present
            if args and hasattr(args[0], '__class__'):
                # Method call - session goes after self
                new_args = (args[0], session) + args[1:]
            else:
                # Function call - session as first arg
                new_args = (session,) + args

            return func(*new_args, **kwargs)

    return wrapper


def init_db() -> None:
    """Initialize the database by creating all tables."""
    import database.models

    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created/verified")


def drop_db() -> None:
    """Drop all tables from the database."""
    Base.metadata.drop_all(bind=get_engine())
    logger.warning("All database tables dropped")


def close_db_connection() -> None:
    """Close the database connection and dispose of the engine."""
    global _engine, _session_factory

    if _session_factory is not None:
        _session_factory.remove()
        _session_factory = None
        logger.info("Session factory cleared")

    if _engine is not None:
        _engine.dispose()
        _engine = None
        logger.info("Database engine disposed")


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


def get_db_health() -> dict:
    """
    Get comprehensive database health information.

    Returns:
        Dictionary with health metrics
    """
    health = {
        "status": "unknown",
        "connection_ok": False,
        "pool_status": {},
        "active_sessions": 0,
        "response_time_ms": 0
    }

    try:
        engine = get_engine()

        # Check connection
        start = time.time()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        health["response_time_ms"] = int((time.time() - start) * 1000)
        health["connection_ok"] = True
        health["status"] = "healthy"

        # Get pool info
        pool = getattr(engine, 'pool', None)
        if pool:
            health["pool_status"] = {
                "size": getattr(pool, 'size', lambda: 0)(),
                "checked_in": getattr(pool, 'checkedin', lambda: 0)(),
                "checked_out": getattr(pool, 'checkedout', lambda: 0)(),
                "overflow": getattr(pool, 'overflow', lambda: 0)(),
            }

        # Track active sessions
        with _session_lock:
            health["active_sessions"] = len(_active_sessions)

    except Exception as e:
        health["status"] = "unhealthy"
        health["error"] = str(e)
        logger.error(f"Database health check failed: {e}")

    return health


def get_db_info() -> dict:
    """Get database information for debugging."""
    engine = get_engine()

    return {
        "url": str(engine.url),
        "dialect": engine.dialect.name,
        "pool_size": DB_POOL_SIZE,
        "max_overflow": DB_MAX_OVERFLOW,
    }


# Convenience functions for common operations

def query(*args, **kwargs):
    """
    Quick query function for simple database operations.
    Prefer using get_session() context manager for complex operations.

    Returns:
        Query object
    """
    with get_session() as session:
        return session.query(*args, **kwargs)


def execute(sql: str, params: dict = None):
    """
    Execute raw SQL with automatic session management.

    Args:
        sql: SQL statement
        params: Optional parameters

    Returns:
        Result proxy
    """
    with get_session() as session:
        if params:
            return session.execute(text(sql), params)
        return session.execute(text(sql))


def bulk_insert(model, data_list: list):
    """
    Bulk insert data efficiently.

    Args:
        model: SQLAlchemy model class
        data_list: List of dictionaries with model data
    """
    with get_session() as session:
        session.bulk_insert_mappings(model, data_list)
        session.commit()


def bulk_update(model, data_list: list, id_field: str = 'id'):
    """
    Bulk update data efficiently.

    Args:
        model: SQLAlchemy model class
        data_list: List of dictionaries with id and fields to update
        id_field: Name of the ID field
    """
    with get_session() as session:
        session.bulk_update_mappings(model, data_list)
        session.commit()
