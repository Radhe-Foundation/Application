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
    ForeignKey, Float, Enum, JSON, UniqueConstraint, Index, LargeBinary
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


class Team(Base):
    """Team model for team management"""
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Announcement(Base):
    """Announcement model for company announcements"""
    __tablename__ = "announcements"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    # general, important, event, policy
    type = Column(String(50), default="general")
    # low, normal, important, high
    priority = Column(String(50), default="normal")
    author = Column(String(100), default="Admin")
    views = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)


class Project(Base):
    """Project model for project management"""
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text)
    client_name = Column(String(200))
    start_date = Column(Date)
    end_date = Column(Date)
    budget = Column(Float, default=0)
    # planning, active, on_hold, completed, cancelled
    status = Column(String(50), default="planning")
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

    # Profile photo
    profile_photo = Column(String(500), nullable=True)
    # Binary data for multi-device access
    profile_photo_data = Column(LargeBinary, nullable=True)

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

    # Relationships
    employee = relationship("Employee", backref="leave_requests")
    leave_type = relationship("LeaveTypeConfig", backref="leave_requests")


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
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    leave_type = Column(String(50), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    reason = Column(Text)
    status = Column(Enum(LeaveStatus), default=LeaveStatus.PENDING)
    created_at = Column(DateTime, default=datetime.utcnow)
    approved_by = Column(Integer, ForeignKey("employees.id"))

    user = relationship("User", foreign_keys=[
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


class EmailGroup(Base):
    """Email distribution groups for sending to multiple recipients"""
    __tablename__ = "email_groups"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    members = relationship("EmailGroupMember", back_populates="group")
    creator = relationship("User")


class EmailGroupMember(Base):
    """Membership in email groups"""
    __tablename__ = "email_group_members"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("email_groups.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(String(20), default="member")  # admin, member
    joined_at = Column(DateTime, default=datetime.utcnow)

    group = relationship("EmailGroup", back_populates="members")
    user = relationship("User")


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


class ButtonAccess(Base):
    """Button-level access permissions for employees"""
    __tablename__ = "button_access"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    # buttons like employees_add, employees_edit, leaves_apply, etc.
    button_key = Column(String(100), nullable=False)
    is_enabled = Column(Boolean, default=True)
    granted_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    granted_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    user = relationship("User", foreign_keys=[
                        user_id], backref="button_access")
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


# ==================== NEW MODELS FOR ENHANCED FEATURES ====================

# ==================== Organization Hierarchy ====================

class OrgHierarchy(Base):
    """Organization hierarchy for org chart display"""
    __tablename__ = "org_hierarchy"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    reports_to_id = Column(Integer, ForeignKey("employees.id"), nullable=True)
    # 1=CEO, 2=Head, 3=Manager, 4=TeamLead, 5=Employee
    hierarchy_level = Column(Integer, default=5)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    employee = relationship("Employee", foreign_keys=[employee_id])
    manager = relationship("Employee", foreign_keys=[reports_to_id])


# ==================== Team Members ====================

class TeamMember(Base):
    """Team members with roles and status"""
    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    role = Column(String(50), default="member")  # team_lead, member
    # work status: active, on_break, on_leave, offline
    work_status = Column(String(50), default="active")
    assigned_tasks = Column(Text)  # JSON string of tasks
    joined_date = Column(Date, default=datetime.utcnow().date)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    team = relationship("Team", backref="members")
    employee = relationship("Employee", backref="team_memberships")


# ==================== Project Members ====================

class ProjectMember(Base):
    """Project members with roles"""
    __tablename__ = "project_members"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    # project_manager, team_lead, developer, designer, tester, consultant
    role = Column(String(50), default="developer")
    assigned_tasks = Column(Text)  # JSON string of tasks
    hourly_rate = Column(Float, default=0)
    is_active = Column(Boolean, default=True)
    joined_date = Column(Date, default=datetime.utcnow().date)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", backref="members")
    employee = relationship("Employee", backref="project_memberships")


# ==================== Inventory Management ====================

class InventoryCategory(Base):
    """Inventory product categories"""
    __tablename__ = "inventory_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    parent_id = Column(Integer, ForeignKey(
        "inventory_categories.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    parent = relationship("InventoryCategory", remote_side=[
                          id], backref="children")


class Product(Base):
    """Inventory products/items"""
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    sku = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    category_id = Column(Integer, ForeignKey("inventory_categories.id"))
    unit = Column(String(20), default="pcs")  # pcs, kg, liter, etc.
    min_stock = Column(Integer, default=0)
    max_stock = Column(Integer, default=1000)
    current_stock = Column(Integer, default=0)
    purchase_price = Column(Float, default=0)
    sale_price = Column(Float, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    category = relationship("InventoryCategory", backref="products")


class ProductImage(Base):
    """Product images"""
    __tablename__ = "product_images"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    image_path = Column(String(500), nullable=False)
    is_primary = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", backref="images")


class InventoryTransaction(Base):
    """Inventory in/out transactions"""
    __tablename__ = "inventory_transactions"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    # purchase, sale, adjustment, return
    transaction_type = Column(String(20), nullable=False)
    quantity = Column(Integer, nullable=False)
    quantity_before = Column(Integer, default=0)
    quantity_after = Column(Integer, default=0)
    notes = Column(Text)
    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    product = relationship("Product", backref="transactions")
    created_by = relationship("User")


class Supplier(Base):
    """Suppliers for inventory management"""
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    contact_person = Column(String(100))
    email = Column(String(100))
    phone = Column(String(20))
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(100))
    pincode = Column(String(20))
    gst_number = Column(String(50))
    pan_number = Column(String(50))
    notes = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)


# ==================== Payment & Transactions ====================

class TransactionCategory(str, enum.Enum):
    """Transaction categories"""
    INCOME = "income"
    EXPENSE = "expense"
    SALARY = "salary"
    VENDOR = "vendor"
    CLIENT = "client"
    OTHER = "other"


class PaymentMethod(str, enum.Enum):
    """Payment methods"""
    CASH = "cash"
    BANK_TRANSFER = "bank_transfer"
    UPI = "upi"
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    CHEQUE = "cheque"
    OTHER = "other"


class TransactionStatus(str, enum.Enum):
    """Transaction status"""
    PENDING = "pending"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    FAILED = "failed"


class Transaction(Base):
    """Payment and transaction records"""
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, index=True)
    transaction_type = Column(String(20), nullable=False)  # income, expense
    amount = Column(Float, nullable=False)
    currency = Column(String(10), default="INR")
    # salary, vendor, client, etc.
    category = Column(String(50), nullable=False)
    description = Column(Text)
    transaction_date = Column(Date, nullable=False)
    payment_method = Column(String(50), default="cash")
    reference_number = Column(String(100))
    status = Column(String(20), default="completed")
    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    created_by = relationship("User", backref="transactions")


class TransactionAttachment(Base):
    """Transaction file attachments (max 500KB per file)"""
    __tablename__ = "transaction_attachments"

    id = Column(Integer, primary_key=True, index=True)
    transaction_id = Column(Integer, ForeignKey(
        "transactions.id"), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(200), nullable=False)
    file_size = Column(Integer, nullable=False)  # in bytes, max 512000 (500KB)
    # Binary data for multi-device access
    file_data = Column(LargeBinary, nullable=True)
    uploaded_by_id = Column(Integer, ForeignKey("users.id"))
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    transaction = relationship("Transaction", backref="attachments")
    uploaded_by = relationship("User")


# ==================== Custom Data Sheets ====================

class DataSheet(Base):
    """Custom spreadsheet-like data sheets"""
    __tablename__ = "data_sheets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    created_by_id = Column(Integer, ForeignKey("users.id"))
    is_public = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    created_by = relationship("User", backref="data_sheets")


class DataSheetColumn(Base):
    """Columns for custom data sheets"""
    __tablename__ = "data_sheet_columns"

    id = Column(Integer, primary_key=True, index=True)
    sheet_id = Column(Integer, ForeignKey("data_sheets.id"), nullable=False)
    column_name = Column(String(100), nullable=False)
    # text, number, date, image, file, link
    column_type = Column(String(20), nullable=False)
    width = Column(Integer, default=150)
    sort_order = Column(Integer, default=0)
    is_required = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    sheet = relationship("DataSheet", backref="columns")


class DataSheetRow(Base):
    """Rows for custom data sheets"""
    __tablename__ = "data_sheet_rows"

    id = Column(Integer, primary_key=True, index=True)
    sheet_id = Column(Integer, ForeignKey("data_sheets.id"), nullable=False)
    row_data = Column(JSON, default=dict)  # {column_id: value}
    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    sheet = relationship("DataSheet", backref="rows")
    created_by = relationship("User")


# ==================== CRM MODELS ====================

class LeadStatus(str, enum.Enum):
    """Lead status enumeration"""
    NEW = "new"
    CONTACTED = "contacted"
    QUALIFIED = "qualified"
    PROPOSAL = "proposal"
    NEGOTIATION = "negotiation"
    WON = "won"
    LOST = "lost"


class LeadSource(str, enum.Enum):
    """Lead source enumeration"""
    WEBSITE = "website"
    REFERRAL = "referral"
    SOCIAL_MEDIA = "social_media"
    COLD_CALL = "cold_call"
    TRADE_SHOW = "trade_show"
    ADVERTISEMENT = "advertisement"
    OTHER = "other"


class LeadPriority(str, enum.Enum):
    """Lead priority enumeration"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


class ContactCategory(str, enum.Enum):
    """Contact category"""
    CUSTOMER = "customer"
    PROSPECT = "prospect"
    PARTNER = "partner"
    VENDOR = "vendor"
    OTHER = "other"


class DealStage(str, enum.Enum):
    """Deal pipeline stages"""
    QUALIFICATION = "qualification"
    MEETING_SCHEDULED = "meeting_scheduled"
    PROPOSAL_SENT = "proposal_sent"
    NEGOTIATION = "negotiation"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"


class CRMCustomer(Base):
    """CRM Customers/Contacts"""
    __tablename__ = "crm_customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    email = Column(String(100))
    phone = Column(String(20))
    company = Column(String(200))
    designation = Column(String(100))
    address = Column(Text)
    city = Column(String(100))
    state = Column(String(100))
    country = Column(String(100))
    pincode = Column(String(20))
    # customer, prospect, partner
    category = Column(String(50), default="prospect")
    source = Column(String(50), default="website")
    notes = Column(Text)
    tags = Column(JSON, default=list)  # List of tags
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_active = Column(Boolean, default=True)
    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    created_by = relationship("User", foreign_keys=[created_by_id])


class CRMLead(Base):
    """CRM Leads"""
    __tablename__ = "crm_leads"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    email = Column(String(100))
    phone = Column(String(20))
    company = Column(String(200))
    designation = Column(String(100))
    source = Column(String(50), default="website")
    # new, contacted, qualified, proposal, negotiation, won, lost
    status = Column(String(50), default="new")
    # low, medium, high, urgent
    priority = Column(String(50), default="medium")
    expected_value = Column(Float, default=0)
    probability = Column(Integer, default=0)  # 0-100%
    notes = Column(Text)
    next_follow_up = Column(DateTime)
    converted_to_customer_id = Column(
        Integer, ForeignKey("crm_customers.id"), nullable=True)
    converted_at = Column(DateTime)
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    created_by = relationship("User", foreign_keys=[created_by_id])
    converted_to_customer = relationship(
        "CRMCustomer", foreign_keys=[converted_to_customer_id])


class CRMDeal(Base):
    """CRM Deals/Pipeline"""
    __tablename__ = "crm_deals"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    customer_id = Column(Integer, ForeignKey(
        "crm_customers.id"), nullable=False)
    value = Column(Float, default=0)
    # qualification, meeting_scheduled, proposal_sent, negotiation, closed_won, closed_lost
    stage = Column(String(50), default="qualification")
    expected_close_date = Column(Date)
    probability = Column(Integer, default=0)  # 0-100%
    notes = Column(Text)
    lost_reason = Column(Text)
    won_notes = Column(Text)
    closed_at = Column(DateTime)
    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    customer = relationship("CRMCustomer", backref="deals")
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    created_by = relationship("User", foreign_keys=[created_by_id])


class CRMActivity(Base):
    """CRM Activities (calls, meetings, tasks)"""
    __tablename__ = "crm_activities"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    # call, meeting, task, email, note
    activity_type = Column(String(50), nullable=False)
    description = Column(Text)
    due_date = Column(DateTime)
    completed_at = Column(DateTime)
    is_completed = Column(Boolean, default=False)

    # Related to
    lead_id = Column(Integer, ForeignKey("crm_leads.id"), nullable=True)
    customer_id = Column(Integer, ForeignKey(
        "crm_customers.id"), nullable=True)
    deal_id = Column(Integer, ForeignKey("crm_deals.id"), nullable=True)

    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    lead = relationship("CRMLead", foreign_keys=[lead_id])
    customer = relationship("CRMCustomer", foreign_keys=[customer_id])
    deal = relationship("CRMDeal", foreign_keys=[deal_id])
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    created_by = relationship("User", foreign_keys=[created_by_id])


class CRMProductCategory(Base):
    """CRM Product Categories"""
    __tablename__ = "crm_product_categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)


class CRMProduct(Base):
    """CRM Products/Services"""
    __tablename__ = "crm_products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    sku = Column(String(50), unique=True, nullable=True)
    description = Column(Text)
    category_id = Column(Integer, ForeignKey(
        "crm_product_categories.id"), nullable=True)
    unit_price = Column(Float, default=0)
    cost_price = Column(Float, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    category = relationship("CRMProductCategory", backref="products")


class CRMQuote(Base):
    """CRM Quotes/Proposals"""
    __tablename__ = "crm_quotes"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    quote_number = Column(String(50), unique=True, nullable=True)
    customer_id = Column(Integer, ForeignKey(
        "crm_customers.id"), nullable=False)
    deal_id = Column(Integer, ForeignKey("crm_deals.id"), nullable=True)

    # Quote details
    subtotal = Column(Float, default=0)
    tax_amount = Column(Float, default=0)
    discount_amount = Column(Float, default=0)
    total_amount = Column(Float, default=0)

    # Status: draft, sent, accepted, rejected, declined
    status = Column(String(50), default="draft")
    valid_until = Column(Date)
    notes = Column(Text)

    # Timestamps
    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    customer = relationship("CRMCustomer", backref="quotes")
    deal = relationship("CRMDeal", foreign_keys=[deal_id])
    created_by = relationship("User", foreign_keys=[created_by_id])


class CRMQuoteItem(Base):
    """CRM Quote Line Items"""
    __tablename__ = "crm_quote_items"

    id = Column(Integer, primary_key=True, index=True)
    quote_id = Column(Integer, ForeignKey("crm_quotes.id"), nullable=False)
    product_id = Column(Integer, ForeignKey("crm_products.id"), nullable=True)
    description = Column(String(500))
    quantity = Column(Float, default=1)
    unit_price = Column(Float, default=0)
    tax_rate = Column(Float, default=0)
    amount = Column(Float, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)

    quote = relationship("CRMQuote", backref="items")
    product = relationship("CRMProduct", foreign_keys=[product_id])


class CRMTask(Base):
    """CRM Tasks"""
    __tablename__ = "crm_tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    # Related to
    lead_id = Column(Integer, ForeignKey("crm_leads.id"), nullable=True)
    customer_id = Column(Integer, ForeignKey(
        "crm_customers.id"), nullable=True)
    deal_id = Column(Integer, ForeignKey("crm_deals.id"), nullable=True)

    # Task details
    due_date = Column(DateTime)
    completed_at = Column(DateTime)
    is_completed = Column(Boolean, default=False)
    # low, medium, high, urgent
    priority = Column(String(50), default="medium")

    assigned_to_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    lead = relationship("CRMLead", foreign_keys=[lead_id])
    customer = relationship("CRMCustomer", foreign_keys=[customer_id])
    deal = relationship("CRMDeal", foreign_keys=[deal_id])
    assigned_to = relationship("User", foreign_keys=[assigned_to_id])
    created_by = relationship("User", foreign_keys=[created_by_id])


# ==================== INVOICING MODELS ====================

class InvoiceStatus(str, enum.Enum):
    """Invoice status"""
    DRAFT = "draft"
    SENT = "sent"
    VIEWED = "viewed"
    PAID = "paid"
    PARTIAL = "partial"
    OVERDUE = "overdue"
    CANCELLED = "cancelled"


class Invoice(Base):
    """Invoice for customers"""
    __tablename__ = "invoices"

    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(50), unique=True, nullable=False)
    customer_id = Column(Integer, ForeignKey(
        "crm_customers.id"), nullable=False)
    deal_id = Column(Integer, ForeignKey("crm_deals.id"), nullable=True)

    invoice_date = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)

    subtotal = Column(Float, default=0)
    tax_amount = Column(Float, default=0)
    discount_amount = Column(Float, default=0)
    total_amount = Column(Float, default=0)

    status = Column(String(50), default="draft")
    notes = Column(Text)
    terms = Column(Text)

    paid_amount = Column(Float, default=0)
    paid_at = Column(DateTime)

    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    customer = relationship("CRMCustomer", backref="invoices")
    deal = relationship("CRMDeal", foreign_keys=[deal_id])
    created_by = relationship("User", foreign_keys=[created_by_id])


class InvoiceItem(Base):
    """Invoice line items"""
    __tablename__ = "invoice_items"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    description = Column(String(500), nullable=False)
    quantity = Column(Float, default=1)
    unit_price = Column(Float, default=0)
    tax_rate = Column(Float, default=0)  # Percentage
    amount = Column(Float, default=0)
    sort_order = Column(Integer, default=0)

    invoice = relationship("Invoice", backref="items")


class Payment(Base):
    """Payment records for invoices"""
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False)
    payment_number = Column(String(50), unique=True, nullable=False)
    amount = Column(Float, nullable=False)
    payment_date = Column(Date, nullable=False)
    # cash, bank_transfer, upi, card, cheque
    payment_method = Column(String(50), default="cash")
    reference_number = Column(String(100))
    notes = Column(Text)
    created_by_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)

    invoice = relationship("Invoice", backref="payments")
    created_by = relationship("User", foreign_keys=[created_by_id])


# ==================== TIME TRACKING MODELS ====================

class TimesheetStatus(str, enum.Enum):
    """Timesheet status"""
    DRAFT = "draft"
    SUBMITTED = "submitted"
    APPROVED = "approved"
    REJECTED = "rejected"


class Timesheet(Base):
    """Employee timesheets"""
    __tablename__ = "timesheets"

    id = Column(Integer, primary_key=True, index=True)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    week_start = Column(Date, nullable=False)  # Start of the week (Monday)
    week_end = Column(Date, nullable=False)  # End of the week (Sunday)
    total_hours = Column(Float, default=0)
    status = Column(String(50), default="draft")
    notes = Column(Text)
    approved_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    approved_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    employee = relationship("Employee", backref="timesheets")
    approved_by = relationship("User", foreign_keys=[approved_by_id])


class TimeEntry(Base):
    """Individual time entries"""
    __tablename__ = "time_entries"

    id = Column(Integer, primary_key=True, index=True)
    timesheet_id = Column(Integer, ForeignKey("timesheets.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=True)
    date = Column(Date, nullable=False)
    hours = Column(Float, nullable=False)
    description = Column(Text)
    is_billable = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    timesheet = relationship("Timesheet", backref="entries")
    project = relationship("Project", foreign_keys=[project_id])
    task = relationship("Task", foreign_keys=[task_id])


# ==================== ASSET MANAGEMENT MODELS ====================

class AssetStatus(str, enum.Enum):
    """Asset status"""
    AVAILABLE = "available"
    ASSIGNED = "assigned"
    MAINTENANCE = "maintenance"
    RETIRED = "retired"
    LOST = "lost"


class AssetCategory(str, enum.Enum):
    """Asset categories"""
    HARDWARE = "hardware"
    FURNITURE = "furniture"
    VEHICLE = "vehicle"
    EQUIPMENT = "equipment"
    SOFTWARE = "software"
    OTHER = "other"


class Asset(Base):
    """Company assets"""
    __tablename__ = "assets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    asset_code = Column(String(50), unique=True, nullable=False)
    category = Column(String(50), default="hardware")
    description = Column(Text)
    purchase_date = Column(Date)
    purchase_price = Column(Float, default=0)
    warranty_expiry = Column(Date)
    serial_number = Column(String(100))
    location = Column(String(200))
    status = Column(String(50), default="available")
    notes = Column(Text)
    image_path = Column(String(500))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)


class AssetAssignment(Base):
    """Asset assignment to employees"""
    __tablename__ = "asset_assignments"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)
    assigned_date = Column(Date, nullable=False)
    returned_date = Column(Date, nullable=True)
    condition_on_issue = Column(String(100), default="good")
    condition_on_return = Column(String(100), nullable=True)
    notes = Column(Text)
    assigned_by_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    asset = relationship("Asset", backref="assignments")
    employee = relationship("Employee", backref="asset_assignments")
    assigned_by = relationship("User", foreign_keys=[assigned_by_id])


class AssetMaintenance(Base):
    """Asset maintenance records"""
    __tablename__ = "asset_maintenance"

    id = Column(Integer, primary_key=True, index=True)
    asset_id = Column(Integer, ForeignKey("assets.id"), nullable=False)
    # repair, service, inspection
    maintenance_type = Column(String(50), nullable=False)
    description = Column(Text, nullable=False)
    maintenance_date = Column(Date, nullable=False)
    next_maintenance_date = Column(Date)
    cost = Column(Float, default=0)
    vendor = Column(String(200))
    performed_by = Column(String(200))
    status = Column(String(50), default="completed")
    created_at = Column(DateTime, default=datetime.utcnow)

    asset = relationship("Asset", backref="maintenance_records")


# ==================== Helper Functions ====================

def get_org_hierarchy_tree():
    """Get organization hierarchy as tree structure"""
    from database.connection import get_db_session
    session = get_db_session()
    try:
        hierarchy = session.query(OrgHierarchy).filter(
            OrgHierarchy.is_active == True
        ).all()

        # Build tree
        tree = {}
        for h in hierarchy:
            emp = session.query(Employee).filter(
                Employee.id == h.employee_id).first()
            if emp:
                tree[h.employee_id] = {
                    'id': h.id,
                    'employee_id': h.employee_id,
                    'name': f"{emp.first_name} {emp.last_name}",
                    'employee_code': emp.employee_code,
                    'reports_to_id': h.reports_to_id,
                    'level': h.hierarchy_level,
                    'position': emp.position.title if emp.position else "Employee",
                    'department': emp.department.name if emp.department else "",
                    'children': []
                }

        # Build parent-child relationships
        for emp_id, node in tree.items():
            if node['reports_to_id'] and node['reports_to_id'] in tree:
                tree[node['reports_to_id']]['children'].append(node)

        return tree
    finally:
        session.close()


# ==================== BILLING & ACCOMMODATION REQUEST MODELS ====================

class BillingRequestStatus(str, enum.Enum):
    """Billing request status enumeration"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CANCELLED = "cancelled"


class BillingRequestType(str, enum.Enum):
    """Billing request type"""
    ACCOMMODATION = "accommodation"
    BILL_REIMBURSEMENT = "bill_reimbursement"
    EXPENSE_CLAIM = "expense_claim"
    OTHER = "other"


class BillingRequest(Base):
    """
    Billing/Accommodation Request - Employees can request organization
    to reimburse/accommodate bills for accommodation or other expenses
    """
    __tablename__ = "billing_requests"

    id = Column(Integer, primary_key=True, index=True)
    request_number = Column(String(50), unique=True, nullable=False)

    # Request type: accommodation, bill_reimbursement, expense_claim, other
    request_type = Column(String(50), nullable=False,
                          default="bill_reimbursement")

    # Employee who made the request
    employee_id = Column(Integer, ForeignKey("employees.id"), nullable=False)

    # Bill details
    bill_description = Column(Text, nullable=False)
    bill_amount = Column(Float, nullable=False)
    bill_date = Column(Date, nullable=False)
    # e.g., Hotel, Travel, Medical, Office Supplies
    bill_category = Column(String(100))

    # Payment details
    payment_mode = Column(String(50))  # cash, bank_transfer, upi, cheque
    payment_details = Column(Text)  # Bank details, UPI ID, etc.

    # Request status
    # pending, approved, rejected, cancelled
    status = Column(String(50), default="pending")

    # Admin review fields
    reviewed_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    review_notes = Column(Text)

    # Notes
    notes = Column(Text)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    # Relationships
    employee = relationship("Employee", backref="billing_requests")
    reviewed_by = relationship("User", foreign_keys=[reviewed_by_id])


class BillingRequestAttachment(Base):
    """
    Attachments for billing requests (receipts, bills, QR codes, etc.)
    """
    __tablename__ = "billing_request_attachments"

    id = Column(Integer, primary_key=True, index=True)
    billing_request_id = Column(Integer, ForeignKey(
        "billing_requests.id"), nullable=False)

    file_name = Column(String(200), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=False)  # in bytes
    file_type = Column(String(50))  # pdf, jpg, png, etc.
    # Binary data for multi-device access
    file_data = Column(LargeBinary, nullable=True)

    # Attachment type: receipt, qr_code, other
    attachment_type = Column(String(50), default="receipt")

    description = Column(String(200))

    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    billing_request = relationship("BillingRequest", backref="attachments")
    uploaded_by = relationship("User")


def get_low_stock_products(threshold=None):
    """Get products with low stock"""
    from database.connection import get_db_session
    session = get_db_session()
    try:
        query = session.query(Product).filter(Product.is_active == True)
        if threshold:
            query = query.filter(Product.current_stock <= threshold)
        else:
            query = query.filter(Product.current_stock <= Product.min_stock)
        return query.all()
    finally:
        session.close()


def get_transaction_summary(start_date=None, end_date=None):
    """Get transaction summary"""
    from database.connection import get_db_session
    from sqlalchemy import func
    session = get_db_session()
    try:
        query = session.query(Transaction)
        if start_date:
            query = query.filter(Transaction.transaction_date >= start_date)
        if end_date:
            query = query.filter(Transaction.transaction_date <= end_date)

        total_income = query.filter(Transaction.transaction_type == "income",
                                    Transaction.status == "completed").func.sum(Transaction.amount) or 0
        total_expense = query.filter(Transaction.transaction_type == "expense",
                                     Transaction.status == "completed").func.sum(Transaction.amount) or 0

        return {
            'total_income': float(total_income),
            'total_expense': float(total_expense),
            'balance': float(total_income) - float(total_expense)
        }
    finally:
        session.close()
