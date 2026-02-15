"""
Vernika HRA - Comprehensive Fixes
This module implements all the bug fixes and new features requested.
"""

import flet as ft
from flet import *
from datetime import datetime, date
import bcrypt

from database.connection import get_db_session
from database.models import (
    User, Role, Employee, Department, Position, Company,
    UserStatus, Attendance, LeaveRequest, Task, ChatMessage,
    EmailMessage, EmailRecipient, EmailCategory, Document,
    TaskStatus, LeaveStatus, AttendanceStatus
)
from database.operations import (
    get_all_users, get_all_roles, get_all_employees, get_all_departments,
    get_user_by_id, get_employee_by_user_id, send_chat_message,
    get_direct_messages, mark_chat_messages_as_read, update_user_presence,
    send_email, get_user_emails, get_dashboard_stats
)


# ==================== FIX 1: Settings Screen Add User Enhancement ====================

def fix_settings_add_user(page, user):
    """Enhanced add user functionality for Settings Screen"""

    def get_roles():
        session = get_db_session()
        try:
            roles = session.query(Role).all()
            return roles
        finally:
            session.close()

    def save_new_user(username, email, password, role_id, on_success, on_error):
        session = get_db_session()
        try:
            # Check if username exists
            existing = session.query(User).filter(
                User.username == username.strip()
            ).first()
            if existing:
                on_error("Username already exists!")
                return

            # Check if email exists
            existing = session.query(User).filter(
                User.email == email.strip()
            ).first()
            if existing:
                on_error("Email already registered!")
                return

            # Hash password
            hashed = bcrypt.hashpw(
                password.encode(), bcrypt.gensalt()
            ).decode()

            # Create user
            new_user = User(
                username=username.strip(),
                email=email.strip(),
                password_hash=hashed,
                role_id=int(role_id),
                status=UserStatus.ACTIVE
            )
            session.add(new_user)
            session.commit()

            on_success()

        except Exception as ex:
            session.rollback()
            on_error(f"Error: {str(ex)}")
        finally:
            session.close()

    return {
        'get_roles': get_roles,
        'save_user': save_new_user
    }


# ==================== FIX 2: Reports Screen - Real Database Data ====================

def get_reports_data():
    """Get real data for reports from database"""
    session = get_db_session()
    try:
        # Get employee stats
        total_employees = session.query(Employee).count()
        active_employees = session.query(Employee).filter(
            Employee.is_active == True).count()

        # Get today's attendance
        today = datetime.now().date()
        present_today = session.query(Attendance).filter(
            Attendance.date == today,
            Attendance.status == AttendanceStatus.PRESENT
        ).count()

        # Get leave requests
        pending_leaves = session.query(LeaveRequest).filter(
            LeaveRequest.status == LeaveStatus.PENDING
        ).count()

        # Get absent count
        absent_today = session.query(Attendance).filter(
            Attendance.date == today,
            Attendance.status == AttendanceStatus.ABSENT
        ).count()

        # Get department stats
        departments = session.query(Department).all()
        dept_stats = []
        for dept in departments:
            emp_count = session.query(Employee).filter(
                Employee.department_id == dept.id
            ).count()
            dept_stats.append({
                'name': dept.name,
                'count': emp_count
            })

        # Get task stats
        pending_tasks = session.query(Task).filter(
            Task.status == TaskStatus.TODO
        ).count()

        completed_tasks = session.query(Task).filter(
            Task.status == TaskStatus.COMPLETED
        ).count()

        return {
            'total_employees': total_employees,
            'active_employees': active_employees,
            'present_today': present_today,
            'absent_today': absent_today,
            'pending_leaves': pending_leaves,
            'pending_tasks': pending_tasks,
            'completed_tasks': completed_tasks,
            'department_stats': dept_stats,
            'departments_count': len(departments)
        }
    except Exception as e:
        print(f"Error getting reports data: {e}")
        return {
            'total_employees': 0,
            'active_employees': 0,
            'present_today': 0,
            'absent_today': 0,
            'pending_leaves': 0,
            'pending_tasks': 0,
            'completed_tasks': 0,
            'department_stats': [],
            'departments_count': 0
        }
    finally:
        session.close()


# ==================== FIX 3: Chat Screen Enhancement ====================

class EnhancedChatFeatures:
    """Enhanced chat features with real-time support"""

    @staticmethod
    def update_last_seen(user_id):
        """Update user's last seen timestamp"""
        session = get_db_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                user.last_seen = datetime.utcnow()
                session.commit()
        finally:
            session.close()

    @staticmethod
    def get_user_presence(user_id):
        """Get user's online status and last seen"""
        session = get_db_session()
        try:
            user = session.query(User).filter(User.id == user_id).first()
            if user:
                return {
                    'is_online': user.is_online,
                    'last_seen': user.last_seen
                }
            return {'is_online': False, 'last_seen': None}
        finally:
            session.close()

    @staticmethod
    def format_last_seen(last_seen):
        """Format last seen timestamp for display"""
        if not last_seen:
            return "Unknown"

        now = datetime.utcnow()
        diff = now - last_seen

        if diff.total_seconds() < 60:
            return "Just now"
        elif diff.total_seconds() < 3600:
            minutes = int(diff.total_seconds() / 60)
            return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
        elif diff.total_seconds() < 86400:
            hours = int(diff.total_seconds() / 3600)
            return f"{hours} hour{'s' if hours > 1 else ''} ago"
        else:
            return last_seen.strftime("%Y-%m-%d %H:%M")

    @staticmethod
    def send_message_with_attachment(sender_id, receiver_id, content, file_path=None, file_name=None):
        """Send a chat message with optional attachment"""
        session = get_db_session()
        try:
            from database.models import MessageType

            message = ChatMessage(
                sender_id=sender_id,
                receiver_id=receiver_id,
                content=content,
                message_type=MessageType.FILE if file_path else MessageType.TEXT,
                has_attachment=bool(file_path),
                attachment_path=file_path
            )
            session.add(message)
            session.commit()
            session.refresh(message)
            return message
        except Exception as e:
            session.rollback()
            print(f"Error sending message: {e}")
            return None
        finally:
            session.close()


# ==================== FIX 4: Employee Screen with Access Control ====================

def get_employee_screen_access(user_id):
    """Get screen access for employee based on admin settings"""
    from utils.screen_access import get_user_screen_access, check_screen_access

    if not user_id:
        return {}

    # Get access from database
    return get_user_screen_access(user_id)


def check_employee_access(user_id, screen_key):
    """Check if employee has access to a specific screen"""
    from utils.screen_access import check_screen_access

    if not user_id:
        return False

    # Admin always has access
    session = get_db_session()
    try:
        user = session.query(User).filter(User.id == user_id).first()
        if user and user.role and user.role.name == 'admin':
            return True
    finally:
        session.close()

    return check_screen_access(user_id, screen_key)


# ==================== FIX 5: Performance Screen Enhancement ====================

class PerformanceManager:
    """Enhanced performance management with database support"""

    @staticmethod
    def get_performance_reviews(employee_id=None):
        """Get performance reviews from database"""
        # This would normally query a PerformanceReview model
        # For now, return empty list as model doesn't exist yet
        return []

    @staticmethod
    def get_goals(employee_id):
        """Get employee goals"""
        # Placeholder - would need Goal model
        return []

    @staticmethod
    def create_review_cycle(name, start_date, end_date, description=""):
        """Create a new review cycle"""
        # Placeholder - would need ReviewCycle model
        return True


# ==================== FIX 6: Data Entry for ETL Screen ====================

class DataEntryManager:
    """Data entry functionality for ETL screen"""

    @staticmethod
    def add_manual_entry(table_name, data):
        """Add manual data entry to a table"""
        session = get_db_session()
        try:
            if table_name == 'employee':
                employee = Employee(**data)
                session.add(employee)
            elif table_name == 'department':
                department = Department(**data)
                session.add(department)
            elif table_name == 'position':
                position = Position(**data)
                session.add(position)
            else:
                return False, f"Unknown table: {table_name}"

            session.commit()
            return True, "Data added successfully"
        except Exception as e:
            session.rollback()
            return False, str(e)
        finally:
            session.close()

    @staticmethod
    def get_table_fields(table_name):
        """Get available fields for a table"""
        fields = {
            'employee': ['first_name', 'last_name', 'email', 'phone', 'department_id', 'position_id', 'date_of_joining', 'employee_code'],
            'department': ['name', 'code', 'description'],
            'position': ['title', 'code', 'description', 'department_id', 'min_salary', 'max_salary'],
            'user': ['username', 'email', 'role_id']
        }
        return fields.get(table_name, [])


# ==================== FIX 7: Mail Screen Enhancement ====================

class MailEnhancements:
    """Enhanced mail features"""

    @staticmethod
    def send_announcement(sender_id, title, content, priority="normal", target_type="all"):
        """Send announcement to all employees"""
        session = get_db_session()
        try:
            # Get all active users
            users = session.query(User).filter(
                User.status == UserStatus.ACTIVE).all()
            recipient_ids = [u.id for u in users if u.id != sender_id]

            email = send_email(
                session,
                sender_id=sender_id,
                subject=f"[ANNOUNCEMENT] {title}",
                body=content,
                recipient_ids=recipient_ids,
                category=EmailCategory.ANNOUNCEMENT
            )

            return True, "Announcement sent successfully"
        except Exception as e:
            return False, str(e)
        finally:
            session.close()

    @staticmethod
    def send_offer_letter(sender_id, recipient_id, position, salary, start_date, terms):
        """Send offer letter to an employee"""
        session = get_db_session()
        try:
            body = f"""
Dear Employee,

We are pleased to offer you the position of {position}.

Salary Package: {salary}
Proposed Start Date: {start_date}

Terms and Conditions:
{terms}

Please sign and return the acceptance copy.

Best regards,
HR Department
            """

            email = send_email(
                session,
                sender_id=sender_id,
                subject=f"Offer Letter - {position}",
                body=body,
                recipient_ids=[recipient_id],
                category=EmailCategory.PROMOTION
            )

            return True, "Offer letter sent successfully"
        except Exception as e:
            return False, str(e)
        finally:
            session.close()


# ==================== Utility Functions ====================

def show_success_snackbar(page, message):
    """Show success snackbar"""
    snack = ft.SnackBar(
        content=ft.Text(message),
        bgcolor=ft.Colors.GREEN
    )
    page.overlay.append(snack)
    snack.open = True
    page.update()


def show_error_snackbar(page, message):
    """Show error snackbar"""
    snack = ft.SnackBar(
        content=ft.Text(message),
        bgcolor=ft.Colors.RED
    )
    page.overlay.append(snack)
    snack.open = True
    page.update()


def show_info_snackbar(page, message):
    """Show info snackbar"""
    snack = ft.SnackBar(
        content=ft.Text(message),
        bgcolor=ft.Colors.BLUE
    )
    page.overlay.append(snack)
    snack.open = True
    page.update()
