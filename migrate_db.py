"""
Database Migration Runner
This script now delegates table creation to SQLAlchemy model metadata.
It is safer and ensures the database schema matches the application's
ORM models in `database.models`.
"""

from database.connection import init_db, get_db_info


def run_migration():
    print("Initializing database from model metadata...")
    init_db()
    info = get_db_info()
    print(
        f"Database initialized using dialect: {info.get('dialect')}, url: {str(info.get('url'))}")


if __name__ == '__main__':
    run_migration()
                    year INTEGER NOT NULL,
                    total_days REAL DEFAULT 0,
                    used_days REAL DEFAULT 0,
                    FOREIGN KEY(employee_id) REFERENCES employees(id),
                    FOREIGN KEY(leave_type_id) REFERENCES leave_type_configs(id)
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
