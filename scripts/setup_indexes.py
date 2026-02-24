"""
Vernika - Direct Database Index Setup
Run this to add performance indexes to Supabase PostgreSQL
"""
import psycopg2
from psycopg2 import sql
import sys

# Database connection parameters
DB_PARAMS = {
    'host': 'db.tbofjzzufxqbwfmfapxh.supabase.co',
    'port': 5432,
    'database': 'postgres',
    'user': 'postgres',
    'password': '!vrMVXZrv84wmKH',
    'sslmode': 'require'
}

INDEXES = [
    # Users table indexes
    ("idx_users_username", "users", "username"),
    ("idx_users_email", "users", "email"),
    ("idx_users_status", "users", "status"),

    # Employees table indexes
    ("idx_employees_user_id", "employees", "user_id"),
    ("idx_employees_department_id", "employees", "department_id"),
    ("idx_employees_is_active", "employees", "is_active"),

    # Attendance table indexes (critical for real-time)
    ("idx_attendance_employee_id", "attendance", "employee_id"),
    ("idx_attendance_date", "attendance", "date"),
    ("idx_attendance_status", "attendance", "status"),

    # Chat Messages indexes (critical for realtime chat!)
    ("idx_chat_messages_sender_id", "chat_messages", "sender_id"),
    ("idx_chat_messages_receiver_id", "chat_messages", "receiver_id"),
    ("idx_chat_messages_group_id", "chat_messages", "group_id"),
    ("idx_chat_messages_created_at", "chat_messages", "created_at"),

    # Leave Requests indexes
    ("idx_leave_requests_employee_id", "leave_requests", "employee_id"),
    ("idx_leave_requests_status", "leave_requests", "status"),
    ("idx_leave_requests_start_date", "leave_requests", "start_date"),

    # Tasks indexes
    ("idx_tasks_assigned_to_id", "tasks", "assigned_to_id"),
    ("idx_tasks_created_by_id", "tasks", "created_by_id"),
    ("idx_tasks_status", "tasks", "status"),
    ("idx_tasks_priority", "tasks", "priority"),

    # Messages (direct messages)
    ("idx_messages_sender_id", "messages", "sender_id"),
    ("idx_messages_receiver_id", "messages", "receiver_id"),

    # Email indexes
    ("idx_email_messages_sender_id", "email_messages", "sender_id"),
    ("idx_email_recipients_recipient_id", "email_recipients", "recipient_id"),

    # Meeting indexes
    ("idx_meetings_organizer_id", "meetings", "organizer_id"),
    ("idx_meetings_start_time", "meetings", "start_time"),
    ("idx_meeting_participants_user_id", "meeting_participants", "user_id"),

    # Documents indexes
    ("idx_documents_uploaded_by", "documents", "uploaded_by"),
    ("idx_documents_category", "documents", "category"),
]


def create_indexes():
    """Create all performance indexes"""
    print("=" * 60)
    print("Vernika - Database Index Setup")
    print("=" * 60)

    try:
        print("\n🔌 Connecting to Supabase PostgreSQL...")
        conn = psycopg2.connect(**DB_PARAMS)
        conn.autocommit = True
        cursor = conn.cursor()
        print("✅ Connected successfully!")

        created = 0
        skipped = 0
        failed = 0

        print("\n📊 Creating indexes...")

        for index_name, table, column in INDEXES:
            try:
                # Check if index already exists
                cursor.execute("""
                    SELECT 1 FROM pg_indexes 
                    WHERE indexname = %s
                """, (index_name,))

                if cursor.fetchone():
                    print(f"  ⏭️  {index_name} - already exists")
                    skipped += 1
                    continue

                # Create index
                query = sql.SQL("CREATE INDEX IF NOT EXISTS {index} ON {table} ({column})").format(
                    index=sql.Identifier(index_name),
                    table=sql.Identifier(table),
                    column=sql.Identifier(column)
                )
                cursor.execute(query)
                print(f"  ✅ {index_name} on {table}.{column}")
                created += 1

            except Exception as e:
                print(f"  ❌ {index_name} - {str(e)[:50]}")
                failed += 1

        cursor.close()
        conn.close()

        print("\n" + "=" * 60)
        print(f"📈 Summary:")
        print(f"   ✅ Created: {created}")
        print(f"   ⏭️  Skipped: {skipped}")
        print(f"   ❌ Failed: {failed}")
        print("=" * 60)

        return True

    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        return False


if __name__ == "__main__":
    success = create_indexes()
    sys.exit(0 if success else 1)
