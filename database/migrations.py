"""
Database Migration Script - Add new columns for enhanced screens
"""

import sqlite3


def run_migrations():
    """Run all database migrations"""
    conn = sqlite3.connect('vernika.db')
    cursor = conn.cursor()

    # ========== Create Announcements Table ==========
    print("\nCreating announcements table...")

    cursor.execute(
        """SELECT name FROM sqlite_master WHERE type='table' AND name='announcements'""")
    if not cursor.fetchone():
        cursor.execute("""
            CREATE TABLE announcements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title VARCHAR(200) NOT NULL,
                content TEXT NOT NULL,
                type VARCHAR(50) DEFAULT 'general',
                priority VARCHAR(20) DEFAULT 'normal',
                author VARCHAR(100) DEFAULT 'Admin',
                created_at DATE DEFAULT CURRENT_DATE,
                views INTEGER DEFAULT 0
            )
        """)
        print("  ✅ Created announcements table")

        # Insert sample announcements
        from datetime import datetime
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

        for title, content, type_, priority, author in sample_announcements:
            cursor.execute("""
                INSERT INTO announcements (title, content, type, priority, author, created_at, views)
                VALUES (?, ?, ?, ?, ?, ?, 0)
            """, (title, content, type_, priority, author, datetime.now().strftime('%Y-%m-%d')))

        print("  ✅ Added sample announcements")
    else:
        print("  ⚠️  announcements table already exists")

    # ========== Department Table Updates ==========
    print("\nUpdating departments table...")

    # Get existing columns
    cursor.execute("PRAGMA table_info(departments)")
    existing_cols = [row[1] for row in cursor.fetchall()]

    # Add columns if they don't exist
    new_dept_cols = [
        ("head_id", "INTEGER"),
        ("budget", "DECIMAL(12,2) DEFAULT 0"),
        ("location", "VARCHAR(200)"),
        ("contact_email", "VARCHAR(100)"),
        ("contact_phone", "VARCHAR(20)"),
        ("parent_dept_id", "INTEGER"),
    ]

    for col_name, col_type in new_dept_cols:
        if col_name not in existing_cols:
            try:
                cursor.execute(
                    f"ALTER TABLE departments ADD COLUMN {col_name} {col_type}")
                print(f"  ✅ Added column: {col_name}")
            except Exception as e:
                print(f"  ⚠️  Column {col_name} already exists or error: {e}")

    # ========== Tasks Table Updates ==========
    print("\nUpdating tasks table...")

    cursor.execute("PRAGMA table_info(tasks)")
    existing_cols = [row[1] for row in cursor.fetchall()]

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

    for col_name, col_type in new_task_cols:
        if col_name not in existing_cols:
            try:
                cursor.execute(
                    f"ALTER TABLE tasks ADD COLUMN {col_name} {col_type}")
                print(f"  ✅ Added column: {col_name}")
            except Exception as e:
                print(f"  ⚠️  Column {col_name} already exists or error: {e}")

    # ========== Create Task Comments Table ==========
    print("\nCreating task_comments table...")

    cursor.execute(
        """SELECT name FROM sqlite_master WHERE type='table' AND name='task_comments'""")
    if not cursor.fetchone():
        cursor.execute("""
            CREATE TABLE task_comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                employee_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks(id),
                FOREIGN KEY (employee_id) REFERENCES employees(id)
            )
        """)
        print("  ✅ Created task_comments table")
    else:
        print("  ⚠️  task_comments table already exists")

    conn.commit()
    conn.close()
    print("\n✅ All migrations completed successfully!")


if __name__ == "__main__":
    run_migrations()
