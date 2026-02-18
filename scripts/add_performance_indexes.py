"""
Vernika HRA - Database Performance Optimization
Add indexes to improve query performance
"""

from sqlalchemy import text
from database.connection import get_engine


def add_performance_indexes():
    """
    Add database indexes for better query performance
    Run this once to add indexes to the database
    """
    engine = get_engine()

    indexes_to_create = [
        # User indexes
        ("idx_users_username",
         "CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)"),
        ("idx_users_email", "CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)"),
        ("idx_users_status", "CREATE INDEX IF NOT EXISTS idx_users_status ON users(status)"),
        ("idx_users_role_id",
         "CREATE INDEX IF NOT EXISTS idx_users_role_id ON users(role_id)"),

        # Employee indexes
        ("idx_employees_user_id",
         "CREATE INDEX IF NOT EXISTS idx_employees_user_id ON employees(user_id)"),
        ("idx_employees_department_id",
         "CREATE INDEX IF NOT EXISTS idx_employees_department_id ON employees(department_id)"),
        ("idx_employees_position_id",
         "CREATE INDEX IF NOT EXISTS idx_employees_position_id ON employees(position_id)"),
        ("idx_employees_is_active",
         "CREATE INDEX IF NOT EXISTS idx_employees_is_active ON employees(is_active)"),
        ("idx_employees_employee_code",
         "CREATE INDEX IF NOT EXISTS idx_employees_employee_code ON employees(employee_code)"),

        # Attendance indexes - CRITICAL for performance
        ("idx_attendance_employee_date",
         "CREATE INDEX IF NOT EXISTS idx_attendance_employee_date ON attendances(employee_id, date)"),
        ("idx_attendance_date",
         "CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendances(date)"),
        ("idx_attendance_status",
         "CREATE INDEX IF NOT EXISTS idx_attendance_status ON attendances(status)"),

        # Leave request indexes
        ("idx_leave_requests_employee_id",
         "CREATE INDEX IF NOT EXISTS idx_leave_requests_employee_id ON leave_requests(employee_id)"),
        ("idx_leave_requests_status",
         "CREATE INDEX IF NOT EXISTS idx_leave_requests_status ON leave_requests(status)"),
        ("idx_leave_requests_dates",
         "CREATE INDEX IF NOT EXISTS idx_leave_requests_dates ON leave_requests(start_date, end_date)"),

        # Task indexes
        ("idx_tasks_assigned_to",
         "CREATE INDEX IF NOT EXISTS idx_tasks_assigned_to ON tasks(assigned_to_id)"),
        ("idx_tasks_created_by",
         "CREATE INDEX IF NOT EXISTS idx_tasks_created_by ON tasks(created_by_id)"),
        ("idx_tasks_status", "CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)"),
        ("idx_tasks_priority",
         "CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority)"),
        ("idx_tasks_due_date",
         "CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date)"),

        # Chat message indexes - CRITICAL for chat performance
        ("idx_chat_messages_sender",
         "CREATE INDEX IF NOT EXISTS idx_chat_messages_sender ON chat_messages(sender_id)"),
        ("idx_chat_messages_receiver",
         "CREATE INDEX IF NOT EXISTS idx_chat_messages_receiver ON chat_messages(receiver_id)"),
        ("idx_chat_messages_group",
         "CREATE INDEX IF NOT EXISTS idx_chat_messages_group ON chat_messages(group_id)"),
        ("idx_chat_messages_created_at",
         "CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at DESC)"),

        # Email indexes
        ("idx_email_messages_sender",
         "CREATE INDEX IF NOT EXISTS idx_email_messages_sender ON email_messages(sender_id)"),
        ("idx_email_messages_created_at",
         "CREATE INDEX IF NOT EXISTS idx_email_messages_created_at ON email_messages(created_at DESC)"),

        ("idx_email_recipients_email_id",
         "CREATE INDEX IF NOT EXISTS idx_email_recipients_email_id ON email_recipients(email_id)"),
        ("idx_email_recipients_recipient",
         "CREATE INDEX IF NOT EXISTS idx_email_recipients_recipient ON email_recipients(recipient_id)"),

        # Meeting indexes
        ("idx_meetings_organizer",
         "CREATE INDEX IF NOT EXISTS idx_meetings_organizer ON meetings(organizer_id)"),
        ("idx_meetings_start_time",
         "CREATE INDEX IF NOT EXISTS idx_meetings_start_time ON meetings(start_time)"),

        ("idx_meeting_participants_meeting",
         "CREATE INDEX IF NOT EXISTS idx_meeting_participants_meeting ON meeting_participants(meeting_id)"),
        ("idx_meeting_participants_user",
         "CREATE INDEX IF NOT EXISTS idx_meeting_participants_user ON meeting_participants(user_id)"),

        # Document indexes
        ("idx_documents_uploaded_by",
         "CREATE INDEX IF NOT EXISTS idx_documents_uploaded_by ON documents(uploaded_by)"),
        ("idx_documents_category",
         "CREATE INDEX IF NOT EXISTS idx_documents_category ON documents(category)"),
        ("idx_documents_group_id",
         "CREATE INDEX IF NOT EXISTS idx_documents_group_id ON documents(group_id)"),

        # Chat group indexes
        ("idx_chat_groups_created_by",
         "CREATE INDEX IF NOT EXISTS idx_chat_groups_created_by ON chat_groups(created_by)"),

        ("idx_chat_group_members_group",
         "CREATE INDEX IF NOT EXISTS idx_chat_group_members_group ON chat_group_members(group_id)"),
        ("idx_chat_group_members_user",
         "CREATE INDEX IF NOT EXISTS idx_chat_group_members_user ON chat_group_members(user_id)"),

        # Audit log indexes
        ("idx_audit_logs_user_id",
         "CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id)"),
        ("idx_audit_logs_created_at",
         "CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at DESC)"),

        # Project indexes
        ("idx_projects_status",
         "CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status)"),

        # Department indexes
        ("idx_departments_is_active",
         "CREATE INDEX IF NOT EXISTS idx_departments_is_active ON departments(is_active)"),

        # Position indexes
        ("idx_positions_department",
         "CREATE INDEX IF NOT EXISTS idx_positions_department ON positions(department_id)"),
        ("idx_positions_is_active",
         "CREATE INDEX IF NOT EXISTS idx_positions_is_active ON positions(is_active)"),

        # Leave balance indexes
        ("idx_leave_balances_employee",
         "CREATE INDEX IF NOT EXISTS idx_leave_balances_employee ON leave_balances(employee_id)"),

        # Time off indexes
        ("idx_time_off_user", "CREATE INDEX IF NOT EXISTS idx_time_off_requests_user_id ON time_off_requests(user_id)"),

        # Screen/Button access indexes
        ("idx_screen_access_user",
         "CREATE INDEX IF NOT EXISTS idx_screen_access_user_id ON screen_access(user_id)"),
        ("idx_button_access_user",
         "CREATE INDEX IF NOT EXISTS idx_button_access_user_id ON button_access(user_id)"),

        # ETL job indexes
        ("idx_etl_jobs_status",
         "CREATE INDEX IF NOT EXISTS idx_etl_jobs_status ON etl_jobs(status)"),
        ("idx_etl_jobs_created_at",
         "CREATE INDEX IF NOT EXISTS idx_etl_jobs_created_at ON etl_jobs(created_at DESC)"),
    ]

    with engine.connect() as conn:
        for index_name, sql in indexes_to_create:
            try:
                conn.execute(text(sql))
                conn.commit()
                print(f"✓ Created index: {index_name}")
            except Exception as e:
                print(f"✗ Error creating index {index_name}: {e}")

    print("\n✅ Database indexes optimization complete!")


if __name__ == "__main__":
    print("Starting database index optimization...")
    add_performance_indexes()
