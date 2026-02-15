#!/usr/bin/env python3
"""
Vernika HRA - Application Fix Script (SQLAlchemy-backed)

This script initializes the database using the project's SQLAlchemy
`init_db()` function and provides a safe place to run maintenance tasks.
"""

from database.connection import init_db


def fix_database():
    """Initialize/verify database schema using SQLAlchemy models."""
    print("=" * 60)
    print("Vernika HRA - Database Fix Script (SQLAlchemy)")
    print("=" * 60)
    print()

    # Initialize DB (create tables defined in models)
    init_db()

    print("Database initialized/verified via SQLAlchemy.\n")


if __name__ == '__main__':
    fix_database()

    # Create leave_requests table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS leave_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            leave_type_id INTEGER NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            days_requested REAL NOT NULL,
            reason TEXT NOT NULL,
            status VARCHAR(20) DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees(id),
            FOREIGN KEY (leave_type_id) REFERENCES leave_type_configs(id)
        )
    """)

    # Create attendances table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attendances (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER NOT NULL,
            date DATE NOT NULL,
            check_in DATETIME,
            check_out DATETIME,
            status VARCHAR(20) NOT NULL,
            working_hours REAL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (employee_id) REFERENCES employees(id),
            UNIQUE(employee_id, date)
        )
    """)

    # Create tasks table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            assigned_to_id INTEGER NOT NULL,
            created_by_id INTEGER NOT NULL,
            status VARCHAR(20) DEFAULT 'todo',
            priority VARCHAR(20) DEFAULT 'medium',
            due_date DATE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (assigned_to_id) REFERENCES employees(id),
            FOREIGN KEY (created_by_id) REFERENCES employees(id)
        )
    """)

    # Create task_comments table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS task_comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER NOT NULL,
            employee_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks(id),
            FOREIGN KEY (employee_id) REFERENCES employees(id)
        )
    """)

    # Create audit_logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            action VARCHAR(100) NOT NULL,
            details TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Create screen_access table (if not exists)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS screen_access (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            screen_key VARCHAR(50) NOT NULL,
            is_enabled BOOLEAN DEFAULT 1,
            granted_by INTEGER,
            granted_at DATETIME,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (granted_by) REFERENCES users(id),
            UNIQUE(user_id, screen_key)
        )
    """)

    # Create user_permissions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            permission_key VARCHAR(50) NOT NULL,
            is_allowed BOOLEAN DEFAULT 1,
            is_global BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id),
            UNIQUE(user_id, permission_key)
        )
    """)

    # Create time_off_requests table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS time_off_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            leave_type VARCHAR(50) NOT NULL,
            start_date DATE NOT NULL,
            end_date DATE NOT NULL,
            reason TEXT,
            status VARCHAR(20) DEFAULT 'pending',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            approved_by INTEGER,
            FOREIGN KEY (user_id) REFERENCES employees(id),
            FOREIGN KEY (approved_by) REFERENCES employees(id)
        )
    """)

    # Create messages table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            receiver_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            is_read BOOLEAN DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sender_id) REFERENCES employees(id),
            FOREIGN KEY (receiver_id) REFERENCES employees(id)
        )
    """)

    # Create chat_groups table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            created_by INTEGER NOT NULL,
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users(id)
        )
    """)

    # Create chat_group_members table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_group_members (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            group_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            role VARCHAR(20) DEFAULT 'member',
            joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (group_id) REFERENCES chat_groups(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
    """)

    # Create chat_messages table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS chat_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender_id INTEGER NOT NULL,
            group_id INTEGER,
            receiver_id INTEGER,
            content TEXT NOT NULL,
            message_type VARCHAR(20) DEFAULT 'text',
            is_read BOOLEAN DEFAULT 0,
            has_attachment BOOLEAN DEFAULT 0,
            attachment_path VARCHAR(500),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (sender_id) REFERENCES users(id),
            FOREIGN KEY (group_id) REFERENCES chat_groups(id),
            FOREIGN KEY (receiver_id) REFERENCES users(id)
        )
    """)

    conn.commit()
    print("✓ All tables created/verified")

    # Seed default data
    _seed_default_data(cursor, conn)

    conn.close()


def _seed_default_data(cursor, conn):
    """Seed default data"""
    print()
    print("Seeding default data...")

    # Check if roles exist
    cursor.execute("SELECT COUNT(*) FROM roles")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO roles (name, display_name, level, permissions) VALUES
            ('admin', 'Administrator', 100, '{"manage_users": true, "manage_employees": true, "manage_departments": true, "view_reports": true}'),
            ('employee', 'Employee', 10, '{"view_profile": true, "apply_leave": true}')
        """)
        print("  ✓ Roles created")

    # Check if company exists
    cursor.execute("SELECT COUNT(*) FROM companies")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO companies (name, email, phone, address) VALUES
            ('Vernika Technologies', 'hr@vernika.com', '+91-XXXX-XXXXXX', 'India')
        """)
        print("  ✓ Company created")

    # Check if admin user exists
    cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
    if cursor.fetchone()[0] == 0:
        # Get admin role ID
        cursor.execute("SELECT id FROM roles WHERE name = 'admin'")
        role = cursor.fetchone()
        if role:
            admin_role_id = role[0]
            # Create admin user with bcrypt hashed password
            hashed = bcrypt.hashpw("admin123".encode(),
                                   bcrypt.gensalt()).decode()
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, role_id, status) VALUES
                (?, ?, ?, ?, ?)
            """, ("admin", "admin@vernika.com", hashed, admin_role_id, "active"))
            print("  ✓ Admin user created (admin / admin123)")
    else:
        # Reset admin password
        cursor.execute("SELECT id FROM roles WHERE name = 'admin'")
        role = cursor.fetchone()
        if role:
            hashed = bcrypt.hashpw("admin123".encode(),
                                   bcrypt.gensalt()).decode()
            cursor.execute(
                "UPDATE users SET password_hash = ? WHERE username = 'admin'", (hashed,))
            print("  ✓ Admin password reset (admin / admin123)")

    # Check if leave types exist
    cursor.execute("SELECT COUNT(*) FROM leave_type_configs")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO leave_type_configs (name, display_name, max_days_per_year, is_paid, color) VALUES
            ('annual', 'Annual Leave', 20, 1, '#2E86AB'),
            ('sick', 'Sick Leave', 10, 1, '#28A745'),
            ('personal', 'Personal Leave', 5, 1, '#FF9800')
        """)
        print("  ✓ Leave types created")

    # Check if departments exist
    cursor.execute("SELECT COUNT(*) FROM departments")
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
            INSERT INTO departments (name, code, description) VALUES
            ('Human Resources', 'HR', 'Manages all HR functions'),
            ('Information Technology', 'IT', 'Software development and infrastructure'),
            ('Finance', 'FIN', 'Financial management and accounting'),
            ('Marketing', 'MKT', 'Marketing and brand management'),
            ('Operations', 'OPS', 'Day-to-day operations')
        """)
        print("  ✓ Departments created")

    # Check if positions exist
    cursor.execute("SELECT COUNT(*) FROM positions")
    if cursor.fetchone()[0] == 0:
        # Get department IDs
        cursor.execute("SELECT id FROM departments WHERE code = 'HR'")
        hr_dept = cursor.fetchone()
        cursor.execute("SELECT id FROM departments WHERE code = 'IT'")
        it_dept = cursor.fetchone()

        positions = [
            ("HR Manager", "HRMGR", "Manage HR department",
             hr_dept[0] if hr_dept else 1),
            ("Software Developer", "DEV", "Develop software",
             it_dept[0] if it_dept else 2),
        ]
        for title, code, desc, dept_id in positions:
            cursor.execute(
                "INSERT INTO positions (title, code, description, department_id) VALUES (?, ?, ?, ?)",
                (title, code, desc, dept_id)
            )
        print("  ✓ Positions created")

    conn.commit()
    print("  ✓ Default data seeded successfully")


if __name__ == "__main__":
    fix_database()
    print()
    print("=" * 60)
    print("Database fix complete!")
    print("You can now run: python main.py")
    print("=" * 60)
