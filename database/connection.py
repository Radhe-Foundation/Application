"""
Vernika - Database Connection Module
Industry-Level Human Resource Management System

This module handles database connection management, session creation,
and engine configuration for SQLAlchemy.

Supports: SQLite, PostgreSQL (Supabase, self-hosted)
"""

from config import (
    DATABASE_URL,
    DATABASE_TYPE,
    DB_POOL_SIZE,
    DB_MAX_OVERFLOW,
    DB_POOL_RECYCLE,
    DB_POOL_TIMEOUT,
    DB_ECHO,
)
import logging
from contextlib import contextmanager
from typing import Optional, Generator

from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base


# Configure logging
logger = logging.getLogger(__name__)

# Create the declarative base class for models
Base = declarative_base()
Base.__table_args__ = {'extend_existing': True}

# Global engine instance
_engine: Optional[Engine] = None
_session_factory = None


def get_engine() -> Engine:
    """Get or create the database engine."""
    global _engine

    if _engine is None:
        connect_args = {}

        if "sqlite" in DATABASE_URL:
            connect_args = {"check_same_thread": False}
        elif "postgresql" in DATABASE_URL:
            connect_args = {
                "connect_timeout": 10,
                "keepalives_idle": 30,
                "keepalives_interval": 5,
                "keepalives_count": 5,
                "application_name": "Vernika_HRA"
            }

        _engine = create_engine(
            DATABASE_URL,
            echo=DB_ECHO,
            pool_size=20,
            max_overflow=30,
            pool_recycle=DB_POOL_RECYCLE,
            pool_timeout=DB_POOL_TIMEOUT,
            pool_pre_ping=True,
            connect_args=connect_args
        )

        if "sqlite" in DATABASE_URL:
            _setup_sqlite_listeners(_engine)
        elif "postgresql" in DATABASE_URL:
            _setup_postgresql_listeners(_engine)

        logger.info(f"Database engine created: {DATABASE_TYPE}")

    return _engine


def _setup_sqlite_listeners(engine: Engine) -> None:
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
    @event.listens_for(engine, "connect")
    def set_pg_session(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("SET statement_timeout = '30s'")
        cursor.close()


def get_session_factory():
    """Get or create the session factory."""
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


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Context manager for database session with automatic cleanup."""
    session = get_session_factory()()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def get_db_session() -> Session:
    """Get a new database session. Caller must close it."""
    return get_session_factory()()


def init_db() -> None:
    """Initialize the database by creating all tables."""
    import database.models
    engine = get_engine()
    Base.metadata.create_all(bind=engine, extend_existing=True)
    logger.info("Database tables created/verified")


def drop_db() -> None:
    """Drop all tables from the database."""
    Base.metadata.drop_all(bind=get_engine())
    logger.warning("All database tables dropped")


def close_db_connection() -> None:
    """Close the database connection and dispose of the engine."""
    global _engine, _session_factory

    if _engine is not None:
        _engine.dispose()
        _engine = None

    _session_factory = None
    logger.info("Database engine disposed")


def check_db_connection() -> bool:
    """Check if the database connection is healthy."""
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False


def get_db_info() -> dict:
    """Get database information for debugging."""
    engine = get_engine()
    return {
        "url": str(engine.url),
        "dialect": engine.dialect.name,
    }


class TransactionManager:
    """Context manager for handling database transactions."""

    def __init__(self, session: Session = None):
        self._session = session
        self._owns_session = session is None

    def __enter__(self) -> Session:
        if self._session is None:
            self._session = get_db_session()
        return self._session

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._session is None:
            return

        if exc_type is not None:
            self._session.rollback()
        else:
            try:
                self._session.commit()
            except Exception:
                self._session.rollback()
                raise

        if self._owns_session:
            self._session.close()
            self._session = None


def query(*args, **kwargs):
    """Quick query function for simple database operations."""
    with get_session() as session:
        return session.query(*args, **kwargs)
