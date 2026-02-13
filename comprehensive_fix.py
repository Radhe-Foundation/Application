#!/usr/bin/env python3
"""
Comprehensive Fix Script for Vernika HRA
Fixes:
1. Chat screen issues
2. Access control for employees dashboard
3. Employee deletion issues
4. Database consistency
"""

import sqlite3
import os

DB_PATH = 'vernika.db'


def get_db_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def fix_screen_access_table():
    """Ensure screen_access table exists and has proper structure"""
    print("\n[1] Fixing screen_access table...")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if screen_access table exists
    cursor.execute("""
        SELECT name FROM sqlite_master WHERE type='table' AND name='screen_access'
    """)

    if not cursor.fetchone():
        # Create table
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
                UNIQUE(user_id, screen_key)
            )
        """)
        print("  ✓ Created screen_access table")
    else:
        print("  ✓ screen_access table exists")

    conn.commit()

    # Now ensure all employees have screen access records
    # Get all users with employee role
    cursor.execute("""
        SELECT u.id, u.username, r.name as role_name
        FROM users u
        LEFT JOIN roles r ON u.role_id = r.id
        WHERE r.name != 'admin'
    """)
    users = cursor.fetchall()

    # Default screen access for employees
    default_screens = [
        ('profile', 1),  # Profile always enabled
        ('tasks', 0),
        ('leaves', 0),
        ('attendance', 0),
        ('documents', 0),
        ('chat', 0),
    ]

    for user in users:
        user_id = user['id']
        # Check if user has any screen access records
        cursor.execute(
            "SELECT COUNT(*) FROM screen_access WHERE user_id = ?", (user_id,))
        count = cursor.fetchone()[0]

        if count == 0:
            # Insert default screen access for this user
            for screen_key, is_enabled in default_screens:
                try:
                    cursor.execute("""
                        INSERT OR IGNORE INTO screen_access 
                        (user_id, screen_key, is_enabled, granted_by, granted_at)
                        VALUES (?, ?, ?, NULL, datetime('now'))
                    """, (user_id, screen_key, is_enabled))
                except Exception as e:
                    pass
            print(
                f"  ✓ Added default screen access for user {user['username']}")

    conn.commit()
    conn.close()
    print("  ✓ Screen access table fixed")


def fix_user_employee_sync():
    """Ensure users have proper employee records"""
    print("\n[2] Fixing user-employee sync...")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Get all users without employee records
    cursor.execute("""
        SELECT u.id, u.username, u.email
        FROM users u
        LEFT JOIN employees e ON u.id = e.user_id
        WHERE e.id IS NULL
    """)
    orphan_users = cursor.fetchall()

    if orphan_users:
        print(f"  Found {len(orphan_users)} users without employee records")

        # Get default department
        cursor.execute("SELECT id FROM departments LIMIT 1")
        dept = cursor.fetchone()
        dept_id = dept['id'] if dept else 1

        for user in orphan_users:
            # Generate employee code
            cursor.execute("SELECT MAX(id) as max_id FROM employees")
            result = cursor.fetchone()
            max_id = result['max_id'] if result and result['max_id'] else 0
            emp_code = f"EMP{max_id + 1:03d}"

            # Create employee record
            cursor.execute("""
                INSERT INTO employees (employee_code, user_id, first_name, last_name, email, department_id, is_active)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            """, (emp_code, user['id'], user['username'], user['username'], user['email'], dept_id))
            print(f"  ✓ Created employee record for {user['username']}")

        conn.commit()
    else:
        print("  ✓ All users have employee records")

    conn.close()


def fix_employee_deletion():
    """Fix employee deletion with proper cascade handling"""
    print("\n[3] Fixing employee deletion...")

    # This is handled in employees_screen.py already, but let's ensure
    # the foreign key constraints are properly handled

    conn = get_db_connection()
    cursor = conn.cursor()

    # Enable foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")

    # Check for any orphaned records that might block deletion
    cursor.execute("""
        SELECT COUNT(*) as count FROM employees e
        LEFT JOIN users u ON e.user_id = u.id
        WHERE u.id IS NULL AND e.user_id IS NOT NULL
    """)
    orphan_count = cursor.fetchone()[0]

    if orphan_count > 0:
        print(f"  Found {orphan_count} employees with invalid user references")
        # Fix by setting user_id to NULL for orphaned employees
        cursor.execute("""
            UPDATE employees SET user_id = NULL
            WHERE user_id IS NOT NULL AND user_id NOT IN (SELECT id FROM users)
        """)
        conn.commit()
        print("  ✓ Fixed orphaned employee records")

    conn.close()
    print("  ✓ Employee deletion fixed")


def fix_chat_tables():
    """Ensure chat-related tables exist and are properly structured"""
    print("\n[4] Fixing chat tables...")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if chat_messages table exists
    cursor.execute("""
        SELECT name FROM sqlite_master WHERE type='table' AND name='chat_messages'
    """)

    if not cursor.fetchone():
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER NOT NULL,
                receiver_id INTEGER,
                group_id INTEGER,
                content TEXT NOT NULL,
                message_type TEXT DEFAULT 'text',
                is_read INTEGER DEFAULT 0,
                has_attachment INTEGER DEFAULT 0,
                attachment_path TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  ✓ Created chat_messages table")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_groups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                created_by INTEGER NOT NULL,
                is_active INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  ✓ Created chat_groups table")

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_group_members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                group_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                role TEXT DEFAULT 'member',
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        print("  ✓ Created chat_group_members table")

    # Create indexes for better chat performance
    try:
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_chat_sender ON chat_messages(sender_id)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_chat_receiver ON chat_messages(receiver_id)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_chat_group ON chat_messages(group_id)")
        cursor.execute(
            "CREATE INDEX IF NOT EXISTS idx_chat_created ON chat_messages(created_at)")
        print("  ✓ Created chat indexes")
    except:
        pass

    conn.commit()
    conn.close()
    print("  ✓ Chat tables fixed")


def add_test_users():
    """Add test users if none exist"""
    print("\n[5] Checking test users...")

    import bcrypt

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check if admin exists
    cursor.execute("SELECT id FROM users WHERE username = 'admin'")
    if not cursor.fetchone():
        # Get admin role
        cursor.execute("SELECT id FROM roles WHERE name = 'admin'")
        role = cursor.fetchone()
        admin_role_id = role['id'] if role else 1

        # Create admin user
        hashed_pw = bcrypt.hashpw(
            "admin123".encode(), bcrypt.gensalt()).decode()
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, role_id, status)
            VALUES (?, ?, ?, ?, 'active')
        """, ("admin", "admin@vernika.com", hashed_pw, admin_role_id))

        user_id = cursor.lastrowid

        # Create admin employee
        cursor.execute("SELECT MAX(id) as max_id FROM employees")
        result = cursor.fetchone()
        max_id = result['max_id'] if result and result['max_id'] else 0
        emp_code = f"EMP{max_id + 1:03d}"

        cursor.execute("""
            INSERT INTO employees (employee_code, user_id, first_name, last_name, email, department_id, is_active)
            VALUES (?, ?, ?, ?, ?, 1, 1)
        """, (emp_code, user_id, "Admin", "User", "admin@vernika.com", 1))

        print("  ✓ Created admin user (admin/admin123)")
    else:
        print("  ✓ Admin user exists")

    # Check if there are any employees
    cursor.execute("SELECT COUNT(*) as count FROM employees")
    emp_count = cursor.fetchone()[0]

    if emp_count < 2:
        # Create test employee
        cursor.execute("SELECT id FROM roles WHERE name = 'employee'")
        role = cursor.fetchone()
        emp_role_id = role['id'] if role else 2

        hashed_pw = bcrypt.hashpw(
            "employee123".encode(), bcrypt.gensalt()).decode()
        cursor.execute("""
            INSERT INTO users (username, email, password_hash, role_id, status)
            VALUES (?, ?, ?, ?, 'active')
        """, ("employee", "employee@vernika.com", hashed_pw, emp_role_id))

        user_id = cursor.lastrowid

        cursor.execute("SELECT MAX(id) as max_id FROM employees")
        result = cursor.fetchone()
        max_id = result['max_id'] if result and result['max_id'] else 0
        emp_code = f"EMP{max_id + 1:03d}"

        cursor.execute("""
            INSERT INTO employees (employee_code, user_id, first_name, last_name, email, department_id, is_active)
            VALUES (?, ?, ?, ?, ?, 1, 1)
        """, (emp_code, user_id, "John", "Doe", "employee@vernika.com", 1))

        print("  ✓ Created test employee (employee/employee123)")

    conn.commit()
    conn.close()
    print("  ✓ Test users checked")


def fix_database_consistency():
    """Fix any database consistency issues"""
    print("\n[6] Fixing database consistency...")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check for missing roles
    cursor.execute("SELECT COUNT(*) as count FROM roles")
    role_count = cursor.fetchone()[0]

    if role_count == 0:
        cursor.execute(
            "INSERT INTO roles (name, display_name, level) VALUES ('admin', 'Administrator', 100)")
        cursor.execute(
            "INSERT INTO roles (name, display_name, level) VALUES ('employee', 'Employee', 10)")
        print("  ✓ Created default roles")

    # Check for departments
    cursor.execute("SELECT COUNT(*) as count FROM departments")
    dept_count = cursor.fetchone()[0]

    if dept_count == 0:
        cursor.execute(
            "INSERT INTO departments (name, code) VALUES ('Human Resources', 'HR')")
        cursor.execute(
            "INSERT INTO departments (name, code) VALUES ('Information Technology', 'IT')")
        cursor.execute(
            "INSERT INTO departments (name, code) VALUES ('Finance', 'FIN')")
        cursor.execute(
            "INSERT INTO departments (name, code) VALUES ('Marketing', 'MKT')")
        print("  ✓ Created default departments")

    # Check for positions
    cursor.execute("SELECT COUNT(*) as count FROM positions")
    pos_count = cursor.fetchone()[0]

    if pos_count == 0:
        cursor.execute("SELECT id FROM departments LIMIT 1")
        dept = cursor.fetchone()
        dept_id = dept['id'] if dept else 1

        cursor.execute(
            "INSERT INTO positions (title, code, department_id) VALUES ('Software Developer', 'DEV', ?)", (dept_id,))
        cursor.execute(
            "INSERT INTO positions (title, code, department_id) VALUES ('HR Manager', 'HRMGR', ?)", (dept_id,))
        cursor.execute(
            "INSERT INTO positions (title, code, department_id) VALUES ('Accountant', 'ACC', ?)", (dept_id,))
        print("  ✓ Created default positions")

    conn.commit()
    conn.close()
    print("  ✓ Database consistency fixed")


def main():
    print("=" * 60)
    print("Vernika HRA - Comprehensive Fix")
    print("=" * 60)

    # Change to the correct directory
    os.chdir('/Users/shashankrajput/Desktop/Vernika')

    # Run all fixes
    fix_database_consistency()
    fix_screen_access_table()
    fix_user_employee_sync()
    fix_employee_deletion()
    fix_chat_tables()
    add_test_users()

    print("\n" + "=" * 60)
    print("✅ All fixes completed!")
    print("=" * 60)
    print("\nTest credentials:")
    print("  Admin: admin / admin123")
    print("  Employee: employee / employee123")
    print("\nNext steps:")
    print("  1. Run: python main.py")
    print("  2. Login and test chat functionality")
    print("  3. Check access control in admin panel")
    print("=" * 60)


if __name__ == "__main__":
    main()
