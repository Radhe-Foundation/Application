"""
Vernika - Session Fix Utility
Utility to fix session leaks in existing screens.

This module provides:
- Decorators to fix session leaks
- Common patterns for proper session management
- Migration guide for existing code
"""

from database.session_manager import get_session, get_db_session
import functools
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)


def with_db_session(func: Callable) -> Callable:
    """
    Decorator to automatically manage database session.

    Usage:
        @with_db_session
        def get_user(user_id):
            session = get_db_session()  # This session will be auto-closed
            return session.query(User).get(user_id)

    Note: This is a wrapper. For better performance, use:
        with get_session() as session:
            session.query(...)
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        session = get_db_session()
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            logger.error(f"Error in {func.__name__}: {e}")
            raise
        finally:
            session.close()

    return wrapper


def with_session_context(func: Callable) -> Callable:
    """
    Decorator that passes session as first argument.

    Usage:
        @with_session_context
        def get_user(session, user_id):
            return session.query(User).get(user_id)
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        with get_session() as session:
            return func(session, *args, **kwargs)

    return wrapper


class DatabaseMixin:
    """
    Mixin class to add database session management to any class.

    Usage:
        class MyScreen(DatabaseMixin, ft.Container):
            def load_data(self):
                with self.get_session() as session:
                    users = session.query(User).all()
    """

    _session = None

    def get_session(self):
        """Get a database session (context manager)"""
        return get_session()

    def get_db_session(self):
        """Get a database session (caller must close)"""
        return get_db_session()

    def with_session(self, operation: Callable, *args, **kwargs):
        """
        Execute operation with session.

        Usage:
            users = self.with_session(session.query, User)
        """
        with get_session() as session:
            return operation(session, *args, **kwargs)


# ==================== Common Fix Patterns ====================

# Pattern 1: Fix sessions that don't close
# BEFORE (LEAK):
#     def load_data(self):
#         db = get_db_session()
#         users = db.query(User).all()
#         # Missing: db.close()

# AFTER (FIXED):
#     def load_data(self):
#         with get_session() as session:
#             users = session.query(User).all()


# Pattern 2: Fix sessions in try-finally
# BEFORE (LEAK):
#     def load_data(self):
#         db = get_db_session()
#         try:
#             users = db.query(User).all()
#             return users
#         except:
#             return []
#         # Missing: finally: db.close()

# AFTER (FIXED):
#     def load_data(self):
#         with get_session() as session:
#             try:
#                 users = session.query(User).all()
#                 return users
#             except:
#                 return []


# Pattern 3: Fix multiple sessions in one function
# BEFORE (LEAK):
#     def process_data(self):
#         db1 = get_db_session()
#         db2 = get_db_session()
#         # ... operations ...
#         # Missing: db1.close(), db2.close()

# AFTER (FIXED):
#     def process_data(self):
#         with get_session() as session:
#             # Use single session for all operations


# Pattern 4: Fix callbacks and event handlers
# These often cause leaks because they're called asynchronously
#
# RECOMMENDATION: Use get_session() context manager in callbacks:
#     def on_button_click(self, e):
#         with get_session() as session:
#             # database operations
#             session.commit()


# ==================== Migration Helper ====================

def fix_screen_session_issues(screen_code: str) -> str:
    """
    Helper to fix common session issues in screen code.
    This is a simple find-replace based migration.

    Args:
        screen_code: The source code of the screen

    Returns:
        Fixed source code
    """

    # Fix 1: Add session close in methods that use get_db_session()
    fixes = [
        # Add import
        ("from database.connection import get_db_session",
         "from database.session_manager import get_session"),

        # Replace get_db_session() calls
        ("db = get_db_session()\n        try:",
         "with get_session() as session:\n            try:"),

        # Add session.close() patterns
        ("        except Exception as e:\n            print(f\"Error: {e}\")\n        finally:\n            session.close()",
         "        except Exception as e:\n            print(f\"Error: {e}\")"),

        # Fix db variable names to session
        ("db = get_db_session()",
         "with get_session() as session:"),

        ("db.close()",
         "# Session auto-closed by context manager"),

        ("db.commit()",
         "session.commit()"),

        ("db.query(",
         "session.query("),

        ("db.add(",
         "session.add("),

        ("db.delete(",
         "session.delete("),
    ]

    fixed_code = screen_code
    for old, new in fixes:
        fixed_code = fixed_code.replace(old, new)

    return fixed_code


# ==================== Database Health Check ====================

def check_session_leaks() -> dict:
    """
    Check for potential session leaks in the application.

    Returns:
        Dictionary with health check results
    """
    from database.session_manager import get_db_health

    health = get_db_health()

    results = {
        'connection_ok': health.get('connection_ok', False),
        'response_time_ms': health.get('response_time_ms', 0),
        'active_sessions': health.get('active_sessions', 0),
        'pool_status': health.get('pool_status', {}),
        'issues': []
    }

    # Check for potential issues
    if not results['connection_ok']:
        results['issues'].append("Database connection failed")

    if results['response_time_ms'] > 1000:
        results['issues'].append(
            f"Slow database response: {results['response_time_ms']}ms")

    pool = results['pool_status']
    if pool:
        checked_out = pool.get('checked_out', 0)
        size = pool.get('size', 10)
        if checked_out >= size:
            results['issues'].append(
                f"Connection pool exhausted: {checked_out}/{size}")

        if checked_out > size * 0.8:
            results['issues'].append(
                f"Connection pool near capacity: {checked_out}/{size}")

    if results['active_sessions'] > 50:
        results['issues'].append(
            f"Many unclosed sessions: {results['active_sessions']}")

    return results


def log_session_health():
    """Log current session health for debugging"""
    import json

    health = get_db_health()
    logger.info(f"Database Health: {json.dumps(health, indent=2)}")

    leaks = check_session_leaks()
    if leaks['issues']:
        for issue in leaks['issues']:
            logger.warning(f"Session Issue: {issue}")


# ==================== Recommended Session Patterns ====================

# Pattern 1: Simple query
def get_user_by_id(user_id: int):
    """Simple query - use context manager"""
    with get_session() as session:
        from database.models import User
        return session.query(User).get(user_id)


# Pattern 2: Query with filters
def search_users(search_term: str):
    """Query with filters"""
    with get_session() as session:
        from database.models import User
        term = f"%{search_term}%"
        return session.query(User).filter(
            (User.username.ilike(term)) |
            (User.email.ilike(term))
        ).all()


# Pattern 3: Create/Update/Delete
def create_user(username: str, email: str, password_hash: str, role_id: int):
    """Create a new user"""
    with get_session() as session:
        from database.models import User
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            role_id=role_id
        )
        session.add(user)
        session.commit()
        session.refresh(user)
        return user


def update_user(user_id: int, **kwargs):
    """Update a user"""
    with get_session() as session:
        from database.models import User
        user = session.query(User).get(user_id)
        if user:
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            session.commit()
            session.refresh(user)
        return user


def delete_user(user_id: int):
    """Delete a user"""
    with get_session() as session:
        from database.models import User
        user = session.query(User).get(user_id)
        if user:
            session.delete(user)
            session.commit()
            return True
        return False


# Pattern 4: Complex queries with relationships
def get_employee_with_details(employee_id: int):
    """Get employee with department and position"""
    from sqlalchemy.orm import joinedload
    from database.models import Employee

    with get_session() as session:
        return session.query(Employee).options(
            joinedload(Employee.department),
            joinedload(Employee.position)
        ).get(employee_id)


# Pattern 5: Transactions
def transfer_employee_to_department(employee_id: int, new_department_id: int):
    """Transfer employee with transaction"""
    with get_session() as session:
        from database.models import Employee
        from datetime import datetime

        try:
            # Start transaction
            employee = session.query(Employee).get(employee_id)
            if not employee:
                return False, "Employee not found"

            old_department = employee.department_id
            employee.department_id = new_department_id
            employee.updated_at = datetime.utcnow()

            # Commit transaction
            session.commit()
            return True, f"Transferred from {old_department} to {new_department_id}"

        except Exception as e:
            session.rollback()
            return False, str(e)


# Pattern 6: Bulk operations
def bulk_create_employees(employees_data: list):
    """Bulk create employees"""
    with get_session() as session:
        from database.models import Employee
        from datetime import datetime

        employees = []
        for data in employees_data:
            emp = Employee(
                employee_code=data['employee_code'],
                first_name=data['first_name'],
                last_name=data['last_name'],
                email=data.get('email'),
                department_id=data.get('department_id'),
                created_at=datetime.utcnow()
            )
            employees.append(emp)

        session.bulk_save_objects(employees)
        session.commit()
        return len(employees)
