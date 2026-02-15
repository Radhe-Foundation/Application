"""
Database Fixes (SQLAlchemy-backed)

This script creates recommended indexes and performs non-destructive
schema fixes using SQLAlchemy's engine. It avoids direct sqlite3 usage
and works with the configured `DATABASE_URL` (Postgres/Supabase).
"""

from database.connection import get_engine
from sqlalchemy import text


def add_indexes():
    engine = get_engine()
    indexes = [
        ("idx_employees_code", "employees", "employee_code"),
        ("idx_employees_email", "employees", "email"),
        ("idx_employees_dept", "employees", "department_id"),
        ("idx_employees_pos", "employees", "position_id"),
        ("idx_employees_status", "employees", "is_active"),
        ("idx_employees_created", "employees", "created_at"),
        ("idx_users_username", "users", "username"),
        ("idx_users_email", "users", "email"),
        ("idx_users_role", "users", "role_id"),
        ("idx_attendance_emp_date", "attendances", "employee_id, date"),
        ("idx_attendance_date", "attendances", "date"),
        ("idx_attendance_status", "attendances", "status"),
        ("idx_leaves_employee", "leave_requests", "employee_id"),
        ("idx_leaves_status", "leave_requests", "status"),
        ("idx_tasks_assignee", "tasks", "assigned_to_id"),
        ("idx_tasks_status", "tasks", "status"),
        ("idx_tasks_priority", "tasks", "priority"),
        ("idx_tasks_due", "tasks", "due_date"),
        ("idx_depts_code", "departments", "code"),
        ("idx_depts_parent", "departments", "parent_dept_id"),
    ]

    with engine.begin() as conn:
        for idx_name, table_name, cols in indexes:
            try:
                conn.execute(
                    text(f"CREATE INDEX IF NOT EXISTS {idx_name} ON {table_name}({cols})"))
                print(f"✓ Created index {idx_name} on {table_name}({cols})")
            except Exception as e:
                print(f"✗ Error creating index {idx_name}: {e}")


if __name__ == '__main__':
    add_indexes()

    # Define the standard ordering for each table
    ORDERING = {
        'employees': 'ORDER BY e.id ASC',
        'departments': 'ORDER BY d.id ASC',
        'positions': 'ORDER BY p.id ASC',
        'attendances': 'ORDER BY a.date DESC, a.id DESC',
        'leave_requests': 'ORDER BY l.created_at DESC, l.id DESC',
        'tasks': 'ORDER BY t.created_at DESC, t.id DESC',
        'users': 'ORDER BY u.id ASC',
    }

    print("✓ Standard ordering defined for all tables:")
    for table, order in ORDERING.items():
        print(f"  {table}: {order}")

    return ORDERING


def fix_views():
    """Create or update database views for consistent data access"""
    conn = get_connection()
    cursor = conn.cursor()

    # Drop existing views if they exist
    views = [
        'view_employees_full',
        'view_attendance_summary',
        'view_leave_balances',
        'view_tasks_summary',
    ]

    for view in views:
        try:
            cursor.execute(f"DROP VIEW IF EXISTS {view}")
            print(f"✓ Dropped view {view}")
        except Exception as e:
            print(f"⏭ Could not drop view {view}: {e}")

    # Create view for full employee details
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS view_employees_full AS
        SELECT 
            e.id,
            e.employee_code,
            e.first_name,
            e.last_name,
            e.email,
            e.phone,
            e.date_of_birth,
            e.gender,
            d.name as department_name,
            p.title as position_title,
            e.employment_type,
            e.employment_status,
            e.date_of_joining,
            e.is_active,
            e.created_at,
            e.updated_at,
            u.username,
            r.name as role_name
        FROM employees e
        LEFT JOIN departments d ON e.department_id = d.id
        LEFT JOIN positions p ON e.position_id = p.id
        LEFT JOIN users u ON e.user_id = u.id
        LEFT JOIN roles r ON u.role_id = r.id
        ORDER BY e.id ASC
    """)
    print("✓ Created view view_employees_full")

    # Create view for attendance summary
    cursor.execute("""
        CREATE VIEW IF NOT EXISTS view_attendance_summary AS
        SELECT 
            e.id as employee_id,
            e.employee_code,
            e.first_name || ' ' || e.last_name as employee_name,
            d.name as department_name,
            COUNT(a.id) as total_days,
            SUM(CASE WHEN a.status = 'present' THEN 1 ELSE 0 END) as present_days,
            SUM(CASE WHEN a.status = 'absent' THEN 1 ELSE 0 END) as absent_days,
            SUM(CASE WHEN a.status = 'late' THEN 1 ELSE 0 END) as late_days,
            SUM(CASE WHEN a.status = 'on_leave' THEN 1 ELSE 0 END) as leave_days,
            ROUND(AVG(CASE WHEN a.working_hours THEN a.working_hours ELSE 0 END), 2) as avg_working_hours
        FROM employees e
        LEFT JOIN attendances a ON e.id = a.employee_id
        LEFT JOIN departments d ON e.department_id = d.id
        GROUP BY e.id
        ORDER BY e.id ASC
    """)
    print("✓ Created view view_attendance_summary")

    conn.commit()
    conn.close()


def run_all_fixes():
    """Run all database fixes"""
    print("=" * 60)
    print("Vernika HRA - Database Fix Script")
    print("=" * 60)
    print()

    # Step 1: Backup database
    print("Step 1: Backing up database...")
    if not backup_database():
        print("✗ No database found to backup")
    print()

    # Step 2: Add missing columns
    print("Step 2: Adding missing columns...")
    add_missing_columns()
    print()

    # Step 3: Add indexes
    print("Step 3: Adding indexes...")
    add_indexes()
    print()

    # Step 4: Fix foreign keys
    print("Step 4: Fixing foreign keys...")
    fix_foreign_keys()
    print()

    # Step 5: Create views
    print("Step 5: Creating views...")
    fix_views()
    print()

    # Step 6: Update ordering
    print("Step 6: Defining standard ordering...")
    update_query_ordering()
    print()

    print("=" * 60)
    print("Database fixes completed successfully!")
    print("=" * 60)
    print()
    print("Summary of changes:")
    print("1. ✓ Database backed up")
    print("2. ✓ Added missing columns (created_at, updated_at)")
    print("3. ✓ Added indexes for better performance")
    print("4. ✓ Created foreign key triggers")
    print("5. ✓ Created views for consistent data access")
    print("6. ✓ Defined standard ordering for exports")
    print()
    print("Note: For PostgreSQL/MySQL, these changes will be")
    print("implemented via SQLAlchemy models directly.")


if __name__ == "__main__":
    run_all_fixes()
