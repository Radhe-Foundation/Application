"""
Migration fixer using SQLAlchemy engine
"""

from sqlalchemy import inspect, text
from database.connection import get_engine


def migrate_database():
    engine = get_engine()
    inspector = inspect(engine)

    existing_tables = inspector.get_table_names()
    migrations_applied = []

    # 1. Check and add missing columns to departments table
    print("\n=== Checking departments table ===")
    if 'departments' in existing_tables:
        dept_cols = {c['name'] for c in inspector.get_columns('departments')}
        missing_dept_cols = {
            'budget': 'REAL DEFAULT 0',
            'location': 'TEXT',
            'contact_email': 'TEXT',
            'contact_phone': 'TEXT',
            'parent_dept_id': 'INTEGER'
        }
        with engine.begin() as conn:
            for col_name, col_type in missing_dept_cols.items():
                if col_name not in dept_cols:
                    try:
                        conn.execute(
                            text(f"ALTER TABLE departments ADD COLUMN {col_name} {col_type}"))
                        migrations_applied.append(
                            f"Added column {col_name} to departments")
                        print(f"  ✓ Added column: {col_name}")
                    except Exception as e:
                        print(f"  ✗ Error adding {col_name}: {e}")
    else:
        print("  ✗ departments table not found; skipping")

    # 2. Check and add missing columns to tasks table
    print("\n=== Checking tasks table ===")
    if 'tasks' in existing_tables:
        task_cols = {c['name'] for c in inspector.get_columns('tasks')}
        missing_task_cols = {
            'task_type': "TEXT DEFAULT 'feature'",
            'category': 'TEXT',
            'project_name': 'TEXT',
            'estimated_hours': 'REAL DEFAULT 0',
            'actual_hours': 'REAL DEFAULT 0',
            'start_date': 'DATE'
        }
        with engine.begin() as conn:
            for col_name, col_type in missing_task_cols.items():
                if col_name not in task_cols:
                    try:
                        conn.execute(
                            text(f"ALTER TABLE tasks ADD COLUMN {col_name} {col_type}"))
                        migrations_applied.append(
                            f"Added column {col_name} to tasks")
                        print(f"  ✓ Added column: {col_name}")
                    except Exception as e:
                        print(f"  ✗ Error adding {col_name}: {e}")
    else:
        print("  ✗ tasks table not found; skipping")

    # 3. Ensure screen_access table exists
    print("\n=== Checking screen_access table ===")
    if 'screen_access' not in existing_tables:
        with engine.begin() as conn:
            conn.execute(text("""
                CREATE TABLE screen_access (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    screen_key VARCHAR(100) NOT NULL,
                    is_enabled BOOLEAN DEFAULT TRUE,
                    granted_by INTEGER,
                    granted_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, screen_key)
                )
            """))
        migrations_applied.append("Created screen_access table")
        print("  ✓ Created screen_access table")
        # Initialize default access for existing users
        with engine.begin() as conn:
            conn.execute(text("""
                INSERT INTO screen_access (user_id, screen_key, is_enabled)
                SELECT u.id, 'profile', TRUE FROM users u
                WHERE NOT EXISTS (
                    SELECT 1 FROM screen_access WHERE user_id = u.id AND screen_key = 'profile'
                )
            """))
            print("  ✓ Initialized default screen access")
    else:
        print("  ✓ screen_access table already exists")

    # 4. Create indexes for better performance (if supported)
    print("\n=== Creating indexes ===")
    with engine.begin() as conn:
        try:
            conn.execute(
                text("CREATE INDEX IF NOT EXISTS idx_employees_user_id ON employees(user_id)"))
            print("  ✓ Created index: idx_employees_user_id")
        except Exception as e:
            print(f"  Note: {e}")

        try:
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_attendances_employee_date ON attendances(employee_id, date)"))
            print("  ✓ Created index: idx_attendances_employee_date")
        except Exception as e:
            print(f"  Note: {e}")

        try:
            conn.execute(
                text("CREATE INDEX IF NOT EXISTS idx_tasks_assigned ON tasks(assigned_to_id)"))
            print("  ✓ Created index: idx_tasks_assigned")
        except Exception as e:
            print(f"  Note: {e}")

    print("\n=== Migration Complete ===")
    if migrations_applied:
        print("Applied migrations:")
        for m in migrations_applied:
            print(f"  - {m}")
    else:
        print("No new migrations needed. Database is up to date.")


if __name__ == "__main__":
    migrate_database()
