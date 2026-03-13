"""
Vernika - Database Utility Module
Centralized database operations with proper session management.

This module provides:
- Easy-to-use database functions
- Automatic session cleanup
- Query result caching
- Common database operations
"""


from database.connection import Base
from database.session_manager import get_session, get_db_session
import logging
from typing import List, Optional, Any, Dict, Type, TypeVar
from datetime import datetime, date
from functools import wraps

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_, or_, text

logger = logging.getLogger(__name__)


T = TypeVar('T')


# ==================== Base Repository ====================

class BaseRepository:
    """
    Base repository class for CRUD operations.
    Provides common database operations with automatic session management.
    """

    model: Type = None  # Override in subclasses

    @classmethod
    def get_all(cls, limit: int = 100, offset: int = 0) -> List:
        """Get all records with pagination"""
        with get_session() as session:
            return session.query(cls.model).offset(offset).limit(limit).all()

    @classmethod
    def get_by_id(cls, id: int) -> Optional:
        """Get a record by ID"""
        with get_session() as session:
            return session.query(cls.model).get(id)

    @classmethod
    def get_by_ids(cls, ids: List[int]) -> List:
        """Get multiple records by IDs"""
        if not ids:
            return []
        with get_session() as session:
            return session.query(cls.model).filter(cls.model.id.in_(ids)).all()

    @classmethod
    def create(cls, **kwargs) -> Any:
        """Create a new record"""
        with get_session() as session:
            obj = cls.model(**kwargs)
            session.add(obj)
            session.commit()
            session.refresh(obj)
            return obj

    @classmethod
    def update(cls, id: int, **kwargs) -> Optional[Any]:
        """Update a record"""
        with get_session() as session:
            obj = session.query(cls.model).get(id)
            if obj:
                for key, value in kwargs.items():
                    if hasattr(obj, key):
                        setattr(obj, key, value)
                session.commit()
                session.refresh(obj)
            return obj

    @classmethod
    def delete(cls, id: int) -> bool:
        """Delete a record"""
        with get_session() as session:
            obj = session.query(cls.model).get(id)
            if obj:
                session.delete(obj)
                session.commit()
                return True
            return False

    @classmethod
    def count(cls) -> int:
        """Count all records"""
        with get_session() as session:
            return session.query(func.count(cls.model.id)).scalar()

    @classmethod
    def exists(cls, id: int) -> bool:
        """Check if record exists"""
        with get_session() as session:
            return session.query(cls.model).get(id) is not None

    @classmethod
    def filter(cls, *filters, limit: int = 100, offset: int = 0) -> List:
        """Filter records"""
        with get_session() as session:
            return session.query(cls.model).filter(*filters).offset(offset).limit(limit).all()

    @classmethod
    def first(cls, *filters) -> Optional:
        """Get first matching record"""
        with get_session() as session:
            return session.query(cls.model).filter(*filters).first()

    @classmethod
    def all_with_relationships(cls, *relationships) -> List:
        """Get all records with eager-loaded relationships"""
        with get_session() as session:
            query = session.query(cls.model)
            for rel in relationships:
                query = query.options(joinedload(rel))
            return query.all()


# ==================== User Repository ====================

class UserRepository(BaseRepository):
    """Repository for User operations"""
    from database.models import User
    model = User

    @classmethod
    def get_by_username(cls, username: str):
        """Get user by username"""
        with get_session() as session:
            return session.query(cls.model).filter(cls.model.username == username).first()

    @classmethod
    def get_by_email(cls, email: str):
        """Get user by email"""
        with get_session() as session:
            return session.query(cls.model).filter(cls.model.email == email).first()

    @classmethod
    def get_active_users(cls):
        """Get all active users"""
        from database.models import UserStatus
        with get_session() as session:
            return session.query(cls.model).filter(cls.model.status == UserStatus.ACTIVE).all()

    @classmethod
    def search(cls, search_term: str, limit: int = 20):
        """Search users by username or email"""
        with get_session() as session:
            term = f"%{search_term}%"
            return session.query(cls.model).filter(
                or_(
                    cls.model.username.ilike(term),
                    cls.model.email.ilike(term)
                )
            ).limit(limit).all()


# ==================== Employee Repository ====================

class EmployeeRepository(BaseRepository):
    """Repository for Employee operations"""
    from database.models import Employee
    model = Employee

    @classmethod
    def get_by_user_id(cls, user_id: int):
        """Get employee by user ID"""
        with get_session() as session:
            return session.query(cls.model).filter(cls.model.user_id == user_id).first()

    @classmethod
    def get_by_employee_code(cls, code: str):
        """Get employee by employee code"""
        with get_session() as session:
            return session.query(cls.model).filter(cls.model.employee_code == code).first()

    @classmethod
    def get_active_employees(cls):
        """Get all active employees"""
        with get_session() as session:
            return session.query(cls.model).filter(cls.model.is_active == True).all()

    @classmethod
    def get_by_department(cls, department_id: int):
        """Get employees by department"""
        with get_session() as session:
            return session.query(cls.model).filter(cls.model.department_id == department_id).all()

    @classmethod
    def search(cls, search_term: str, limit: int = 20):
        """Search employees by name or code"""
        with get_session() as session:
            term = f"%{search_term}%"
            return session.query(cls.model).filter(
                or_(
                    cls.model.first_name.ilike(term),
                    cls.model.last_name.ilike(term),
                    cls.model.employee_code.ilike(term),
                    cls.model.email.ilike(term)
                )
            ).limit(limit).all()

    @classmethod
    def get_with_relationships(cls, id: int):
        """Get employee with department and position"""
        with get_session() as session:
            return session.query(cls.model).options(
                joinedload(cls.model.department),
                joinedload(cls.model.position)
            ).filter(cls.model.id == id).first()

    @classmethod
    def get_all_with_relationships(cls, limit: int = 100, offset: int = 0):
        """Get all employees with relationships"""
        with get_session() as session:
            return session.query(cls.model).options(
                joinedload(cls.model.department),
                joinedload(cls.model.position)
            ).offset(offset).limit(limit).all()


# ==================== Department Repository ====================

class DepartmentRepository(BaseRepository):
    """Repository for Department operations"""
    from database.models import Department
    model = Department

    @classmethod
    def get_by_code(cls, code: str):
        """Get department by code"""
        with get_session() as session:
            return session.query(cls.model).filter(cls.model.code == code).first()

    @classmethod
    def get_active_departments(cls):
        """Get all active departments"""
        with get_session() as session:
            return session.query(cls.model).filter(cls.model.is_active == True).all()

    @classmethod
    def get_with_employee_count(cls):
        """Get departments with employee count"""
        from database.models import Employee
        with get_session() as session:
            return session.query(
                cls.model,
                func.count(Employee.id).label('employee_count')
            ).outerjoin(Employee).group_by(cls.model.id).all()


# ==================== Attendance Repository ====================

class AttendanceRepository(BaseRepository):
    """Repository for Attendance operations"""
    from database.models import Attendance
    model = Attendance

    @classmethod
    def get_by_employee_and_date(cls, employee_id: int, date: date):
        """Get attendance for employee on specific date"""
        with get_session() as session:
            return session.query(cls.model).filter(
                and_(
                    cls.model.employee_id == employee_id,
                    cls.model.date == date
                )
            ).first()

    @classmethod
    def get_employee_attendance(cls, employee_id: int, start_date: date = None, end_date: date = None):
        """Get attendance records for employee in date range"""
        with get_session() as session:
            query = session.query(cls.model).filter(
                cls.model.employee_id == employee_id)
            if start_date:
                query = query.filter(cls.model.date >= start_date)
            if end_date:
                query = query.filter(cls.model.date <= end_date)
            return query.order_by(cls.model.date.desc()).all()

    @classmethod
    def get_today_attendance(cls):
        """Get today's attendance records"""
        today = date.today()
        with get_session() as session:
            return session.query(cls.model).filter(cls.model.date == today).all()

    @classmethod
    def get_present_count_today(cls):
        """Get count of employees present today"""
        from database.models import AttendanceStatus
        today = date.today()
        with get_session() as session:
            return session.query(func.count(cls.model.id)).filter(
                and_(
                    cls.model.date == today,
                    cls.model.status == AttendanceStatus.PRESENT
                )
            ).scalar() or 0


# ==================== Leave Repository ====================

class LeaveRepository(BaseRepository):
    """Repository for LeaveRequest operations"""
    from database.models import LeaveRequest
    model = LeaveRequest

    @classmethod
    def get_pending_requests(cls):
        """Get all pending leave requests"""
        from database.models import LeaveStatus
        with get_session() as session:
            return session.query(cls.model).options(
                joinedload(cls.model.employee),
                joinedload(cls.model.leave_type)
            ).filter(cls.model.status == LeaveStatus.PENDING).all()

    @classmethod
    def get_employee_requests(cls, employee_id: int):
        """Get leave requests for an employee"""
        with get_session() as session:
            return session.query(cls.model).filter(
                cls.model.employee_id == employee_id
            ).order_by(cls.model.created_at.desc()).all()

    @classmethod
    def get_active_leaves(cls, check_date: date = None):
        """Get employees currently on leave"""
        from database.models import LeaveStatus
        if check_date is None:
            check_date = date.today()

        with get_session() as session:
            return session.query(cls.model).filter(
                and_(
                    cls.model.status == LeaveStatus.APPROVED,
                    cls.model.start_date <= check_date,
                    cls.model.end_date >= check_date
                )
            ).all()


# ==================== Task Repository ====================

class TaskRepository(BaseRepository):
    """Repository for Task operations"""
    from database.models import Task
    model = Task

    @classmethod
    def get_by_status(cls, status):
        """Get tasks by status"""
        with get_session() as session:
            return session.query(cls.model).filter(cls.model.status == status).all()

    @classmethod
    def get_assigned_tasks(cls, employee_id: int):
        """Get tasks assigned to an employee"""
        with get_session() as session:
            return session.query(cls.model).options(
                joinedload(cls.model.assigned_to)
            ).filter(cls.model.assigned_to_id == employee_id).all()

    @classmethod
    def get_pending_count(cls):
        """Get count of pending tasks"""
        from database.models import TaskStatus
        with get_session() as session:
            return session.query(func.count(cls.model.id)).filter(
                cls.model.status.in_([TaskStatus.TODO, TaskStatus.IN_PROGRESS])
            ).scalar() or 0


# ==================== CRM Repository ====================


# ==================== Dashboard Stats ====================


def get_dashboard_stats() -> Dict[str, Any]:
    """Get dashboard statistics - optimized single query version"""
    from database.models import (
        User, Employee, Department, Position, Attendance, LeaveRequest,
        Task, UserStatus, LeaveStatus, AttendanceStatus, TaskStatus
    )
    from datetime import date as date_type

    stats = {
        'total_users': 0,
        'active_users': 0,
        'total_employees': 0,
        'departments': 0,
        'positions': 0,
        'present_today': 0,
        'on_leave': 0,
        'pending_tasks': 0,
    }

    try:
        with get_session() as session:
            today = date_type.today()

            # Users - use string comparison for better performance
            stats['total_users'] = session.query(
                func.count(User.id)).scalar() or 0
            stats['active_users'] = session.query(func.count(User.id)).filter(
                User.status == 'active'
            ).scalar() or 0

            # Employees
            stats['total_employees'] = session.query(
                func.count(Employee.id)).scalar() or 0

            # Departments & Positions
            stats['departments'] = session.query(func.count(Department.id)).filter(
                Department.is_active == True
            ).scalar() or 0
            stats['positions'] = session.query(func.count(Position.id)).filter(
                Position.is_active == True
            ).scalar() or 0

            # Today's attendance - use string for status
            stats['present_today'] = session.query(func.count(Attendance.id)).filter(
                and_(
                    Attendance.date == today,
                    Attendance.status == 'present'
                )
            ).scalar() or 0

            # On leave today
            stats['on_leave'] = session.query(func.count(LeaveRequest.id)).filter(
                and_(
                    LeaveRequest.status == 'approved',
                    LeaveRequest.start_date <= today,
                    LeaveRequest.end_date >= today
                )
            ).scalar() or 0

            # Pending tasks - use string for status
            stats['pending_tasks'] = session.query(func.count(Task.id)).filter(
                Task.status.in_(['todo', 'in_progress'])
            ).scalar() or 0

    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")

    return stats


# ==================== Optimized Dashboard Stats V2 ====================

def get_dashboard_stats_v2() -> Dict[str, Any]:
    """Get dashboard statistics using PostgreSQL function - fastest method"""
    from sqlalchemy import text

    try:
        with get_session() as session:
            # Try to call the PostgreSQL function directly
            result = session.execute(
                text("SELECT * FROM get_dashboard_statistics()")).fetchone()
            if result:
                return {
                    'total_users': result[0] or 0,
                    'active_users': result[1] or 0,
                    'total_employees': result[2] or 0,
                    'departments': result[4] or 0,
                    'positions': result[5] or 0,
                    'present_today': result[6] or 0,
                    'on_leave': result[8] or 0,
                    'pending_tasks': result[10] or 0,
                    'in_progress_tasks': result[11] or 0,
                    'completed_tasks': result[12] or 0,
                }
    except Exception as e:
        logger.debug(f"PostgreSQL function not available, using fallback: {e}")

    # Fallback to the standard function
    return get_dashboard_stats()


# ==================== Fast Employee Loading ====================

def get_employees_for_screens(limit: int = 1000) -> List[Dict]:
    """
    Get employees with all related data for screen display.
    Optimized for fast loading in employee-related screens.
    """
    try:
        with get_session() as session:
            # Use raw SQL with JOINs for maximum performance
            result = session.execute(text("""
                SELECT 
                    e.id, e.employee_code, e.first_name, e.last_name, 
                    e.email, e.phone, e.is_active, e.department_id, e.position_id,
                    d.name as department_name, d.code as department_code,
                    p.title as position_title, p.code as position_code
                FROM employees e
                LEFT JOIN departments d ON e.department_id = d.id
                LEFT JOIN positions p ON e.position_id = p.id
                ORDER BY e.first_name, e.last_name
                LIMIT :limit
            """), {"limit": limit}).fetchall()

            return [dict(row._mapping) for row in result]
    except Exception as e:
        logger.error(f"Error getting employees for screens: {e}")
        return []


# ==================== Convenience Functions ====================

def execute_query(query_func, *args, **kwargs):
    """
    Execute a query function with proper session management.

    Usage:
        users = execute_query(session.query, User)
    """
    with get_session() as session:
        return query_func(session, *args, **kwargs)


def bulk_operation(items: List[Dict], model_class, mode: str = 'insert'):
    """
    Perform bulk insert or update.

    Args:
        items: List of dictionaries with model data
        model_class: SQLAlchemy model class
        mode: 'insert' or 'update'
    """
    with get_session() as session:
        if mode == 'insert':
            session.bulk_insert_mappings(model_class, items)
        elif mode == 'update':
            session.bulk_update_mappings(model_class, items)
        session.commit()
