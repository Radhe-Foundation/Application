"""
Vernika HRA - Database Models
Industry-Level Human Resource Management System
"""

import enum
from datetime import datetime, date
from typing import Optional, List
import flet as ft
from sqlalchemy import (
    Column, Integer, String, Boolean, DateTime, Date, Text,
    ForeignKey, Float, Enum, JSON, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship, Mapped, mapped_column
from sqlalchemy.sql import func
from database.connection import Base


# ==================== ENUMS ====================

class UserStatus(str, enum.Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    LOCKED = "locked"
    PENDING = "pending"


class LeaveStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class LeaveType(str, enum.Enum):
    ANNUAL = "annual"
    SICK = "sick"
    PERSONAL = "personal"
    MATERNITY = "maternity"
    PATERNITY = "paternity"
    BEREAVEMENT = "bereavement"
    UNPAID = "unpaid"


class AttendanceStatus(str, enum.Enum):
    PRESENT = "present"
    ABSENT = "absent"
    LATE = "late"
    HALF_DAY = "half_day"
    ON_LEAVE = "on_leave"


class TaskPriority(str, enum.Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class TaskStatus(str, enum.Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class Gender(str, enum.Enum):
    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class EmailCategory(str, enum.Enum):
    GENERAL = "general"
    ANNOUNCEMENT = "announcement"
    RESIGNATION = "resignation"
    PROMOTION = "promotion"
    MEETING_REQUEST = "meeting_request"
    HR_COMMUNICATION = "hr_communication"


class MeetingStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MessageType(str, enum.Enum):
    TEXT = "text"
    FILE = "file"
    IMAGE = "image"
    CALL_INVITATION = "call_invitation"


# ==================== MODELS ====================

class Company(Base):
    __tablename__ = "companies"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    email = Column(String(100))
    phone = Column(String(20))
    address = Column(Text)


class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    level = Column(Integer, default=1)
    permissions = Column(JSON, default=dict)

    users = relationship("User", back_populates="role")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role_id = Column(Integer, ForeignKey("roles.id"), nullable=False)
    status = Column(Enum(UserStatus), default=UserStatus.ACTIVE)
    created_at = Column(DateTime, default=datetime.utcnow)

    # User presence tracking for multi-user support
    last_seen = Column(DateTime, nullable=True)
    is_online = Column(Boolean, default=False)

    # Session token for concurrent login handling
    session_token = Column(String(255), nullable=True)
    last_login = Column(DateTime, nullable=True)
    last_ip = Column(String(50), nullable=True)

    role = relationship("Role", back_populates="users")

    def check_password(self, password: str) -> bool:
        """
        Check if the provided password matches the stored hash.

        Args:
            password: Plain text password to check

        Returns:
            bool: True if password matches
        """
        import bcrypt
        try:
            # Ensure password is bytes
            password_bytes = password.encode(
                'utf-8') if isinstance(password, str) else password

            # Get stored hash from database (handles both Column and string types)
            stored_hash = self.password_hash
            if hasattr(stored_hash, 'first'):
                # It's a Column, get the actual value
                stored_hash = stored_hash.first(
                )[0] if stored_hash.first() else None

            if not stored_hash:
                return False

            # Ensure stored hash is bytes
            hash_bytes = stored_hash.encode(
                'utf-8') if isinstance(stored_hash, str) else stored_hash

            return bcrypt.checkpw(password_bytes, hash_bytes)
        except Exception as e:
            print(f"Password check error: {e}")
            return False

    def is_active_user(self) -> bool:
        """Check if user is active"""
        return self.status == UserStatus.ACTIVE

    def get_employee(self):
        """Get associated employee profile"""
        from database.operations import get_employee_by_user_id
        from database.connection import get_db_session
        session = get_db_session()
        try:
            return get_employee_by_user_id(session, self.id)
        finally:
            session.close()


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    code = Column(String(20), unique=True, nullable=False)
    description = Column(Text)
    head_id = Column(Integer)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Position(Base):
    __tablename__ = "positions"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    code = Column(String(20), unique=True, nullable=False)
    description = Column(Text)
    department_id = Column(Integer, ForeignKey("departments.id"))
    is_active = Column(Boolean, default=True)
    min_salary = Column(Float)
    max_salary = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    department = relationship("Department", backref="positions")


class Employee(Base):
    __tablename__ = "employees"

    id = Column(Integer, primary_key=True, index=True)
    employee_code = Column(String(20), unique=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    company_id = Column(Integer, ForeignKey("companies.id"))

    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    date_of_birth = Column(Date)
    gender = Column(Enum(Gender))

    email = Column(String(100))
    phone = Column(String(20))
    department_id = Column(Integer, ForeignKey("departments.id"))
    position_id = Column(Integer, ForeignKey("positions.id"))
    date_of_joining = Column(Date)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Additional fields used in employees_screen.py
    employment_type = Column(String(50), default="full_time")
    employment_status = Column(String(50), default="active")

    # Address fields
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(100))
    pincode = Column(String(20))

    # Emergency contact
    emergency_contact_name = Column(String(200))
    emergency_phone = Column(String(20))
    emergency_relation = Column(String(50))

    # Bank details
    bank_name = Column(String(200))
    account_number = Column(String(50))
    ifsc_code = Column(String(50))
    branch_name = Column(String(200))

    # Salary information
    basic_salary = Column(Float, default=0)
    allowance = Column(Float, default=0)
    deduction = Column(Float, default=0)

    user = relationship("User", backref="employee")
    department = relationship("Department", backref="employees")
    position = relationship("Position", backref="employees")


class Attendance(Base):
    __tablename__ = "attendances"
    __table_args__ = (UniqueConstraint(
        'employee_id', 'date', name='uq_employee_date'),)

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    date = Column(Date, nullable=False)
    check_in = Column(DateTime)
    check_out = Column(DateTime)
    status = Column(Enum(AttendanceStatus), nullable=False)
    working_hours = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)

    employee = relationship("Employee", backref="attendances")


class LeaveTypeConfig(Base):
    __tablename__ = "leave_type_configs"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    display_name = Column(String(50), nullable=False)
    max_days_per_year = Column(Integer, default=0)
    is_paid = Column(Boolean, default=True)
    color = Column(String(20), default="#2E86AB")


class LeaveBalance(Base):
    __tablename__ = "leave_balances"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    leave_type_id = Column(Integer, ForeignKey(
        "leave_type_configs.id"), nullable=False)
    year = Column(Integer, nullable=False)
    total_days = Column(Float, default=0)
    used_days = Column(Float, default=0)


class LeaveRequest(Base):
    __tablename__ = "leave_requests"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    leave_type_id = Column(Integer, ForeignKey(
        "leave_type_configs.id"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    days_requested = Column(Float, nullable=False)
    reason = Column(Text, nullable=False)
    status = Column(Enum(LeaveStatus), default=LeaveStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    assigned_to_id = Column(Integer, ForeignKey(
        "employees.id"), nullable=False)
    created_by_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    status = Column(Enum(TaskStatus), default=TaskStatus.TODO)
    priority = Column(Enum(TaskPriority), default=TaskPriority.MEDIUM)
    due_date = Column(Date)
    created_at = Column(DateTime, default=datetime.utcnow)

    assigned_to = relationship("Employee", foreign_keys=[
                               assigned_to_id], backref="tasks_assigned")
    created_by = relationship("Employee", foreign_keys=[
                              created_by_id], backref="tasks_created")


class TaskComment(Base):
    __tablename__ = "task_comments"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("Task", backref="comments")
    employee = relationship("Employee")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(100), nullable=False)
    details = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", backref="audit_logs")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    content = Column(Text, nullable=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    sender = relationship("Employee", foreign_keys=[
                          sender_id], backref="sent_messages")
    receiver = relationship("Employee", foreign_keys=[
                            receiver_id], backref="received_messages")


class TimeOff(Base):
    __tablename__ = "time_off_requests"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    leave_type = Column(String(50), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    reason = Column(Text)
    status = Column(Enum(LeaveStatus), default=LeaveStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    approved_by = Column(Integer, ForeignKey("employees.id"))

    user = relationship("Employee", foreign_keys=[
                        user_id], backref="time_off_requests")
    approver = relationship("Employee", foreign_keys=[
                            approved_by], backref="approved_time_offs")


# ==================== COMMUNICATION MODELS ====================

class ChatGroup(Base):
    """Chat groups for team communication"""
    __tablename__ = "chat_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    members = relationship("ChatGroupMember", back_populates="group")


class ChatGroupMember(Base):
    """Membership in chat groups"""
    __tablename__ = "chat_group_members"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("chat_groups.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(20), default="member")  # admin, member
    joined_at = Column(DateTime, default=datetime.utcnow)

    group = relationship("ChatGroup", back_populates="members")
    user = relationship("User")


class ChatMessage(Base):
    """Messages for both direct and group chat"""
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("chat_groups.id"),
                      nullable=True)  # NULL for direct messages
    receiver_id = Column(Integer, ForeignKey("users.id"),
                         nullable=True)  # NULL for group messages
    content = Column(Text, nullable=False)
    message_type = Column(Enum(MessageType), default=MessageType.TEXT)
    is_read = Column(Boolean, default=False)
    has_attachment = Column(Boolean, default=False)
    attachment_path = Column(String(500))
    created_at = Column(DateTime, default=datetime.utcnow)

    sender = relationship("User", foreign_keys=[
                          sender_id], backref="sent_chat_messages")
    receiver = relationship("User", foreign_keys=[
                            receiver_id], backref="received_chat_messages")
    group = relationship("ChatGroup", backref="messages")


class EmailMessage(Base):
    """Internal email messages"""
    __tablename__ = "email_messages"

    id = Column(Integer, primary_key=True, index=True)
    sender_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    subject = Column(String(200), nullable=False)
    body = Column(Text, nullable=False)
    category = Column(Enum(EmailCategory), default=EmailCategory.GENERAL)
    is_read = Column(Boolean, default=False)
    is_draft = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    sender = relationship("User", backref="sent_emails")
    recipients = relationship("EmailRecipient", back_populates="email")


class EmailRecipient(Base):
    """Email recipients (many-to-many relationship)"""
    __tablename__ = "email_recipients"

    id = Column(Integer, primary_key=True, index=True)
    email_id = Column(Integer, ForeignKey("email_messages.id"), nullable=False)
    recipient_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    recipient_type = Column(String(10), default="to")  # to, cc, bcc
    is_read = Column(Boolean, default=False)
    read_at = Column(DateTime)

    email = relationship("EmailMessage", back_populates="recipients")
    recipient = relationship("User", backref="received_emails")


class Meeting(Base):
    """Meeting scheduler"""
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    organizer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    meeting_link = Column(String(500))  # Placeholder for video call link
    status = Column(Enum(MeetingStatus), default=MeetingStatus.SCHEDULED)
    is_recurring = Column(Boolean, default=False)
    recurrence_pattern = Column(String(50))  # daily, weekly, monthly
    created_at = Column(DateTime, default=datetime.utcnow)

    organizer = relationship("User", backref="organized_meetings")
    participants = relationship("MeetingParticipant", back_populates="meeting")


class MeetingParticipant(Base):
    """Meeting participants"""
    __tablename__ = "meeting_participants"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # pending, accepted, declined, tentative
    status = Column(String(20), default="pending")
    response_at = Column(DateTime)
    joined_at = Column(DateTime)
    left_at = Column(DateTime)

    meeting = relationship("Meeting", back_populates="participants")
    user = relationship("User", backref="meeting_participations")


class CallType(str, enum.Enum):
    """Call type enumeration"""
    VIDEO = "video"
    VOICE = "voice"


class CallStatus(str, enum.Enum):
    """Call status enumeration"""
    INITIATED = "initiated"
    CONNECTED = "connected"
    COMPLETED = "completed"
    MISSED = "missed"
    REJECTED = "rejected"


class CallLog(Base):
    """Video and voice call logging"""
    __tablename__ = "call_logs"

    id = Column(Integer, primary_key=True, index=True)
    caller_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    call_type = Column(Enum(CallType), nullable=False)  # video or voice
    status = Column(Enum(CallStatus), default=CallStatus.INITIATED)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime)
    duration_seconds = Column(Integer, default=0)  # Duration in seconds
    notes = Column(Text)

    caller = relationship("User", foreign_keys=[
                          caller_id], backref="calls_made")
    receiver = relationship("User", foreign_keys=[
                            receiver_id], backref="calls_received")


class Document(Base):
    """Document sharing"""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50))  # pdf, doc, xls, image, etc.
    file_size = Column(Integer)  # in bytes
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    description = Column(Text)
    category = Column(String(50), default="general")  # personal, shared, group
    group_id = Column(Integer, ForeignKey("chat_groups.id"), nullable=True)
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    uploader = relationship("User", backref="uploaded_documents")
    group = relationship("ChatGroup", backref="documents")


class UserPermission(Base):
    """Granular user permissions for communication features"""
    __tablename__ = "user_permissions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # e.g., can_chat, can_send_email
    permission_key = Column(String(50), nullable=False)
    is_allowed = Column(Boolean, default=True)
    # If True, overrides role permissions
    is_global = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    user = relationship("User", backref="permissions")


class ScreenAccess(Base):
    """Screen access permissions for employees"""
    __tablename__ = "screen_access"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # profile, tasks, leaves, attendance, documents, chat
    screen_key = Column(String(50), nullable=False)
    is_enabled = Column(Boolean, default=True)
    granted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    granted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    user = relationship("User", foreign_keys=[
                        user_id], backref="screen_access")
    granter = relationship("User", foreign_keys=[granted_by])


# Available screen access keys
SCREEN_ACCESS_KEYS = {
    "profile": {"name": "My Profile", "icon": ft.Icons.PERSON, "description": "View and edit personal profile"},
    "tasks": {"name": "My Tasks", "icon": ft.Icons.TASK, "description": "View and manage assigned tasks"},
    "leaves": {"name": "Time Off", "icon": ft.Icons.CALENDAR_MONTH, "description": "Request and manage leave requests"},
    "attendance": {"name": "Attendance", "icon": ft.Icons.ACCESS_TIME, "description": "View attendance records"},
    "documents": {"name": "Documents", "icon": ft.Icons.DESCRIPTION, "description": "Access and share documents"},
    "chat": {"name": "Chat", "icon": ft.Icons.CHAT, "description": "Send and receive messages"},
}


def get_default_screen_access(role_name: str) -> dict:
    """Get default screen access based on role"""
    default_access = {
        "admin": {
            "profile": True,
            "tasks": True,
            "leaves": True,
            "attendance": True,
            "documents": True,
            "chat": True,
        },
        "employee": {
            "profile": True,  # Profile always enabled
            "tasks": False,
            "leaves": False,
            "attendance": False,
            "documents": False,
            "chat": False,
        }
    }
    return default_access.get(role_name.lower(), default_access["employee"])


# ==================== DEFAULT PERMISSIONS ====================

# Default permission keys
COMMUNICATION_PERMISSIONS = {
    # Chat permissions
    "can_chat": True,
    "can_create_group": True,
    "can_join_groups": True,
    "can_call_video": True,
    "can_call_voice": True,
    # Email permissions
    "can_send_email": True,
    "can_receive_email": True,
    "can_announce": False,  # Only managers/admins
    "can_send_resignation": False,  # Only employees
    # Meeting permissions
    "can_schedule_meeting": True,
    "can_join_meeting": True,
    "can_invite_others": True,
    # Document permissions
    "can_upload_document": True,
    "can_download_document": True,
    "can_share_document": True,
    "can_delete_document": False,
}


def get_default_permissions_for_role(role_name: str) -> dict:
    """Get default permissions based on role name"""
    base_permissions = COMMUNICATION_PERMISSIONS.copy()

    if role_name == "admin":
        # Admin has all permissions
        return {k: True for k in base_permissions.keys()}
    elif role_name in ["hr_manager", "manager"]:
        # Managers have most permissions
        return {
            **base_permissions,
            "can_announce": True,
            "can_delete_document": True,
            "can_send_resignation": False,  # Not applicable
        }
    else:  # employee
        # Regular employees have basic permissions
        return {
            **base_permissions,
            "can_create_group": False,
            "can_announce": False,
            "can_delete_document": False,
            "can_invite_others": False,
        }


# ==================== INITIALIZATION ====================

def init_database():
    """Initialize database with default data"""
    import bcrypt
    from database.connection import get_db_session
    from database.models import Company, Role, LeaveTypeConfig

    session = get_db_session()
    try:
        # Create default company
        if not session.query(Company).first():
            company = Company(
                name="Vernika Technologies",
                email="hr@vernika.com",
                phone="+91-XXXX-XXXXXX",
                address="India"
            )
            session.add(company)

        # Create default roles
        if not session.query(Role).first():
            admin_role = Role(
                name="admin",
                display_name="Administrator",
                level=100,
                permissions={
                    "manage_users": True, "manage_employees": True,
                    "manage_departments": True, "view_reports": True
                }
            )
            session.add(admin_role)

            employee_role = Role(
                name="employee",
                display_name="Employee",
                level=10,
                permissions={"view_profile": True, "apply_leave": True}
            )
            session.add(employee_role)

        # Create default admin user
        if not session.query(User).first():
            admin_role = session.query(Role).filter_by(name="admin").first()
            if admin_role:
                admin_user = User(
                    username="admin",
                    email="admin@vernika.com",
                    password_hash=bcrypt.hashpw(
                        "admin123".encode(), bcrypt.gensalt()).decode(),
                    role_id=admin_role.id
                )
                session.add(admin_user)

        # Create default leave types
        if not session.query(LeaveTypeConfig).first():
            for lt in [
                {"name": "annual", "display_name": "Annual Leave",
                    "max_days_per_year": 20},
                {"name": "sick", "display_name": "Sick Leave",
                    "max_days_per_year": 10},
                {"name": "personal",
                    "display_name": "Personal Leave", "max_days_per_year": 5},
            ]:
                session.add(LeaveTypeConfig(**lt))

        # Create default departments
        if not session.query(Department).first():
            dept_hr = Department(name="Human Resources", code="HR")
            session.add(dept_hr)
            dept_it = Department(name="Information Technology", code="IT")
            session.add(dept_it)
            dept_fin = Department(name="Finance", code="FIN")
            session.add(dept_fin)
            dept_mkt = Department(name="Marketing", code="MKT")
            session.add(dept_mkt)
            dept_ops = Department(name="Operations", code="OPS")
            session.add(dept_ops)
            session.flush()

            # Create default positions
            if not session.query(Position).first():
                positions = [
                    Position(title="HR Manager", code="HRMGR",
                             department_id=dept_hr.id),
                    Position(title="Software Developer",
                             code="DEV", department_id=dept_it.id),
                    Position(title="Accountant", code="ACC",
                             department_id=dept_fin.id),
                    Position(title="Marketing Specialist",
                             code="MKTSP", department_id=dept_mkt.id),
                    Position(title="Operations Manager",
                             code="OPSMGR", department_id=dept_ops.id),
                ]
                for pos in positions:
                    session.add(pos)

        session.commit()
        print("✅ Database initialized successfully!")
        print("   Login: admin / admin123")

    except Exception as e:
        session.rollback()
        print(f"❌ Error initializing database: {e}")
    finally:
        session.close()


# ==================== ETL & DATA INTEGRATION MODELS ====================

class ETLJobStatus(str, enum.Enum):
    """ETL Job status enumeration"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ETLJobType(str, enum.Enum):
    """ETL Job type enumeration"""
    IMPORT = "import"
    EXPORT = "export"
    SYNC = "sync"
    POWERBI_REFRESH = "powerbi_refresh"


class ETLJob(Base):
    """
    ETL Job model for tracking data import/export operations
    """
    __tablename__ = "etl_jobs"

    id = Column(Integer, primary_key=True, index=True)
    job_name = Column(String(200), nullable=False)
    job_type = Column(Enum(ETLJobType), nullable=False)
    # Source table for export, target for import
    source_table = Column(String(100))
    # Target table for import, source for export
    target_table = Column(String(100))
    source_file = Column(String(500))  # Excel file path for import
    status = Column(Enum(ETLJobStatus), default=ETLJobStatus.PENDING)
    total_rows = Column(Integer, default=0)
    processed_rows = Column(Integer, default=0)
    success_rows = Column(Integer, default=0)
    failed_rows = Column(Integer, default=0)
    error_log = Column(Text)  # JSON string of errors
    column_mapping = Column(JSON)  # Mapping of Excel columns to DB fields
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    created_by = relationship("User", backref="etl_jobs")


class DataImportLog(Base):
    """
    Log for individual row imports
    """
    __tablename__ = "data_import_logs"

    id = Column(Integer, primary_key=True, index=True)
    etl_job_id = Column(Integer, ForeignKey("etl_jobs.id"), nullable=False)
    row_number = Column(Integer, nullable=False)  # Row number in source Excel
    status = Column(String(20), default="success")  # success, failed, skipped
    error_message = Column(Text)
    data_hash = Column(String(64))  # Hash of row data for deduplication
    imported_data = Column(JSON)  # The imported data as JSON
    created_at = Column(DateTime, default=datetime.utcnow)

    etl_job = relationship("ETLJob", backref="import_logs")


class PowerBIRefreshLog(Base):
    """
    Log for Power BI dataset refresh operations
    """
    __tablename__ = "powerbi_refresh_logs"

    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(String(100), nullable=False)
    dataset_name = Column(String(200), nullable=False)
    workspace_id = Column(String(100))
    status = Column(Enum(ETLJobStatus), default=ETLJobStatus.PENDING)
    triggered_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    refresh_type = Column(String(50), default="full")  # full, incremental
    error_message = Column(Text)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

    triggered_by = relationship("User", backref="powerbi_refresh_logs")


class ExcelTemplate(Base):
    """
    Store Excel template configurations for data import
    """
    __tablename__ = "excel_templates"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    target_table = Column(String(100), nullable=False)
    column_mappings = Column(JSON, nullable=False)  # {excel_col: db_field}
    required_columns = Column(JSON)  # List of required columns
    sample_file_path = Column(String(500))
    is_active = Column(Boolean, default=True)
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    created_by = relationship("User", backref="excel_templates")


# ==================== ETL HELPER FUNCTIONS ====================

def get_etl_status_counts() -> dict:
    """Get counts of ETL jobs by status"""
    from database.connection import get_db_session
    session = get_db_session()
    try:
        result = {}
        for status in ETLJobStatus:
            count = session.query(ETLJob).filter_by(status=status).count()
            result[status.value] = count
        return result
    finally:
        session.close()


def get_recent_etl_jobs(limit: int = 10) -> list:
    """Get recent ETL jobs"""
    from database.connection import get_db_session
    session = get_db_session()
    try:
        jobs = session.query(ETLJob).order_by(
            ETLJob.created_at.desc()
        ).limit(limit).all()
        return jobs
    finally:
        session.close()


# ==================== POWER BI CONFIGURATION ====================

# Power BI configuration keys (stored in database or config)
POWERBI_CONFIG = {
    "tenant_id": "",
    "client_id": "",
    "client_secret": "",
    "workspace_id": "",
    "authority_url": "https://login.microsoftonline.com/",
    "resource_url": "https://analysis.windows.net/powerbi/api",
}

# Default column mappings for common tables
DEFAULT_COLUMN_MAPPINGS = {
    "employees": {
        "Employee Code": "employee_code",
        "First Name": "first_name",
        "Last Name": "last_name",
        "Email": "email",
        "Phone": "phone",
        "Department": "department_id",
        "Position": "position_id",
        "Date of Joining": "date_of_joining",
        "Basic Salary": "basic_salary",
    },
    "departments": {
        "Department Name": "name",
        "Code": "code",
        "Description": "description",
    },
    "attendances": {
        "Employee Code": "employee_id",
        "Date": "date",
        "Status": "status",
        "Check In": "check_in",
        "Check Out": "check_out",
    },
}
