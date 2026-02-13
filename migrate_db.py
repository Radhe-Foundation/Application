"""
Database Migration Script
Creates missing tables and fixes schema issues
"""

import sqlite3
import sys


def run_migration():
    """Run database migrations to add missing tables"""

    conn = sqlite3.connect('vernika.db')
    cursor = conn.cursor()

    # List of tables that should exist based on models.py
    required_tables = [
        # Core tables
        "companies",
        "roles",
        "users",
        "departments",
        "positions",
        "employees",

        # Attendance & Leave
        "attendance",
        "attendances",  # Alternative name
        "leave_type_configs",
        "leave_balances",
        "leave_requests",

        # Tasks
        "tasks",
        "task_comments",

        # Communication
        "chat_groups",
        "chat_group_members",
        "chat_messages",
        "messages",
        "email_messages",
        "email_recipients",
        "meetings",
        "meeting_participants",
        "documents",
        "user_permissions",

        # Announcements (NEW)
        "announcements",

        # Audit
        "audit_logs",
        "time_off_requests",

        # Screen Access (NEW)
        "screen_access",

        # ETL Tables (NEW)
        "etl_jobs",
        "data_import_logs",
        "powerbi_refresh_logs",
        "excel_templates",
    ]

    # Check existing tables
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    existing_tables = [row[0] for row in cursor.fetchall()]
    print(f"Existing tables: {existing_tables}")

    # Create missing tables
    created_tables = []

    # Attendance table (main one used by attendance_screen.py)
    if "attendance" not in existing_tables:
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS attendance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id INTEGER NOT NULL,
                    date TEXT NOT NULL,
                    check_in TEXT,
                    check_out TEXT,
                    status TEXT NOT NULL DEFAULT 'present',
                    working_hours REAL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (employee_id) REFERENCES employees(id),
                    UNIQUE(employee_id, date)
                )
            """)
            created_tables.append("attendance")
            print("✅ Created 'attendance' table")
        except Exception as e:
            print(f"❌ Error creating attendance table: {e}")

    # Leave requests table
    if "leave_requests" not in existing_tables:
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS leave_requests (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id INTEGER NOT NULL,
                    leave_type_id INTEGER NOT NULL,
                    start_date TEXT NOT NULL,
                    end_date TEXT NOT NULL,
                    days_requested REAL NOT NULL,
                    reason TEXT NOT NULL,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (employee_id) REFERENCES employees(id),
                    FOREIGN KEY (leave_type_id) REFERENCES leave_type_configs(id)
                )
            """)
            created_tables.append("leave_requests")
            print("✅ Created 'leave_requests' table")
        except Exception as e:
            print(f"❌ Error creating leave_requests table: {e}")

    # Leave type configs table
    if "leave_type_configs" not in existing_tables:
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS leave_type_configs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT UNIQUE NOT NULL,
                    display_name TEXT NOT NULL,
                    max_days_per_year INTEGER DEFAULT 0,
                    is_paid INTEGER DEFAULT 1,
                    color TEXT DEFAULT '#2E86AB'
                )
            """)
            created_tables.append("leave_type_configs")
            print("✅ Created 'leave_type_configs' table")

            # Insert default leave types
            cursor.executemany(
                "INSERT OR IGNORE INTO leave_type_configs (name, display_name, max_days_per_year, is_paid, color) VALUES (?, ?, ?, ?, ?)",
                [
                    ("annual", "Annual Leave", 20, 1, "#4CAF50"),
                    ("sick", "Sick Leave", 10, 1, "#F44336"),
                    ("personal", "Personal Leave", 5, 1, "#FF9800"),
                    ("maternity", "Maternity Leave", 90, 1, "#E91E63"),
                    ("paternity", "Paternity Leave", 14, 1, "#2196F3"),
                    ("bereavement", "Bereavement Leave", 5, 1, "#9C27B0"),
                    ("unpaid", "Unpaid Leave", 0, 0, "#607D8B"),
                ]
            )
            print("✅ Inserted default leave types")
        except Exception as e:
            print(f"❌ Error creating leave_type_configs table: {e}")

    # Leave balances table
    if "leave_balances" not in existing_tables:
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS leave_balances (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    employee_id INTEGER NOT NULL,
                    leave_type_id INTEGER NOT NULL,
                    year INTEGER NOT NULL,
                    total_days REAL DEFAULT 0,
                    used_days REAL DEFAULT 0,
                    FOREIGN KEY (employee_id) REFERENCES employees(id),
                    FOREIGN KEY (leave_type_id) REFERENCES leave_type_configs(id)
                )
            """)
            created_tables.append("leave_balances")
            print("✅ Created 'leave_balances' table")
        except Exception as e:
            print(f"❌ Error creating leave_balances table: {e}")

    # Chat messages table
    if "chat_messages" not in existing_tables:
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender_id INTEGER NOT NULL,
                    group_id INTEGER,
                    receiver_id INTEGER,
                    content TEXT NOT NULL,
                    message_type TEXT DEFAULT 'text',
                    is_read INTEGER DEFAULT 0,
                    has_attachment INTEGER DEFAULT 0,
                    attachment_path TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (sender_id) REFERENCES users(id),
                    FOREIGN KEY (group_id) REFERENCES chat_groups(id),
                    FOREIGN KEY (receiver_id) REFERENCES users(id)
                )
            """)
            created_tables.append("chat_messages")
            print("✅ Created 'chat_messages' table")
        except Exception as e:
            print(f"❌ Error creating chat_messages table: {e}")

    # Messages table (direct messages)
    if "messages" not in existing_tables:
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender_id INTEGER NOT NULL,
                    receiver_id INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    is_read INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (sender_id) REFERENCES employees(id),
                    FOREIGN KEY (receiver_id) REFERENCES employees(id)
                )
            """)
            created_tables.append("messages")
            print("✅ Created 'messages' table")
        except Exception as e:
            print(f"❌ Error creating messages table: {e}")

    # Chat groups table
    if "chat_groups" not in existing_tables:
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_by INTEGER NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (created_by) REFERENCES users(id)
                )
            """)
            created_tables.append("chat_groups")
            print("✅ Created 'chat_groups' table")
        except Exception as e:
            print(f"❌ Error creating chat_groups table: {e}")

    # Chat group members table
    if "chat_group_members" not in existing_tables:
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_group_members (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    role TEXT DEFAULT 'member',
                    joined_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (group_id) REFERENCES chat_groups(id),
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            created_tables.append("chat_group_members")
            print("✅ Created 'chat_group_members' table")
        except Exception as e:
            print(f"❌ Error creating chat_group_members table: {e}")

    # Tasks table
    if "tasks" not in existing_tables:
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    assigned_to_id INTEGER NOT NULL,
                    created_by_id INTEGER NOT NULL,
                    status TEXT DEFAULT 'todo',
                    priority TEXT DEFAULT 'medium',
                    due_date TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (assigned_to_id) REFERENCES employees(id),
                    FOREIGN KEY (created_by_id) REFERENCES employees(id)
                )
            """)
            created_tables.append("tasks")
            print("✅ Created 'tasks' table")
        except Exception as e:
            print(f"❌ Error creating tasks table: {e}")

    # Task comments table
    if "task_comments" not in existing_tables:
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS task_comments (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    task_id INTEGER NOT NULL,
                    employee_id INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (task_id) REFERENCES tasks(id),
                    FOREIGN KEY (employee_id) REFERENCES employees(id)
                )
            """)
            created_tables.append("task_comments")
            print("✅ Created 'task_comments' table")
        except Exception as e:
            print(f"❌ Error creating task_comments table: {e}")

    # Screen Access table (NEW)
    if "screen_access" not in existing_tables:
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS screen_access (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    screen_key TEXT NOT NULL,
                    is_enabled INTEGER DEFAULT 1,
                    granted_by INTEGER,
                    granted_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (granted_by) REFERENCES users(id)
                )
            """)
            created_tables.append("screen_access")
            print("✅ Created 'screen_access' table")
        except Exception as e:
            print(f"❌ Error creating screen_access table: {e}")

    # ETL Jobs table
    if "etl_jobs" not in existing_tables:
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS etl_jobs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    job_name TEXT NOT NULL,
                    job_type TEXT NOT NULL,
                    source_table TEXT,
                    target_table TEXT,
                    source_file TEXT,
                    status TEXT DEFAULT 'pending',
                    total_rows INTEGER DEFAULT 0,
                    processed_rows INTEGER DEFAULT 0,
                    success_rows INTEGER DEFAULT 0,
                    failed_rows INTEGER DEFAULT 0,
                    error_log TEXT,
                    column_mapping TEXT,
                    created_by_id INTEGER,
                    started_at TEXT,
                    completed_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (created_by_id) REFERENCES users(id)
                )
            """)
            created_tables.append("etl_jobs")
            print("✅ Created 'etl_jobs' table")
        except Exception as e:
            print(f"❌ Error creating etl_jobs table: {e}")

    # Data Import Logs table
    if "data_import_logs" not in existing_tables:
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS data_import_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    etl_job_id INTEGER NOT NULL,
                    row_number INTEGER NOT NULL,
                    status TEXT DEFAULT 'success',
                    error_message TEXT,
                    data_hash TEXT,
                    imported_data TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (etl_job_id) REFERENCES etl_jobs(id)
                )
            """)
            created_tables.append("data_import_logs")
            print("✅ Created 'data_import_logs' table")
        except Exception as e:
            print(f"❌ Error creating data_import_logs table: {e}")

    # Power BI Refresh Logs table
    if "powerbi_refresh_logs" not in existing_tables:
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS powerbi_refresh_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    dataset_id TEXT NOT NULL,
                    dataset_name TEXT NOT NULL,
                    workspace_id TEXT,
                    status TEXT DEFAULT 'pending',
                    triggered_by_id INTEGER,
                    refresh_type TEXT DEFAULT 'full',
                    error_message TEXT,
                    started_at TEXT,
                    completed_at TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (triggered_by_id) REFERENCES users(id)
                )
            """)
            created_tables.append("powerbi_refresh_logs")
            print("✅ Created 'powerbi_refresh_logs' table")
        except Exception as e:
            print(f"❌ Error creating powerbi_refresh_logs table: {e}")

    # Excel Templates table
    if "excel_templates" not in existing_tables:
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS excel_templates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    target_table TEXT NOT NULL,
                    column_mappings TEXT NOT NULL,
                    required_columns TEXT,
                    sample_file_path TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_by_id INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (created_by_id) REFERENCES users(id)
                )
            """)
            created_tables.append("excel_templates")
            print("✅ Created 'excel_templates' table")
        except Exception as e:
            print(f"❌ Error creating excel_templates table: {e}")

    conn.commit()

    # Verify tables
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    final_tables = [row[0] for row in cursor.fetchall()]
    print(f"\n📊 Final tables: {final_tables}")

    conn.close()

    if created_tables:
        print(
            f"\n✅ Migration completed! Created {len(created_tables)} tables: {created_tables}")
        return True
    else:
        print("\n✅ No new tables needed - all required tables already exist")
        return True


if __name__ == "__main__":
    try:
        print("🔄 Running database migration...")
        run_migration()
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        sys.exit(1)
