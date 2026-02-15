"""
Database migrations using SQLAlchemy engine/inspector.

This script creates/updates schema items previously done with a direct
SQLite connection. It uses the central `database.connection.get_engine`
to operate safely against SQLite or PostgreSQL (Supabase).
"""

from datetime import datetime
from sqlalchemy import text, inspect
from database.connection import get_engine


def run_migrations():
    engine = get_engine()
    inspector = inspect(engine)

    # ========== Create Announcements Table ==========
    print("\nCreating announcements table...")

    tables = inspector.get_table_names()
    if 'announcements' not in tables:
        create_sql = """
        CREATE TABLE announcements (
            id SERIAL PRIMARY KEY,
            title VARCHAR(200) NOT NULL,
            content TEXT NOT NULL,
            type VARCHAR(50) DEFAULT 'general',
            priority VARCHAR(20) DEFAULT 'normal',
            author VARCHAR(100) DEFAULT 'Admin',
            created_at DATE DEFAULT CURRENT_DATE,
            views INTEGER DEFAULT 0
        )
        """
        # Use IF NOT EXISTS in dialects that support it
        try:
            with engine.begin() as conn:
                conn.execute(text(create_sql))
            print("  ✅ Created announcements table")
        except Exception:
            # Fallback using IF NOT EXISTS for SQLite/Postgres
            with engine.begin() as conn:
                conn.execute(text("CREATE TABLE IF NOT EXISTS announcements (\n"
                                  "id INTEGER PRIMARY KEY AUTOINCREMENT,\n"
                                  "title VARCHAR(200) NOT NULL,\n"
                                  "content TEXT NOT NULL,\n"
                                  "type VARCHAR(50) DEFAULT 'general',\n"
                                  "priority VARCHAR(20) DEFAULT 'normal',\n"
                                  "author VARCHAR(100) DEFAULT 'Admin',\n"
                                  "created_at DATE DEFAULT CURRENT_DATE,\n"
                                  "views INTEGER DEFAULT 0\n)"))
            print("  ✅ Created announcements table (fallback)")

        # Insert sample announcements
        sample_announcements = [
            ("Office Closure - Holiday Notice",
             "The office will be closed on Friday for a company-wide holiday.",
             "important", "high", "Admin"),
            ("New Health Insurance Plan",
             "We are pleased to announce an improved health insurance plan.",
             "policy", "important", "HR Manager"),
            ("Welcome to New Team Members",
             "Let's welcome our new team members joining this month!",
             "general", "normal", "HR Manager"),
        ]

        with engine.begin() as conn:
            for title, content, type_, priority, author in sample_announcements:
                conn.execute(
                    text("INSERT INTO announcements (title, content, type, priority, author, created_at, views)"
                         " VALUES (:title, :content, :type, :priority, :author, :created_at, 0)"),
                    {
                        'title': title,
                        'content': content,
                        'type': type_,
                        'priority': priority,
                        'author': author,
                        'created_at': datetime.now().strftime('%Y-%m-%d')
                    }
                )

        print("  ✅ Added sample announcements")
    else:
        print("  ⚠️  announcements table already exists")

    # ========== Department Table Updates ==========
    print("\nUpdating departments table...")

    cols = {c['name'] for c in inspector.get_columns(
        'departments')} if 'departments' in inspector.get_table_names() else set()

    new_dept_cols = [
        ("head_id", "INTEGER"),
        ("budget", "DECIMAL(12,2) DEFAULT 0"),
        ("location", "VARCHAR(200)"),
        ("contact_email", "VARCHAR(100)"),
        ("contact_phone", "VARCHAR(20)"),
        ("parent_dept_id", "INTEGER"),
    ]

    with engine.begin() as conn:
        for col_name, col_type in new_dept_cols:
            if col_name not in cols:
                try:
                    conn.execute(
                        text(f"ALTER TABLE departments ADD COLUMN {col_name} {col_type}"))
                    print(f"  ✅ Added column: {col_name}")
                except Exception as e:
                    print(
                        f"  ⚠️  Column {col_name} could not be added or already exists: {e}")

    # ========== Tasks Table Updates ==========
    print("\nUpdating tasks table...")
    cols = {c['name'] for c in inspector.get_columns(
        'tasks')} if 'tasks' in inspector.get_table_names() else set()

    new_task_cols = [
        ("category", "VARCHAR(50)"),
        ("project_name", "VARCHAR(200)"),
        ("estimated_hours", "DECIMAL(5,2) DEFAULT 0"),
        ("actual_hours", "DECIMAL(5,2) DEFAULT 0"),
        ("start_date", "DATE"),
        ("end_date", "DATE"),
        ("task_type", "VARCHAR(50) DEFAULT 'feature'"),
        ("attachments", "TEXT"),
        ("time_spent", "DECIMAL(5,2) DEFAULT 0"),
    ]

    with engine.begin() as conn:
        for col_name, col_type in new_task_cols:
            if col_name not in cols:
                try:
                    conn.execute(
                        text(f"ALTER TABLE tasks ADD COLUMN {col_name} {col_type}"))
                    print(f"  ✅ Added column: {col_name}")
                except Exception as e:
                    print(
                        f"  ⚠️  Column {col_name} could not be added or already exists: {e}")

    # ========== Create Task Comments Table ==========
    print("\nCreating task_comments table...")
    if 'task_comments' not in inspector.get_table_names():
        create_comments = """
        CREATE TABLE task_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            employee_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
        try:
            with engine.begin() as conn:
                conn.execute(text(create_comments))
            print("  ✅ Created task_comments table")
        except Exception as e:
            print(f"  ⚠️  Could not create task_comments: {e}")
    else:
        print("  ⚠️  task_comments table already exists")

    print("\n✅ All migrations completed successfully!")


if __name__ == "__main__":
    run_migrations()
