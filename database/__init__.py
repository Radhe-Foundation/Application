"""Database module for Vernika HRA"""
from database.connection import get_engine, Base, init_db

# Import models with error handling to prevent duplicate table definition errors
try:
    from database.models import *
    from database.operations import *
except Exception as e:
    # Handle case where tables are already defined
    import logging
    logging.getLogger(__name__).warning(
        f"Database import issue (may be expected): {e}")

# Import new session management
from database.session_manager import (
    get_session,
    get_db_session,
    get_db_health,
    check_db_connection,
    with_session,
    query,
    execute,
    close_db_connection
)

# Import repositories
from database.repositories import (
    BaseRepository,
    UserRepository,
    EmployeeRepository,
    DepartmentRepository,
    AttendanceRepository,
    LeaveRepository,
    TaskRepository,
    get_dashboard_stats
)
