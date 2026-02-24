"""
Vernika - Database Indexes for Performance
Creates indexes to improve query performance for 200+ users
Run this script to add performance indexes to the database
"""

import logging
from sqlalchemy import text
from database.session_manager import get_engine, get_session

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_performance_indexes():
    """Create indexes for better performance with 200+ users"""

    indexes = [
        # User indexes
        ("idx_users_username", "users", "username"),
        ("idx_users_email", "users", "email"),
        ("idx_users_status", "users", "status"),
        ("idx_users_is_online", "users", "is_online"),

        # Employee indexes
        ("idx_employees_user_id", "employees", "user_id"),
        ("idx_employees_department_id", "employees", "department_id"),
        ("idx_employees_position_id", "employees", "position_id"),
        ("idx_employees_is_active", "employees", "is_active"),
        ("idx_employees_employee_code", "employees", "employee_code"),

        # Attendance indexes
        ("idx_attendance_employee_id", "attendance", "employee_id"),
        ("idx_attendance_date", "attendance", "date"),
        ("idx_attendance_status", "attendance", "status"),

        # Leave request indexes
        ("idx_leave_requests_employee_id", "leave_requests", "employee_id"),
        ("idx_leave_requests_status", "leave_requests", "status"),
        ("idx_leave_requests_start_date", "leave_requests", "start_date"),
        ("idx_leave_requests_end_date", "leave_requests", "end_date"),

        # Task indexes
        ("idx_tasks_assigned_to_id", "tasks", "assigned_to_id"),
        ("idx_tasks_created_by_id", "tasks", "created_by_id"),
        ("idx_tasks_status", "tasks", "status"),
        ("idx_tasks_due_date", "tasks", "due_date"),

        # Chat message indexes
        ("idx_chat_messages_sender_id", "chat_messages", "sender_id"),
        ("idx_chat_messages_receiver_id", "chat_messages", "receiver_id"),
        ("idx_chat_messages_group_id", "chat_messages", "group_id"),
        ("idx_chat_messages_created_at", "chat_messages", "created_at"),

        # Email indexes
        ("idx_email_messages_sender_id", "email_messages", "sender_id"),
        ("idx_email_recipients_recipient_id", "email_recipients", "recipient_id"),

        # Meeting indexes
        ("idx_meetings_organizer_id", "meetings", "organizer_id"),
        ("idx_meetings_start_time", "meetings", "start_time"),
        ("idx_meeting_participants_user_id", "meeting_participants", "user_id"),

        # Document indexes
        ("idx_documents_uploaded_by", "documents", "uploaded_by"),
        ("idx_documents_category", "documents", "category"),

        # Audit log indexes
        ("idx_audit_logs_user_id", "audit_logs", "user_id"),
        ("idx_audit_logs_created_at", "audit_logs", "created_at"),

        # Data sheet indexes
        ("idx_data_sheets_created_by", "data_sheets", "created_by"),
        ("idx_data_sheet_columns_sheet_id", "data_sheet_columns", "sheet_id"),
        ("idx_data_sheet_rows_sheet_id", "data_sheet_rows", "sheet_id"),

        # Time tracking indexes
        ("idx_time_tracking_user_id", "time_tracking", "user_id"),
        ("idx_time_tracking_date", "time_tracking", "date"),

        # Project indexes
        ("idx_projects_created_by", "projects", "created_by"),
        ("idx_projects_status", "projects", "status"),

        # Inventory indexes
        ("idx_inventory_category_id", "inventory", "category_id"),
        ("idx_inventory_is_low_stock", "inventory", "is_low_stock"),
    ]

    engine = get_engine()

    with engine.connect() as conn:
        for index_name, table_name, column_name in indexes:
            try:
                # Check if index exists
                result = conn.execute(text(f"""
                    SELECT 1 FROM pg_indexes 
                    WHERE indexname = '{index_name}'
                """))

                if result.fetchone():
                    logger.info(f"Index {index_name} already exists, skipping")
                    continue

                # Create index
                sql = f"CREATE INDEX CONCURRENTLY IF NOT EXISTS {index_name} ON {table_name} ({column_name})"
                conn.execute(text(sql))
                conn.commit()
                logger.info(f"Created index: {index_name}")

            except Exception as e:
                logger.error(f"Error creating index {index_name}: {e}")
                # Try without CONCURRENTLY for older PostgreSQL
                try:
                    sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} ({column_name})"
                    conn.execute(text(sql))
                    conn.commit()
                    logger.info(
                        f"Created index (non-concurrent): {index_name}")
                except Exception as e2:
                    logger.error(f"Failed to create index {index_name}: {e2}")

    logger.info("Index creation completed!")


def create_composite_indexes():
    """Create composite indexes for common query patterns"""

    composite_indexes = [
        # Attendance - get employee attendance for date range
        ("idx_attendance_employee_date", "attendance", "(employee_id, date)"),

        # Leave requests - get approved leaves for date range
        ("idx_leave_requests_status_dates",
         "leave_requests", "(status, start_date, end_date)"),

        # Chat messages - get conversation between two users
        ("idx_chat_messages_conversation", "chat_messages",
         "(sender_id, receiver_id, created_at)"),

        # Chat group messages
        ("idx_chat_messages_group", "chat_messages", "(group_id, created_at)"),

        # Tasks - get user's tasks by status
        ("idx_tasks_user_status", "tasks", "(assigned_to_id, status)"),

        # Audit logs - user's recent activity
        ("idx_audit_logs_user_time", "audit_logs", "(user_id, created_at DESC)"),
    ]

    engine = get_engine()

    with engine.connect() as conn:
        for index_name, table_name, columns in composite_indexes:
            try:
                result = conn.execute(text(f"""
                    SELECT 1 FROM pg_indexes 
                    WHERE indexname = '{index_name}'
                """))

                if result.fetchone():
                    logger.info(
                        f"Composite index {index_name} already exists, skipping")
                    continue

                sql = f"CREATE INDEX CONCURRENTLY IF NOT EXISTS {index_name} ON {table_name} {columns}"
                conn.execute(text(sql))
                conn.commit()
                logger.info(f"Created composite index: {index_name}")

            except Exception as e:
                logger.error(
                    f"Error creating composite index {index_name}: {e}")
                try:
                    sql = f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name} {columns}"
                    conn.execute(text(sql))
                    conn.commit()
                    logger.info(
                        f"Created composite index (non-concurrent): {index_name}")
                except Exception as e2:
                    logger.error(
                        f"Failed to create composite index {index_name}: {e2}")

    logger.info("Composite index creation completed!")


if __name__ == "__main__":
    print("=" * 60)
    print("Creating performance indexes for 200+ users...")
    print("=" * 60)

    create_performance_indexes()
    create_composite_indexes()

    print("=" * 60)
    print("Done! Database is optimized for multi-user access.")
    print("=" * 60)
