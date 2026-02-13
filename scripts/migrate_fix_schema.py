"""
Vernika HRA - Database Migration Script
Fixes missing columns and schema issues
"""

import sqlite3
import os


def migrate_database():
    """Run database migrations to fix schema issues"""
    db_path = 'vernika.db'

    if not os.path.exists(db_path):
        print(f"Database {db_path} not found. Creating new database...")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    migrations_applied = []

    # 1. Check and add missing columns to departments table
    print("\n=== Checking departments table ===")
    cursor.execute("PRAGMA table_info(departments)")
    dept_columns = {row[1] for row in cursor.fetchall()}

    missing_dept_cols = {
        'budget': 'REAL DEFAULT 0',
        'location': 'TEXT',
        'contact_email': 'TEXT',
        'contact_phone': 'TEXT',
        'parent_dept_id': 'INTEGER REFERENCES departments(id)'
    }

    for col_name, col_type in missing_dept_cols.items():
        if col_name not in dept_columns:
            try:
                cursor.execute(
                    f"ALTER TABLE departments ADD COLUMN {col_name} {col_type}")
                migrations_applied(f"Added column {col_name} to departments")
                print(f"  ✓ Added column: {col_name}")
            except sqlite3.Error as e:
                print(f"  ✗ Error adding {col_name}: {e}")

    # 2. Check and add missing columns to tasks table
    print("\n=== Checking tasks table ===")
    cursor.execute("PRAGMA table_info(tasks)")
    task_columns = {row[1] for row in cursor.fetchall()}

    missing_task_cols = {
        'task_type': 'TEXT DEFAULT "feature"',
        'category': 'TEXT',
        'project_name': 'TEXT',
        'estimated_hours': 'REAL DEFAULT 0',
        'actual_hours': 'REAL DEFAULT 0',
        'start_date': 'DATE'
    }

    for col_name, col_type in missing_task_cols.items():
        if col_name not in task_columns:
            try:
                cursor.execute(
                    f"ALTER TABLE tasks ADD COLUMN {col_name} {col_type}")
                migrations_applied.append(f"Added column {col_name} to tasks")
                print(f"  ✓ Added column: {col_name}")
            except sqlite3.Error as e:
                print(f"  ✗ Error adding {col_name}: {e}")

    # 3. Ensure screen_access table exists
    print("\n=== Checking screen_access table ===")
    cursor.execute("""
        SELECT name FROM sqlite_master WHERE type='table' AND name='screen_access'
    """)
    if not cursor.fetchone():
        cursor.execute("""
            CREATE TABLE screen_access (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                screen_key TEXT NOT NULL,
                is_enabled INTEGER DEFAULT 1,
                granted_by INTEGER REFERENCES users(id),
                granted_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, screen_key)
            )
        """)
        migrations_applied.append("Created screen_access table")
        print("  ✓ Created screen_access table")

        # Initialize default access for existing users
        cursor.execute("""
            INSERT INTO screen_access (user_id, screen_key, is_enabled)
            SELECT u.id, 'profile', 1 FROM users u
            WHERE NOT EXISTS (
                SELECT 1 FROM screen_access WHERE user_id = u.id AND screen_key = 'profile'
            )
        """)
        print("  ✓ Initialized default screen access")
    else:
        print("  ✓ screen_access table already exists")

    # 4. Create index for better performance
    print("\n=== Creating indexes ===")
    try:
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_employees_user_id ON employees(user_id)")
        print("  ✓ Created index: idx_employees_user_id")
    except sqlite3.Error as e:
        print(f"  Note: {e}")

    try:
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_attendances_employee_date ON attendances(employee_id, date)")
        print("  ✓ Created index: idx_attendances_employee_date")
    except sqlite3.Error as e:
        print(f"  Note: {e}")

    try:
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_tasks_assigned ON tasks(assigned_to_id)")
        print("  ✓ Created index: idx_tasks_assigned")
    except sqlite3.Error as e:
        print(f"  Note: {e}")

    conn.commit()
    conn.close()

    print("\n=== Migration Complete ===")
    if migrations_applied:
        print("Applied migrations:")
        for m in migrations_applied:
            print(f"  - {m}")
    else:
        print("No new migrations needed. Database is up to date.")


if __name__ == "__main__":
    migrate_database()
