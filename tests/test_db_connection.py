import pytest

from database.connection import check_db_connection


def test_database_connection_is_healthy():
    """
    Basic health check for the configured database.

    This uses the same SQLAlchemy engine and DATABASE_URL that the
    application uses (SQLite for local dev, PostgreSQL for cloud).
    """
    assert check_db_connection() is True

