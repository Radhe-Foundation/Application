"""
Vernika HRA - Database Seed Script
Creates proper test users with correctly hashed passwords and sample data
"""

import bcrypt
import sqlite3
from datetime import datetime, timedelta
import random
import string


def get_db():
    """Get database connection"""
    conn = sqlite3.connect('vernika.db')
    conn.row_factory = sqlite3.Row
    return conn


def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def create_tables(conn):
    """Create all tables if they don't exist"""
    cursor = conn.cursor()

    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role_id INTEGER,
            status TEXT DEFAULT 'active',
            created_at TEXT,
            last_seen TEXT,
            is_online INTEGER DEFAULT 0,
            session_token TEXT,
            last_login TEXT,
            last_ip TEXT,
            FOREIGN KEY (role_id) REFERENCES roles (id)
        )
    """
    Vernika HRA - Database Seed Script (DISABLED FOR PRODUCTION)
    All demo/test/sample data seeding is removed for production use.
    """

    if __name__ == "__main__":
        print("This script is disabled for production. No demo data will be seeded.")
        exit(0)
    ''')

    conn.commit()
    print("✓ All tables created/verified")


def seed_roles(cursor):
    """Seed roles table"""
    # Check if roles exist
    cursor.execute("SELECT COUNT(*) FROM roles")
    if cursor.fetchone()[0] > 0:
        print("✓ Roles already exist, skipping...")
        return

    roles = [
        ('admin', 'Administrator', 'Full system access', 100,
         '{"manage_users": true, "manage_employees": true, "view_reports": true}'),
        ('hr_manager', 'HR Manager', 'HR management access', 50,
         '{"manage_employees": true, "view_reports": true}'),
        ('manager', 'Manager', 'Team management access',
         30, '{"view_team": true}'),
        ('employee', 'Employee', 'Basic employee access',
         10, '{"view_profile": true}'),
    ]

    for name, display_name, description, level, permissions in roles:
        cursor.execute(
            "INSERT INTO roles (name, display_name, description, level, permissions) VALUES (?, ?, ?, ?, ?)",
            (name, display_name, description, level, permissions)
        )

    conn.commit()
    print("✓ Roles seeded")


def seed_departments(cursor):
    """Seed departments table"""
    cursor.execute("SELECT COUNT(*) FROM departments")
    if cursor.fetchone()[0] > 0:
        print("✓ Departments already exist, skipping...")
        return

    departments = [
        ('Human Resources', 'HR', 'HR Department'),
        ('Information Technology', 'IT', 'IT Department'),
        ('Finance', 'FIN', 'Finance Department'),
        ('Marketing', 'MKT', 'Marketing Department'),
        ('Operations', 'OPS', 'Operations Department'),
    ]

    for name, code, description in departments:
        cursor.execute(
            "INSERT INTO departments (name, code, description, created_at) VALUES (?, ?, ?, ?)",
            (name, code, description, datetime.now().isoformat())
        )

    conn.commit()
    print("✓ Departments seeded")


def seed_positions(cursor):
    """Seed positions table"""
    cursor.execute("SELECT COUNT(*) FROM positions")
    if cursor.fetchone()[0] > 0:
        print("✓ Positions already exist, skipping...")
        return

    positions = [
        ('HR Manager', 'HRMGR', None, 'HR Management'),
        ('Software Developer', 'DEV', None, 'Development'),
        ('Accountant', 'ACC', None, 'Finance'),
        ('Marketing Specialist', 'MKTSP', None, 'Marketing'),
        ('Operations Manager', 'OPSMGR', None, 'Operations'),
        ('Senior Developer', 'SRDEV', None, 'Development'),
        ('QA Engineer', 'QA', None, 'Quality Assurance'),
        ('DevOps Engineer', 'DEVOPS', None, 'IT Operations'),
    ]

    for title, code, dept_id, description in positions:
        cursor.execute(
            "INSERT INTO positions (title, code, description, created_at) VALUES (?, ?, ?, ?)",
            (title, code, description, datetime.now().isoformat())
        )

    conn.commit()
    print("✓ Positions seeded")


def seed_leave_types(cursor):
    """Seed leave type configs table"""
    cursor.execute("SELECT COUNT(*) FROM leave_type_configs")
    if cursor.fetchone()[0] > 0:
        print("✓ Leave types already exist, skipping...")
        return

    leave_types = [
        ('annual', 'Annual Leave', 20, 1, '#2E86AB'),
        ('sick', 'Sick Leave', 10, 1, '#F44336'),
        ('personal', 'Personal Leave', 5, 1, '#FF9800'),
        ('maternity', 'Maternity Leave', 90, 1, '#E91E63'),
        ('paternity', 'Paternity Leave', 14, 1, '#2196F3'),
        ('bereavement', 'Bereavement Leave', 5, 1, '#9C27B0'),
        ('unpaid', 'Unpaid Leave', 0, 0, '#607D8B'),
    ]

    for name, display_name, max_days, is_paid, color in leave_types:
        cursor.execute(
            "INSERT INTO leave_type_configs (name, display_name, max_days_per_year, is_paid, color) VALUES (?, ?, ?, ?, ?)",
            (name, display_name, max_days, is_paid, color)
        )

    conn.commit()
    print("✓ Leave types seeded")


def seed_users_and_employees(cursor):
    """Seed users and employees"""
    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] > 0:
        print("✓ Users already exist, skipping...")
        return

    # Users with their passwords
    users = [
        # Admin user
        {
            'username': 'admin',
            'email': 'admin@vernika.com',
            'password': 'admin123',
            'role_id': 1,
            'first_name': 'System',
            'last_name': 'Administrator',
            'department_id': 1,
            'position_id': 1,
            'basic_salary': 150000,
        },
        # HR Manager
        {
            'username': 'hr_manager',
            'email': 'hr@vernika.com',
            'password': 'hr123',
            'role_id': 2,
            'first_name': 'Sarah',
            'last_name': 'Johnson',
            'department_id': 1,
            'position_id': 1,
            'basic_salary': 120000,
        },
        # Manager
        {
            'username': 'manager',
            'email': 'manager@vernika.com',
            'password': 'manager123',
            'role_id': 3,
            'first_name': 'Michael',
            'last_name': 'Chen',
            'department_id': 2,
            'position_id': 6,
            'basic_salary': 100000,
        },
        # Employees
        {
            'username': 'john_doe',
            'email': 'john@vernika.com',
            'password': 'john123',
            'role_id': 4,
            'first_name': 'John',
            'last_name': 'Doe',
            'department_id': 2,
            'position_id': 2,
            'basic_salary': 60000,
        },
        {
            'username': 'jane_smith',
            'email': 'jane@vernika.com',
            'password': 'jane123',
            'role_id': 4,
            'first_name': 'Jane',
            'last_name': 'Smith',
            'department_id': 2,
            'position_id': 6,
            'basic_salary': 75000,
        },
        {
            'username': 'mike_wilson',
            'email': 'mike@vernika.com',
            'password': 'mike123',
            'role_id': 4,
            'first_name': 'Mike',
            'last_name': 'Wilson',
            'department_id': 2,
            'position_id': 2,
            'basic_salary': 65000,
        },
        {
            'username': 'emily_brown',
            'email': 'emily@vernika.com',
            'password': 'emily123',
            'role_id': 4,
            'first_name': 'Emily',
            'last_name': 'Brown',
            'department_id': 3,
            'position_id': 3,
            'basic_salary': 55000,
        },
        {
            'username': 'david_lee',
            'email': 'david@vernika.com',
            'password': 'david123',
            'role_id': 4,
            'first_name': 'David',
            'last_name': 'Lee',
            'department_id': 4,
            'position_id': 4,
            'basic_salary': 58000,
        },
        {
            'username': 'lisa_wong',
            'email': 'lisa@vernika.com',
            'password': 'lisa123',
            'role_id': 4,
            'first_name': 'Lisa',
            'last_name': 'Wong',
            'department_id': 5,
            'position_id': 5,
            'basic_salary': 70000,
        },
        {
            'username': 'alex_garcia',
            'email': 'alex@vernika.com',
            'password': 'alex123',
            'role_id': 4,
            'first_name': 'Alex',
            'last_name': 'Garcia',
            'department_id': 2,
            'position_id': 7,
            'basic_salary': 62000,
        },
    ]

    for user_data in users:
        # Create user
        hashed_password = hash_password(user_data['password'])
        cursor.execute(
            """INSERT INTO users (username, email, password_hash, role_id, status, created_at) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_data['username'], user_data['email'], hashed_password,
             user_data['role_id'], 'active', datetime.now().isoformat())
        )
        user_id = cursor.lastrowid

        # Generate employee code
        max_id = user_id if user_id > 0 else 1
        emp_code = f"EMP{max_id:03d}"

        # Create employee
        cursor.execute(
            """INSERT INTO employees (
                employee_code, user_id, first_name, last_name, email, phone,
                department_id, position_id, basic_salary, employment_type, 
                employment_status, date_of_joining, is_active, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                emp_code, user_id, user_data['first_name'], user_data['last_name'],
                user_data['email'], f"+91-98765{random.randint(10000, 99999)}",
                user_data['department_id'], user_data['position_id'],
                user_data['basic_salary'], 'full_time', 'active',
                (datetime.now() - timedelta(days=random.randint(30, 365))
                 ).strftime('%Y-%m-%d'),
                1, datetime.now().isoformat()
            )
        )

    conn.commit()
    print("✓ Users and employees seeded")


def seed_chat_groups(cursor):
    """Seed chat groups"""
    cursor.execute("SELECT COUNT(*) FROM chat_groups")
    if cursor.fetchone()[0] > 0:
        print("✓ Chat groups already exist, skipping...")
        return

    groups = [
        ('General', 'General company announcements', 1),
        ('IT Team', 'IT Department discussions', 1),
        ('HR Updates', 'HR announcements', 2),
        ('Managers', 'Manager discussions', 3),
        ('New Hires', 'Welcome new employees', 1),
    ]

    for name, description, created_by in groups:
        cursor.execute(
            "INSERT INTO chat_groups (name, description, created_by, is_active, created_at) VALUES (?, ?, ?, ?, ?)",
            (name, description, created_by, 1, datetime.now().isoformat())
        )
        group_id = cursor.lastrowid

        # Add members to groups
        if group_id == 1:  # General - all users
            for user_id in range(1, 11):
                role = 'admin' if user_id == 1 else 'member'
                cursor.execute(
                    "INSERT INTO chat_group_members (group_id, user_id, role, joined_at) VALUES (?, ?, ?, ?)",
                    (group_id, user_id, role, datetime.now().isoformat())
                )
        elif group_id == 2:  # IT Team
            for user_id in [1, 4, 5, 6, 10]:
                role = 'admin' if user_id == 1 else 'member'
                cursor.execute(
                    "INSERT INTO chat_group_members (group_id, user_id, role, joined_at) VALUES (?, ?, ?, ?)",
                    (group_id, user_id, role, datetime.now().isoformat())
                )
        elif group_id == 3:  # HR Updates
            for user_id in [1, 2]:
                role = 'admin' if user_id == 2 else 'member'
                cursor.execute(
                    "INSERT INTO chat_group_members (group_id, user_id, role, joined_at) VALUES (?, ?, ?, ?)",
                    (group_id, user_id, role, datetime.now().isoformat())
                )
        elif group_id == 4:  # Managers
            for user_id in [1, 3]:
                role = 'admin' if user_id == 1 else 'member'
                cursor.execute(
                    "INSERT INTO chat_group_members (group_id, user_id, role, joined_at) VALUES (?, ?, ?, ?)",
                    (group_id, user_id, role, datetime.now().isoformat())
                )
        elif group_id == 5:  # New Hires
            for user_id in [1, 4, 5, 6]:
                role = 'admin' if user_id == 1 else 'member'
                cursor.execute(
                    "INSERT INTO chat_group_members (group_id, user_id, role, joined_at) VALUES (?, ?, ?, ?)",
                    (group_id, user_id, role, datetime.now().isoformat())
                )

    conn.commit()
    print("✓ Chat groups seeded")


def seed_sample_messages(cursor):
    """Seed sample chat messages"""
    cursor.execute("SELECT COUNT(*) FROM chat_messages")
    if cursor.fetchone()[0] > 0:
        print("✓ Sample messages already exist, skipping...")
        return

    messages = [
        # Group messages - General
        (1, 1, None, 'Welcome to Vernika HRA! Feel free to introduce yourself.',
         '2024-01-15 09:00:00'),
        (1, 2, None, 'Hello everyone! Happy to be here!', '2024-01-15 09:15:00'),
        (1, 3, None, 'Welcome Sarah! Great to have you!', '2024-01-15 09:20:00'),
        (1, 4, None, 'Hi all, John Doe here, excited to work here!', '2024-01-15 10:00:00'),
        (1, 5, None, 'Welcome John! Let me know if you need any help!',
         '2024-01-15 10:05:00'),

        # Group messages - IT Team
        (2, 1, None, 'IT Team channel is active!', '2024-01-16 08:00:00'),
        (2, 4, None, 'Ready to start the new project!', '2024-01-16 09:00:00'),
        (2, 5, None, 'Sprint planning at 2 PM today', '2024-01-16 10:00:00'),
        (2, 6, None, 'Will be there!', '2024-01-16 10:30:00'),

        # Direct messages
        (None, 1, 4, 'Hi John, welcome to the team!', '2024-01-15 10:30:00'),
        (None, 4, 1, 'Thank you! Excited to work here!', '2024-01-15 10:35:00'),
        (None, 1, 5, 'Jane, please help John with onboarding', '2024-01-15 11:00:00'),
        (None, 5, 1, 'Will do!', '2024-01-15 11:05:00'),
    ]

    for sender_id, group_id, receiver_id, content, created_at in messages:
        cursor.execute(
            """INSERT INTO chat_messages (sender_id, group_id, receiver_id, content, message_type, is_read, created_at) 
               VALUES (?, ?, ?, ?, 'text', ?, ?)""",
            (sender_id, group_id, receiver_id, content, 1, created_at)
        )

    conn.commit()
    print("✓ Sample messages seeded")


def seed_attendance(cursor):
    """Seed sample attendance records for today"""
    today = datetime.now().strftime('%Y-%m-%d')

    # Mark all employees as present for today (sample data)
    cursor.execute("SELECT id FROM employees WHERE is_active = 1")
    employees = cursor.fetchall()

    for emp in employees:
        cursor.execute(
            """INSERT OR IGNORE INTO attendances (employee_id, date, status, created_at) 
               VALUES (?, ?, ?, ?)""",
            (emp['id'], today, 'present', datetime.now().isoformat())
        )

    conn.commit()
    print("✓ Attendance records seeded")


def seed_tasks(cursor):
    """Seed sample tasks"""
    cursor.execute("SELECT COUNT(*) FROM tasks")
    if cursor.fetchone()[0] > 0:
        print("✓ Tasks already exist, skipping...")
        return

    tasks = [
        ('Complete onboarding', 'Finish all onboarding formalities',
         4, 1, 'todo', 'high', None),
        ('Set up development environment', 'Install required software',
         4, 1, 'in_progress', 'high', None),
        ('Review project documentation',
         'Go through project specs', 5, 3, 'todo', 'medium', None),
        ('Team meeting', 'Attend weekly team meeting', 6, 3, 'todo', 'medium', None),
        ('Submit timesheet', 'Fill out weekly timesheet', 4, 1, 'todo', 'low', None),
    ]

    for title, description, assigned_to, created_by, status, priority, due_date in tasks:
        cursor.execute(
            """INSERT INTO tasks (title, description, assigned_to_id, created_by_id, status, priority, due_date, created_at) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (title, description, assigned_to, created_by, status,
             priority, due_date, datetime.now().isoformat())
        )

    conn.commit()
    print("✓ Tasks seeded")


def main():
    """Main seed function"""
    global conn

    print("\n" + "="*50)
    print("Vernika HRA - Database Seeding")
    print("="*50 + "\n")

    conn = get_db()
    cursor = conn.cursor()

    try:
        # Create tables
        create_tables(conn)

        # Seed data
        seed_roles(cursor)
        seed_departments(cursor)
        seed_positions(cursor)
        seed_leave_types(cursor)
        seed_users_and_employees(cursor)
        seed_chat_groups(cursor)
        seed_sample_messages(cursor)
        seed_attendance(cursor)
        seed_tasks(cursor)

        print("\n" + "="*50)
        print("✅ Database seeding completed successfully!")
        print("="*50)
        print("\n📋 Login Credentials:")
        print("-" * 30)
        print("Username     | Password    | Role")
        print("-" * 30)
        print("admin        | admin123    | Administrator")
        print("hr_manager   | hr123       | HR Manager")
        print("manager      | manager123  | Manager")
        print("john_doe     | john123     | Employee")
        print("jane_smith   | jane123     | Employee")
        print("mike_wilson  | mike123     | Employee")
        print("-" * 30)
        print("\n💡 All passwords work with both username and email")

    except Exception as e:
        print(f"\n❌ Error seeding database: {e}")
        import traceback
        traceback.print_exc()
        conn.rollback()
    finally:
        conn.close()


if __name__ == "__main__":
    main()
