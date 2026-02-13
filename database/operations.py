
# Vernika Application - Database Operations
# Complete CRUD operations for HR Management System

from sqlalchemy.orm import Session
from sqlalchemy import func, or_
from datetime import datetime, date
import bcrypt
import secrets
from database.models import (
    User, Role, Employee, Department, Position,
    Attendance, LeaveRequest, LeaveBalance, LeaveTypeConfig,
    Task, TaskComment, AuditLog, Message, TimeOff,
    UserStatus, LeaveStatus, AttendanceStatus, TaskPriority, TaskStatus, Gender,
    # Communication models
    ChatGroup, ChatGroupMember, ChatMessage, EmailMessage, EmailRecipient,
    Meeting, MeetingParticipant, Document, UserPermission,
    EmailCategory, MeetingStatus, MessageType, CallLog, CallType, CallStatus
)


# ==================== USER OPERATIONS ====================

def get_user_by_username(db: Session, username: str):
    """Get user by username"""
    return db.query(User).filter(User.username == username).first()


def get_user_by_email(db: Session, email: str):
    """Get user by email"""
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int):
    """Get user by ID"""
    return db.query(User).filter(User.id == user_id).first()


def create_user(db: Session, username: str, email: str, password: str, role_id: int):
    """Create a new user"""
    user = User(
        username=username,
        email=email,
        role_id=role_id,
        password_hash=bcrypt.hashpw(
            password.encode(), bcrypt.gensalt()).decode()
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_all_users(db: Session, skip: int = 0, limit: int = 100):
    """Get all users with pagination"""
    return db.query(User).offset(skip).limit(limit).all()


def update_user_status(db: Session, user_id: int, status: UserStatus):
    """Activate or deactivate a user"""
    user = get_user_by_id(db, user_id)
    if user:
        user.status = status
        db.commit()
    return user


def delete_user(db: Session, user_id: int):
    """Delete a user"""
    user = get_user_by_id(db, user_id)
    if user:
        db.delete(user)
        db.commit()
        return True
    return False


# ==================== ROLE OPERATIONS ====================

def get_role_by_name(db: Session, role_name: str):
    """Get role by name"""
    return db.query(Role).filter(Role.name == role_name).first()


def get_role_by_id(db: Session, role_id: int):
    """Get role by ID"""
    return db.query(Role).filter(Role.id == role_id).first()


def get_all_roles(db: Session):
    """Get all roles"""
    return db.query(Role).all()


def create_role(db: Session, name: str, display_name: str, level: int = 1,
                description: str = None, permissions: dict = None):
    """Create a new role"""
    role = Role(
        name=name,
        display_name=display_name,
        level=level,
        description=description,
        permissions=permissions or {}
    )
    db.add(role)
    db.commit()
    db.refresh(role)
    return role


# ==================== DEPARTMENT OPERATIONS ====================

def get_all_departments(db: Session):
    """Get all departments"""
    return db.query(Department).all()


def get_department_by_id(db: Session, dept_id: int):
    """Get department by ID"""
    return db.query(Department).filter(Department.id == dept_id).first()


def get_department_by_code(db: Session, code: str):
    """Get department by code"""
    return db.query(Department).filter(Department.code == code).first()


def create_department(db: Session, name: str, code: str, description: str = None, head_id: int = None):
    """Create a new department"""
    department = Department(
        name=name,
        code=code,
        description=description,
        head_id=head_id
    )
    db.add(department)
    db.commit()
    db.refresh(department)
    return department


def update_department(db: Session, dept_id: int, **kwargs):
    """Update a department"""
    department = get_department_by_id(db, dept_id)
    if department:
        for key, value in kwargs.items():
            if hasattr(department, key):
                setattr(department, key, value)
        db.commit()
        db.refresh(department)
    return department


def delete_department(db: Session, dept_id: int):
    """Delete a department"""
    department = get_department_by_id(db, dept_id)
    if department:
        db.delete(department)
        db.commit()
        return True
    return False


# ==================== POSITION OPERATIONS ====================

def get_all_positions(db: Session):
    """Get all positions"""
    return db.query(Position).all()


def get_position_by_id(db: Session, pos_id: int):
    """Get position by ID"""
    return db.query(Position).filter(Position.id == pos_id).first()


def get_positions_by_department(db: Session, department_id: int):
    """Get positions by department"""
    return db.query(Position).filter(Position.department_id == department_id).all()


def create_position(db: Session, title: str, code: str, department_id: int = None,
                    description: str = None, min_salary: float = None, max_salary: float = None):
    """Create a new position"""
    position = Position(
        title=title,
        code=code,
        department_id=department_id,
        description=description,
        min_salary=min_salary,
        max_salary=max_salary
    )
    db.add(position)
    db.commit()
    db.refresh(position)
    return position


def update_position(db: Session, pos_id: int, **kwargs):
    """Update a position"""
    position = get_position_by_id(db, pos_id)
    if position:
        for key, value in kwargs.items():
            if hasattr(position, key):
                setattr(position, key, value)
        db.commit()
        db.refresh(position)
    return position


def delete_position(db: Session, pos_id: int):
    """Delete a position"""
    position = get_position_by_id(db, pos_id)
    if position:
        db.delete(position)
        db.commit()
        return True
    return False


# ==================== EMPLOYEE OPERATIONS ====================

def get_employee_by_user_id(db: Session, user_id: int):
    """Get employee profile by user ID"""
    return db.query(Employee).filter(Employee.user_id == user_id).first()


def get_employee_by_id(db: Session, emp_id: int):
    """Get employee by ID"""
    return db.query(Employee).filter(Employee.id == emp_id).first()


def get_all_employees(db: Session, skip: int = 0, limit: int = 100):
    """Get all employees with pagination"""
    return db.query(Employee).offset(skip).limit(limit).all()


def create_employee_with_user(db: Session, username: str, email: str, password: str,
                              role_id: int, first_name: str, last_name: str,
                              department_id: int = None, position_id: int = None,
                              phone: str = None, date_of_birth: date = None,
                              gender: Gender = None, employee_code: str = None):
    """Create both a user and employee profile in a transaction"""
    # Generate employee code if not provided
    if not employee_code:
        max_code = db.query(func.max(Employee.id)).scalar() or 0
        employee_code = f"EMP{str(max_code + 1).zfill(4)}"

    # Create user first
    user = User(
        username=username,
        email=email,
        role_id=role_id,
        password_hash=bcrypt.hashpw(
            password.encode(), bcrypt.gensalt()).decode()
    )
    db.add(user)
    db.flush()  # Get the user ID

    # Create employee profile
    employee = Employee(
        employee_code=employee_code,
        user_id=user.id,
        first_name=first_name,
        last_name=last_name,
        email=email,
        department_id=department_id,
        position_id=position_id,
        phone=phone,
        date_of_birth=date_of_birth,
        gender=gender
    )
    db.add(employee)
    db.commit()
    db.refresh(employee)
    return employee


def update_employee(db: Session, emp_id: int, **kwargs):
    """Update employee profile"""
    employee = get_employee_by_id(db, emp_id)
    if employee:
        for key, value in kwargs.items():
            if hasattr(employee, key):
                setattr(employee, key, value)
        db.commit()
        db.refresh(employee)
    return employee


def delete_employee(db: Session, emp_id: int):
    """Delete an employee and their user account"""
    employee = get_employee_by_id(db, emp_id)
    if employee:
        user_id = employee.user_id
        db.delete(employee)
        if user_id:
            user = get_user_by_id(db, user_id)
            if user:
                db.delete(user)
        db.commit()
        return True
    return False


def get_employees_by_department(db: Session, department_id: int):
    """Get all employees in a department"""
    return db.query(Employee).filter(Employee.department_id == department_id).all()


def get_active_employees(db: Session):
    """Get all active employees"""
    return db.query(Employee).filter(Employee.is_active == True).all()


def search_employees(db: Session, search_term: str):
    """Search employees by name or code"""
    return db.query(Employee).filter(
        (Employee.first_name.contains(search_term)) |
        (Employee.last_name.contains(search_term)) |
        (Employee.employee_code.contains(search_term)) |
        (Employee.email.contains(search_term))
    ).all()


# ==================== ATTENDANCE OPERATIONS ====================

def mark_attendance(db: Session, employee_id: int, date: date = None,
                    status: AttendanceStatus = AttendanceStatus.PRESENT,
                    check_in: datetime = None, check_out: datetime = None):
    """Mark attendance for an employee"""
    if date is None:
        date = datetime.now().date()

    # Check if attendance already exists for this date
    existing = db.query(Attendance).filter(
        Attendance.employee_id == employee_id,
        Attendance.date == date
    ).first()

    if existing:
        # Update existing record
        existing.check_in = check_in or existing.check_in
        existing.check_out = check_out or existing.check_out
        existing.status = status
        db.commit()
        db.refresh(existing)
        return existing

    # Calculate working hours if both check-in and check-out are provided
    working_hours = None
    if check_in and check_out:
        working_hours = (check_out - check_in).total_seconds() / 3600

    attendance = Attendance(
        employee_id=employee_id,
        date=date,
        check_in=check_in,
        check_out=check_out,
        status=status,
        working_hours=working_hours
    )
    db.add(attendance)
    db.commit()
    db.refresh(attendance)
    return attendance


def get_attendance_records(db: Session, employee_id: int = None,
                           start_date: date = None, end_date: date = None,
                           skip: int = 0, limit: int = 100):
    """Get attendance records with optional filters"""
    query = db.query(Attendance)

    if employee_id:
        query = query.filter(Attendance.employee_id == employee_id)
    if start_date:
        query = query.filter(Attendance.date >= start_date)
    if end_date:
        query = query.filter(Attendance.date <= end_date)

    return query.order_by(Attendance.date.desc()).offset(skip).limit(limit).all()


def get_today_attendance(db: Session, employee_id: int):
    """Get today's attendance for an employee"""
    today = datetime.now().date()
    return db.query(Attendance).filter(
        Attendance.employee_id == employee_id,
        Attendance.date == today
    ).first()


def get_attendance_summary(db: Session, employee_id: int, month: int = None, year: int = None):
    """Get attendance summary for an employee"""
    from datetime import datetime

    if year is None:
        year = datetime.now().year
    if month is None:
        month = datetime.now().month

    records = db.query(Attendance).filter(
        Attendance.employee_id == employee_id
    ).all()

    present = sum(1 for r in records if r.status == AttendanceStatus.PRESENT)
    absent = sum(1 for r in records if r.status == AttendanceStatus.ABSENT)
    late = sum(1 for r in records if r.status == AttendanceStatus.LATE)
    on_leave = sum(1 for r in records if r.status == AttendanceStatus.ON_LEAVE)

    return {
        "present": present,
        "absent": absent,
        "late": late,
        "on_leave": on_leave,
        "total": len(records)
    }


# ==================== LEAVE OPERATIONS ====================

def get_leave_type_configs(db: Session):
    """Get all leave type configurations"""
    return db.query(LeaveTypeConfig).all()


def get_leave_type_by_id(db: Session, leave_type_id: int):
    """Get leave type by ID"""
    return db.query(LeaveTypeConfig).filter(LeaveTypeConfig.id == leave_type_id).first()


def create_leave_request(db: Session, employee_id: int, leave_type_id: int,
                         start_date: date, end_date: date, reason: str):
    """Create a leave request"""
    # Calculate days requested
    days = (end_date - start_date).days + 1

    leave_request = LeaveRequest(
        employee_id=employee_id,
        leave_type_id=leave_type_id,
        start_date=start_date,
        end_date=end_date,
        days_requested=days,
        reason=reason,
        status=LeaveStatus.PENDING
    )
    db.add(leave_request)
    db.commit()
    db.refresh(leave_request)
    return leave_request


def approve_leave_request(db: Session, request_id: int, approved_by: int = None):
    """Approve a leave request"""
    leave_request = db.query(LeaveRequest).filter(
        LeaveRequest.id == request_id).first()
    if leave_request:
        leave_request.status = LeaveStatus.APPROVED
        db.commit()
        db.refresh(leave_request)
    return leave_request


def reject_leave_request(db: Session, request_id: int):
    """Reject a leave request"""
    leave_request = db.query(LeaveRequest).filter(
        LeaveRequest.id == request_id).first()
    if leave_request:
        leave_request.status = LeaveStatus.REJECTED
        db.commit()
        db.refresh(leave_request)
    return leave_request


def cancel_leave_request(db: Session, request_id: int):
    """Cancel a leave request"""
    leave_request = db.query(LeaveRequest).filter(
        LeaveRequest.id == request_id).first()
    if leave_request:
        leave_request.status = LeaveStatus.CANCELLED
        db.commit()
        db.refresh(leave_request)
    return leave_request


def get_leave_requests(db: Session, employee_id: int = None,
                       status: LeaveStatus = None, skip: int = 0, limit: int = 100):
    """Get leave requests with optional filters"""
    query = db.query(LeaveRequest)

    if employee_id:
        query = query.filter(LeaveRequest.employee_id == employee_id)
    if status:
        query = query.filter(LeaveRequest.status == status)

    return query.order_by(LeaveRequest.created_at.desc()).offset(skip).limit(limit).all()


def get_employee_leave_balance(db: Session, employee_id: int, year: int = None):
    """Get leave balance for an employee for a year"""
    from datetime import datetime
    if year is None:
        year = datetime.now().year

    return db.query(LeaveBalance).filter(
        LeaveBalance.employee_id == employee_id,
        LeaveBalance.year == year
    ).all()


def initialize_employee_leave_balance(db: Session, employee_id: int, year: int = None):
    """Initialize leave balance for a new employee"""
    from datetime import datetime
    if year is None:
        year = datetime.now().year

    leave_types = get_leave_type_configs(db)
    for lt in leave_types:
        existing = db.query(LeaveBalance).filter(
            LeaveBalance.employee_id == employee_id,
            LeaveBalance.leave_type_id == lt.id,
            LeaveBalance.year == year
        ).first()

        if not existing:
            balance = LeaveBalance(
                employee_id=employee_id,
                leave_type_id=lt.id,
                year=year,
                total_days=lt.max_days_per_year,
                used_days=0
            )
            db.add(balance)

    db.commit()


# ==================== TASK OPERATIONS ====================

def create_task(db: Session, title: str, description: str,
                assigned_to_id: int, created_by_id: int,
                priority: TaskPriority = TaskPriority.MEDIUM,
                due_date: date = None, status: TaskStatus = TaskStatus.TODO):
    """Create a new task"""
    task = Task(
        title=title,
        description=description,
        assigned_to_id=assigned_to_id,
        created_by_id=created_by_id,
        priority=priority,
        due_date=due_date,
        status=status
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


def get_task_by_id(db: Session, task_id: int):
    """Get task by ID"""
    return db.query(Task).filter(Task.id == task_id).first()


def update_task_status(db: Session, task_id: int, status: TaskStatus):
    """Update task status"""
    task = get_task_by_id(db, task_id)
    if task:
        task.status = status
        db.commit()
        db.refresh(task)
    return task


def update_task(db: Session, task_id: int, **kwargs):
    """Update task details"""
    task = get_task_by_id(db, task_id)
    if task:
        for key, value in kwargs.items():
            if hasattr(task, key):
                setattr(task, key, value)
        db.commit()
        db.refresh(task)
    return task


def delete_task(db: Session, task_id: int):
    """Delete a task"""
    task = get_task_by_id(db, task_id)
    if task:
        db.delete(task)
        db.commit()
        return True
    return False


def get_tasks_for_user(db: Session, user_id: int):
    """Get all tasks assigned to a user"""
    employee = get_employee_by_user_id(db, user_id)
    if employee:
        return db.query(Task).filter(
            Task.assigned_to_id == employee.id
        ).order_by(Task.created_at.desc()).all()
    return []


def get_tasks_created_by_user(db: Session, user_id: int):
    """Get all tasks created by a user"""
    employee = get_employee_by_user_id(db, user_id)
    if employee:
        return db.query(Task).filter(
            Task.created_by_id == employee.id
        ).order_by(Task.created_at.desc()).all()
    return []


def get_all_tasks(db: Session, skip: int = 0, limit: int = 100):
    """Get all tasks with pagination"""
    return db.query(Task).order_by(Task.created_at.desc()).offset(skip).limit(limit).all()


def get_tasks_by_status(db: Session, status: TaskStatus):
    """Get tasks by status"""
    return db.query(Task).filter(Task.status == status).all()


def add_task_comment(db: Session, task_id: int, employee_id: int, content: str):
    """Add a comment to a task"""
    comment = TaskComment(
        task_id=task_id,
        employee_id=employee_id,
        content=content
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def get_task_comments(db: Session, task_id: int):
    """Get all comments for a task"""
    return db.query(TaskComment).filter(
        TaskComment.task_id == task_id
    ).order_by(TaskComment.created_at.asc()).all()


# ==================== AUDIT LOG OPERATIONS ====================

def create_audit_log(db: Session, user_id: int, action: str, details: str = None):
    """Create an audit log entry"""
    log = AuditLog(
        user_id=user_id,
        action=action,
        details=details
    )
    db.add(log)
    db.commit()
    return log


def get_user_audit_logs(db: Session, user_id: int, limit: int = 100):
    """Get audit logs for a specific user"""
    return db.query(AuditLog)\
             .filter(AuditLog.user_id == user_id)\
             .order_by(AuditLog.created_at.desc())\
             .limit(limit)\
             .all()


def get_all_audit_logs(db: Session, skip: int = 0, limit: int = 100):
    """Get all audit logs with pagination"""
    return db.query(AuditLog)\
             .order_by(AuditLog.created_at.desc())\
             .offset(skip)\
             .limit(limit)\
             .all()


# ==================== MESSAGE OPERATIONS ====================

def create_message(db: Session, sender_id: int, receiver_id: int, content: str):
    """Create a new message"""
    message = Message(
        sender_id=sender_id,
        receiver_id=receiver_id,
        content=content
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_messages_between_users(db: Session, user1_id: int, user2_id: int, limit: int = 50):
    """Get messages between two users"""
    return db.query(Message)\
             .filter(
                 ((Message.sender_id == user1_id) & (Message.receiver_id == user2_id)) |
                 ((Message.sender_id == user2_id) &
                  (Message.receiver_id == user1_id))
    )\
        .order_by(Message.created_at)\
        .limit(limit)\
        .all()


def get_unread_messages(db: Session, user_id: int):
    """Get unread messages for a user"""
    return db.query(Message)\
             .filter(Message.receiver_id == user_id, Message.is_read == False)\
             .order_by(Message.created_at)\
             .all()


def mark_messages_as_read(db: Session, user_id: int, sender_id: int):
    """Mark messages from a sender as read for a user"""
    db.query(Message)\
      .filter(
          Message.sender_id == sender_id,
          Message.receiver_id == user_id,
          Message.is_read == False
    )\
        .update({"is_read": True})
    db.commit()


def get_recent_messages(db: Session, user_id: int, limit: int = 20):
    """Get recent messages for a user (sent or received)"""
    return db.query(Message)\
             .filter(
                 (Message.sender_id == user_id) | (
                     Message.receiver_id == user_id)
    )\
        .order_by(Message.created_at.desc())\
        .limit(limit)\
        .all()


# ==================== TIME OFF OPERATIONS ====================

def create_time_off_request(db: Session, user_id: int, leave_type: str,
                            start_date: date, end_date: date, reason: str = None):
    """Create a time off request"""
    time_off = TimeOff(
        user_id=user_id,
        leave_type=leave_type,
        start_date=start_date,
        end_date=end_date,
        reason=reason
    )
    db.add(time_off)
    db.commit()
    db.refresh(time_off)
    return time_off


def get_time_off_requests_for_user(db: Session, user_id: int):
    """Get time off requests for a user"""
    return db.query(TimeOff)\
             .filter(TimeOff.user_id == user_id)\
             .order_by(TimeOff.created_at.desc())\
             .all()


def update_time_off_status(db: Session, request_id: int, status: LeaveStatus, approved_by: int = None):
    """Update time off request status"""
    time_off = db.query(TimeOff).filter(TimeOff.id == request_id).first()
    if time_off:
        time_off.status = status
        if approved_by:
            time_off.approved_by = approved_by
        db.commit()
        return time_off
    return None


def get_all_time_off_requests(db: Session, skip: int = 0, limit: int = 100):
    """Get all time off requests with pagination"""
    return db.query(TimeOff)\
             .order_by(TimeOff.created_at.desc())\
             .offset(skip)\
             .limit(limit)\
             .all()


# ==================== DASHBOARD STATISTICS ====================

def get_dashboard_stats(db: Session):
    """Get dashboard statistics"""
    total_users = db.query(User).count()
    total_employees = db.query(Employee).count()
    total_departments = db.query(Department).count()
    total_positions = db.query(Position).count()

    pending_tasks = db.query(Task).filter(
        Task.status == TaskStatus.TODO).count()
    in_progress_tasks = db.query(Task).filter(
        Task.status == TaskStatus.IN_PROGRESS).count()
    completed_tasks = db.query(Task).filter(
        Task.status == TaskStatus.COMPLETED).count()

    pending_leaves = db.query(LeaveRequest).filter(
        LeaveRequest.status == LeaveStatus.PENDING).count()

    return {
        "total_users": total_users,
        "total_employees": total_employees,
        "total_departments": total_departments,
        "total_positions": total_positions,
        "pending_tasks": pending_tasks,
        "in_progress_tasks": in_progress_tasks,
        "completed_tasks": completed_tasks,
        "pending_leaves": pending_leaves
    }


# ==================== CHAT GROUP OPERATIONS ====================

def create_chat_group(db: Session, name: str, description: str, created_by: int):
    """Create a new chat group"""
    group = ChatGroup(
        name=name,
        description=description,
        created_by=created_by
    )
    db.add(group)
    db.commit()
    db.refresh(group)

    # Add creator as admin member
    add_group_member(db, group.id, created_by, role="admin")
    return group


def add_group_member(db: Session, group_id: int, user_id: int, role: str = "member"):
    """Add a member to a group"""
    # Check if already a member
    existing = db.query(ChatGroupMember).filter(
        ChatGroupMember.group_id == group_id,
        ChatGroupMember.user_id == user_id
    ).first()
    if existing:
        return existing

    member = ChatGroupMember(
        group_id=group_id,
        user_id=user_id,
        role=role
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member


def remove_group_member(db: Session, group_id: int, user_id: int):
    """Remove a member from a group"""
    member = db.query(ChatGroupMember).filter(
        ChatGroupMember.group_id == group_id,
        ChatGroupMember.user_id == user_id
    ).first()
    if member:
        db.delete(member)
        db.commit()
        return True
    return False


def get_user_groups(db: Session, user_id: int):
    """Get all groups a user is a member of"""
    return db.query(ChatGroup).join(ChatGroupMember).filter(
        ChatGroupMember.user_id == user_id,
        ChatGroup.is_active == True
    ).all()


def get_group_by_id(db: Session, group_id: int):
    """Get group by ID"""
    return db.query(ChatGroup).filter(ChatGroup.id == group_id).first()


def get_group_members(db: Session, group_id: int):
    """Get all members of a group"""
    return db.query(ChatGroupMember).filter(
        ChatGroupMember.group_id == group_id
    ).all()


def delete_chat_group(db: Session, group_id: int):
    """Soft delete a chat group"""
    group = get_group_by_id(db, group_id)
    if group:
        group.is_active = False
        db.commit()
        return True
    return False


# ==================== CHAT MESSAGE OPERATIONS ====================

def send_chat_message(db: Session, sender_id: int, content: str,
                      group_id: int = None, receiver_id: int = None,
                      message_type: MessageType = MessageType.TEXT,
                      has_attachment: bool = False, attachment_path: str = None):
    """Send a chat message (direct or group)"""
    message = ChatMessage(
        sender_id=sender_id,
        group_id=group_id,
        receiver_id=receiver_id,
        content=content,
        message_type=message_type,
        has_attachment=has_attachment,
        attachment_path=attachment_path
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def get_group_messages(db: Session, group_id: int, limit: int = 100):
    """Get messages for a group"""
    return db.query(ChatMessage).filter(
        ChatMessage.group_id == group_id
    ).order_by(ChatMessage.created_at.desc()).limit(limit).all()


def get_direct_messages(db: Session, user1_id: int, user2_id: int, limit: int = 100):
    """Get direct messages between two users"""
    return db.query(ChatMessage).filter(
        or_(
            (ChatMessage.sender_id == user1_id) & (
                ChatMessage.receiver_id == user2_id),
            (ChatMessage.sender_id == user2_id) & (
                ChatMessage.receiver_id == user1_id)
        ),
        ChatMessage.group_id == None
    ).order_by(ChatMessage.created_at.desc()).limit(limit).all()


def get_unread_chat_messages(db: Session, user_id: int):
    """Get unread chat messages for a user"""
    return db.query(ChatMessage).filter(
        ChatMessage.receiver_id == user_id,
        ChatMessage.is_read == False
    ).all()


def mark_chat_messages_as_read(db: Session, user_id: int, sender_id: int = None, group_id: int = None):
    """Mark messages as read"""
    query = db.query(ChatMessage).filter(
        ChatMessage.receiver_id == user_id,
        ChatMessage.is_read == False
    )
    if sender_id:
        query = query.filter(ChatMessage.sender_id == sender_id)
    if group_id:
        query = query.filter(ChatMessage.group_id == group_id)
    query.update({"is_read": True})
    db.commit()


# ==================== EMAIL OPERATIONS ====================

def send_email(db: Session, sender_id: int, subject: str, body: str,
               recipient_ids: list, category: EmailCategory = EmailCategory.GENERAL,
               cc_ids: list = None, bcc_ids: list = None, is_draft: bool = False):
    """Send an internal email"""
    # Create email message
    email = EmailMessage(
        sender_id=sender_id,
        subject=subject,
        body=body,
        category=category,
        is_draft=is_draft
    )
    db.add(email)
    db.flush()

    # Add recipients
    for recipient_id in recipient_ids:
        recipient = EmailRecipient(
            email_id=email.id,
            recipient_id=recipient_id,
            recipient_type="to"
        )
        db.add(recipient)

    if cc_ids:
        for cc_id in cc_ids:
            recipient = EmailRecipient(
                email_id=email.id,
                recipient_id=cc_id,
                recipient_type="cc"
            )
            db.add(recipient)

    if bcc_ids:
        for bcc_id in bcc_ids:
            recipient = EmailRecipient(
                email_id=email.id,
                recipient_id=bcc_id,
                recipient_type="bcc"
            )
            db.add(recipient)

    db.commit()
    db.refresh(email)
    return email


def get_user_emails(db: Session, user_id: int, folder: str = "inbox", limit: int = 50):
    """Get emails for a user by folder"""
    if folder == "inbox":
        return db.query(EmailMessage).join(EmailRecipient).filter(
            EmailRecipient.recipient_id == user_id,
            EmailMessage.is_draft == False
        ).order_by(EmailMessage.created_at.desc()).limit(limit).all()
    elif folder == "sent":
        return db.query(EmailMessage).filter(
            EmailMessage.sender_id == user_id,
            EmailMessage.is_draft == False
        ).order_by(EmailMessage.created_at.desc()).limit(limit).all()
    elif folder == "drafts":
        return db.query(EmailMessage).filter(
            EmailMessage.sender_id == user_id,
            EmailMessage.is_draft == True
        ).order_by(EmailMessage.created_at.desc()).limit(limit).all()
    elif folder == "announcements":
        return db.query(EmailMessage).filter(
            EmailMessage.sender_id == user_id,
            EmailMessage.category == EmailCategory.ANNOUNCEMENT
        ).order_by(EmailMessage.created_at.desc()).limit(limit).all()
    return []


def get_email_by_id(db: Session, email_id: int):
    """Get email by ID"""
    return db.query(EmailMessage).filter(EmailMessage.id == email_id).first()


def mark_email_as_read(db: Session, email_id: int, user_id: int):
    """Mark an email as read"""
    recipient = db.query(EmailRecipient).filter(
        EmailRecipient.email_id == email_id,
        EmailRecipient.recipient_id == user_id
    ).first()
    if recipient:
        recipient.is_read = True
        recipient.read_at = datetime.utcnow()
        db.commit()


def delete_email(db: Session, email_id: int):
    """Delete an email (draft)"""
    email = get_email_by_id(db, email_id)
    if email and email.is_draft:
        db.delete(email)
        db.commit()
        return True
    return False


def get_unread_email_count(db: Session, user_id: int):
    """Get count of unread emails"""
    return db.query(EmailRecipient).filter(
        EmailRecipient.recipient_id == user_id,
        EmailRecipient.is_read == False
    ).count()


# ==================== MEETING OPERATIONS ====================

def create_meeting(db: Session, title: str, organizer_id: int,
                   start_time: datetime, end_time: datetime,
                   description: str = None, participant_ids: list = None,
                   is_recurring: bool = False, recurrence_pattern: str = None):
    """Create a new meeting"""
    meeting = Meeting(
        title=title,
        organizer_id=organizer_id,
        start_time=start_time,
        end_time=end_time,
        description=description,
        is_recurring=is_recurring,
        recurrence_pattern=recurrence_pattern,
        meeting_link=f"https://vernika.local/meeting/{organizer_id}_{int(start_time.timestamp())}"
    )
    db.add(meeting)
    db.flush()

    # Add participants
    if participant_ids:
        for participant_id in participant_ids:
            participant = MeetingParticipant(
                meeting_id=meeting.id,
                user_id=participant_id
            )
            db.add(participant)

    db.commit()
    db.refresh(meeting)
    return meeting


def get_user_meetings(db: Session, user_id: int, upcoming: bool = True, limit: int = 50):
    """Get meetings for a user"""
    now = datetime.utcnow()
    query = db.query(Meeting).join(MeetingParticipant).filter(
        MeetingParticipant.user_id == user_id
    )

    if upcoming:
        query = query.filter(Meeting.start_time >= now)
    else:
        query = query.filter(Meeting.start_time < now)

    return query.order_by(Meeting.start_time).limit(limit).all()


def get_meeting_by_id(db: Session, meeting_id: int):
    """Get meeting by ID"""
    return db.query(Meeting).filter(Meeting.id == meeting_id).first()


def get_meeting_participants(db: Session, meeting_id: int):
    """Get all participants of a meeting"""
    return db.query(MeetingParticipant).filter(
        MeetingParticipant.meeting_id == meeting_id
    ).all()


def update_meeting_status(db: Session, meeting_id: int, status: MeetingStatus):
    """Update meeting status"""
    meeting = get_meeting_by_id(db, meeting_id)
    if meeting:
        meeting.status = status
        db.commit()
        db.refresh(meeting)
    return meeting


def respond_to_meeting(db: Session, meeting_id: int, user_id: int, status: str):
    """Respond to a meeting invitation"""
    participant = db.query(MeetingParticipant).filter(
        MeetingParticipant.meeting_id == meeting_id,
        MeetingParticipant.user_id == user_id
    ).first()
    if participant:
        participant.status = status
        participant.response_at = datetime.utcnow()
        db.commit()
        db.refresh(participant)
    return participant


def cancel_meeting(db: Session, meeting_id: int):
    """Cancel a meeting"""
    return update_meeting_status(db, meeting_id, MeetingStatus.CANCELLED)


def get_upcoming_meetings(db: Session, user_id: int = None, limit: int = 10):
    """Get upcoming meetings"""
    now = datetime.utcnow()
    query = db.query(Meeting).filter(
        Meeting.start_time >= now,
        Meeting.status == MeetingStatus.SCHEDULED
    )

    if user_id:
        query = query.join(MeetingParticipant).filter(
            MeetingParticipant.user_id == user_id
        )

    return query.order_by(Meeting.start_time).limit(limit).all()


# ==================== CALL LOG OPERATIONS ====================

def initiate_call(db: Session, caller_id: int, receiver_id: int, call_type: CallType):
    """Initiate a new call (video or voice)"""
    call_log = CallLog(
        caller_id=caller_id,
        receiver_id=receiver_id,
        call_type=call_type,
        status=CallStatus.INITIATED,
        started_at=datetime.utcnow()
    )
    db.add(call_log)
    db.commit()
    db.refresh(call_log)
    return call_log


def end_call(db: Session, call_id: int, status: CallStatus = CallStatus.COMPLETED):
    """End a call and calculate duration"""
    call_log = db.query(CallLog).filter(CallLog.id == call_id).first()
    if call_log:
        call_log.status = status
        call_log.ended_at = datetime.utcnow()

        # Calculate duration in seconds
        if call_log.started_at and call_log.ended_at:
            delta = call_log.ended_at - call_log.started_at
            call_log.duration_seconds = int(delta.total_seconds())

        db.commit()
        db.refresh(call_log)
    return call_log


def get_call_history(db: Session, user_id: int, limit: int = 50):
    """Get call history for a user (both incoming and outgoing)"""
    return db.query(CallLog).filter(
        (CallLog.caller_id == user_id) | (CallLog.receiver_id == user_id)
    ).order_by(CallLog.started_at.desc()).limit(limit).all()


def get_user_calls(db: Session, user_id: int, call_type: CallType = None, limit: int = 50):
    """Get calls for a user filtered by type"""
    query = db.query(CallLog).filter(
        (CallLog.caller_id == user_id) | (CallLog.receiver_id == user_id)
    )

    if call_type:
        query = query.filter(CallLog.call_type == call_type)

    return query.order_by(CallLog.started_at.desc()).limit(limit).all()


def get_missed_calls(db: Session, user_id: int, limit: int = 50):
    """Get missed calls for a user"""
    return db.query(CallLog).filter(
        CallLog.receiver_id == user_id,
        CallLog.status == CallStatus.MISSED
    ).order_by(CallLog.started_at.desc()).limit(limit).all()


def get_call_by_id(db: Session, call_id: int):
    """Get a call log by ID"""
    return db.query(CallLog).filter(CallLog.id == call_id).first()


# ==================== DOCUMENT OPERATIONS ====================

def upload_document(db: Session, name: str, file_path: str, uploaded_by: int,
                    file_type: str = None, file_size: int = None,
                    description: str = None, category: str = "personal",
                    group_id: int = None, is_public: bool = False):
    """Upload a document"""
    document = Document(
        name=name,
        file_path=file_path,
        file_type=file_type,
        file_size=file_size,
        uploaded_by=uploaded_by,
        description=description,
        category=category,
        group_id=group_id,
        is_public=is_public
    )
    db.add(document)
    db.commit()
    db.refresh(document)
    return document


def get_user_documents(db: Session, user_id: int, category: str = None, limit: int = 100):
    """Get documents for a user"""
    query = db.query(Document).filter(
        or_(
            Document.uploaded_by == user_id,
            Document.is_public == True
        )
    )

    if category:
        query = query.filter(Document.category == category)

    return query.order_by(Document.created_at.desc()).limit(limit).all()


def get_group_documents(db: Session, group_id: int, limit: int = 100):
    """Get documents shared with a group"""
    return db.query(Document).filter(
        Document.group_id == group_id
    ).order_by(Document.created_at.desc()).limit(limit).all()


def get_document_by_id(db: Session, document_id: int):
    """Get document by ID"""
    return db.query(Document).filter(Document.id == document_id).first()


def delete_document(db: Session, document_id: int, user_id: int):
    """Delete a document (only by uploader or admin)"""
    doc = get_document_by_id(db, document_id)
    if doc and (doc.uploaded_by == user_id or is_admin(db, user_id)):
        db.delete(doc)
        db.commit()
        return True
    return False


# ==================== USER PERMISSION OPERATIONS ====================

def get_user_permission(db: Session, user_id: int, permission_key: str):
    """Get a specific permission for a user"""
    # First check user-specific permission
    perm = db.query(UserPermission).filter(
        UserPermission.user_id == user_id,
        UserPermission.permission_key == permission_key
    ).first()

    if perm:
        return perm.is_allowed

    # If no user-specific permission, check role-based permissions
    user = get_user_by_id(db, user_id)
    if user and user.role:
        return user.role.permissions.get(permission_key, False)

    return False


def set_user_permission(db: Session, user_id: int, permission_key: str,
                        is_allowed: bool, is_global: bool = True):
    """Set a permission for a user (overrides role permissions if is_global=True)"""
    existing = db.query(UserPermission).filter(
        UserPermission.user_id == user_id,
        UserPermission.permission_key == permission_key
    ).first()

    if existing:
        existing.is_allowed = is_allowed
        existing.is_global = is_global
        existing.updated_at = datetime.utcnow()
    else:
        perm = UserPermission(
            user_id=user_id,
            permission_key=permission_key,
            is_allowed=is_allowed,
            is_global=is_global
        )
        db.add(perm)

    db.commit()


def get_all_user_permissions(db: Session, user_id: int):
    """Get all permissions for a user (including defaults from role)"""
    user = get_user_by_id(db, user_id)
    if not user:
        return {}

    # Start with role permissions
    permissions = user.role.permissions.copy() if user.role else {}

    # Override with user-specific permissions
    user_perms = db.query(UserPermission).filter(
        UserPermission.user_id == user_id,
        UserPermission.is_global == True
    ).all()

    for perm in user_perms:
        permissions[perm.permission_key] = perm.is_allowed

    return permissions


def has_permission(db: Session, user_id: int, permission_key: str) -> bool:
    """Check if a user has a specific permission"""
    return get_user_permission(db, user_id, permission_key)


def is_admin(db: Session, user_id: int) -> bool:
    """Check if a user is an admin"""
    user = get_user_by_id(db, user_id)
    return user and user.role and user.role.name == "admin"


def initialize_user_permissions(db: Session, user_id: int):
    """Initialize default permissions for a new user"""
    from database.models import get_default_permissions_for_role

    user = get_user_by_id(db, user_id)
    if not user or not user.role:
        return

    defaults = get_default_permissions_for_role(user.role.name)

    for perm_key, is_allowed in defaults.items():
        # Only set if not already set
        existing = db.query(UserPermission).filter(
            UserPermission.user_id == user_id,
            UserPermission.permission_key == perm_key
        ).first()

        if not existing:
            perm = UserPermission(
                user_id=user_id,
                permission_key=perm_key,
                is_allowed=is_allowed,
                is_global=False
            )
            db.add(perm)

    db.commit()


# ==================== HELPER FUNCTIONS ====================

def get_internal_email(username: str) -> str:
    """Get internal email address for a username"""
    return f"{username}@vernika.local"


def get_username_from_email(email: str) -> str:
    """Extract username from internal email"""
    if email.endswith("@vernika.local"):
        return email.replace("@vernika.local", "")
    return email


def search_users_by_username(db: Session, search_term: str):
    """Search users by username for autocomplete"""
    return db.query(User).filter(
        User.username.contains(search_term),
        User.status == UserStatus.ACTIVE
    ).limit(10).all()


# ==================== AUTHENTICATION OPERATIONS ====================

def authenticate_user(db: Session, username_or_email: str, password: str):
    """
    Authenticate a user with username/email and password.

    Args:
        db: Database session
        username_or_email: Username or email address
        password: Plain text password

    Returns:
        tuple: (success: bool, user_data: dict or None, message: str)
    """
    # Find user by username or email
    user = db.query(User).filter(
        (User.username == username_or_email) | (
            User.email == username_or_email)
    ).first()

    if not user:
        return False, None, "Invalid username or password"

    # Check if user is active
    if user.status != UserStatus.ACTIVE:
        return False, None, "Account is deactivated. Please contact administrator."

    # Verify password
    password_bytes = password.encode('utf-8')

    # Get stored hash
    stored_hash = user.password_hash
    if isinstance(stored_hash, str):
        hash_bytes = stored_hash.encode('utf-8')
    else:
        hash_bytes = stored_hash

    if not bcrypt.checkpw(password_bytes, hash_bytes):
        return False, None, "Invalid username or password"

    # Generate session token
    session_token = secrets.token_urlsafe(32)

    # Update user presence and session
    user.is_online = True
    user.last_seen = datetime.utcnow()
    user.session_token = session_token
    user.last_login = datetime.utcnow()
    db.commit()

    # Get role name
    role_name = user.role.name if user.role else "employee"

    # Build user data dict
    user_data = {
        'id': user.id,
        'user_id': user.id,
        'username': user.username,
        'email': user.email,
        'role': role_name,
        'role_id': user.role_id,
        'status': user.status.value if hasattr(user.status, 'value') else str(user.status),
        'session_token': session_token
    }

    return True, user_data, "Login successful"


def logout_user(db: Session, user_id: int):
    """
    Logout a user (mark as offline).

    Args:
        db: Database session
        user_id: User ID

    Returns:
        bool: True if successful
    """
    user = get_user_by_id(db, user_id)
    if user:
        user.is_online = False
        user.last_seen = datetime.utcnow()
        user.session_token = None
        db.commit()
        return True
    return False


def update_user_presence(db: Session, user_id: int, is_online: bool = True):
    """
    Update user presence status.

    Args:
        db: Database session
        user_id: User ID
        is_online: Whether user is online

    Returns:
        bool: True if successful
    """
    user = get_user_by_id(db, user_id)
    if user:
        user.is_online = is_online
        user.last_seen = datetime.utcnow()
        db.commit()
        return True
    return False


def get_online_users(db: Session):
    """
    Get all currently online users.

    Args:
        db: Database session

    Returns:
        list: List of online users
    """
    return db.query(User).filter(User.is_online == True).all()


def get_user_by_session(db: Session, session_token: str):
    """
    Get user by session token.

    Args:
        db: Database session
        session_token: Session token

    Returns:
        User or None
    """
    return db.query(User).filter(User.session_token == session_token).first()


def refresh_user_session(db: Session, user_id: int):
    """
    Refresh user session (update last_seen).

    Args:
        db: Database session
        user_id: User ID

    Returns:
        bool: True if successful
    """
    user = get_user_by_id(db, user_id)
    if user:
        user.last_seen = datetime.utcnow()
        db.commit()
        return True
    return False


# ==================== USER WITH EMPLOYEE INFO ====================

def get_user_with_employee(db: Session, user_id: int):
    """
    Get user with their employee profile.

    Args:
        db: Database session
        user_id: User ID

    Returns:
        tuple: (user: User or None, employee: Employee or None)
    """
    user = get_user_by_id(db, user_id)
    if not user:
        return None, None

    employee = get_employee_by_user_id(db, user_id)
    return user, employee


def get_all_users_with_employees(db: Session):
    """
    Get all users with their employee profiles.

    Args:
        db: Database session

    Returns:
        list: List of tuples (user, employee)
    """
    users = db.query(User).all()
    result = []
    for user in users:
        employee = get_employee_by_user_id(db, user.id)
        result.append((user, employee))
    return result
