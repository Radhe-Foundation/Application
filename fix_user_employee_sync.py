"""
User-Employee Synchronization Utility
Ensures all users have employee records and all employees have user accounts
Run this after creating users or employees to sync the data
"""

import sqlite3
import bcrypt
from datetime import date


def auto_create_employee_for_user(conn, user_id, username, email):
    """Auto-create employee record when a user is created"""
    cursor = conn.cursor()

    # Check if employee already exists for this user
    cursor.execute("SELECT id FROM employees WHERE user_id = ?", (user_id,))
    if cursor.fetchone():
        return False  # Already has employee

    # Generate employee code
    cursor.execute("SELECT MAX(id) FROM employees")
    max_id = cursor.fetchone()[0] or 0
    emp_code = f"EMP{str(max_id + 1).zfill(4)}"

    # Generate name from username
    name_parts = username.replace('_', ' ').title().split()
    first_name = name_parts[0] if name_parts else username
    last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''

    # Insert employee record
    cursor.execute("""
        INSERT INTO employees (employee_code, user_id, first_name, last_name, email, 
                             date_of_joining, is_active, employment_type, employment_status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (emp_code, user_id, first_name, last_name, email, date.today(), 1, 'full_time', 'active'))
    return True


def auto_create_user_for_employee(conn, emp_id, first_name, last_name, email):
    """Auto-create user account when an employee is created without user"""
    cursor = conn.cursor()

    # Check if user already exists
    cursor.execute("SELECT user_id FROM employees WHERE id = ?", (emp_id,))
    result = cursor.fetchone()
    if result and result[0]:
        return False  # Already has user

    # Generate username
    username = f"{first_name.lower()}_{last_name.lower()}"

    # Make unique if needed
    cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
    if cursor.fetchone():
        username = first_name.lower()

    # Default password
    password = 'password123'
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    # Get employee role
    cursor.execute("SELECT id FROM roles WHERE name = ?", ('employee',))
    role = cursor.fetchone()
    role_id = role[0] if role else 2

    # Insert user
    cursor.execute("""
        INSERT INTO users (username, email, password_hash, role_id, status)
        VALUES (?, ?, ?, ?, ?)
    """, (username, email, password_hash, role_id, 'active'))

    user_id = cursor.lastrowid

    # Link to employee
    cursor.execute(
        "UPDATE employees SET user_id = ? WHERE id = ?", (user_id, emp_id))
    return True


def sync_user_employee():
    """Sync users and employees - ensure every user has an employee and vice versa"""
    conn = sqlite3.connect('vernika.db')
    cursor = conn.cursor()

    print("=== User-Employee Sync ===\n")

    # Get all roles
    cursor.execute("SELECT id, name FROM roles")
    roles = {r[1]: r[0] for r in cursor.fetchall()}
    print(f"Roles: {roles}")

    # 1. Find users WITHOUT employee records
    cursor.execute("""
        SELECT u.id, u.username, u.email, r.name as role_name
        FROM users u
        LEFT JOIN roles r ON u.role_id = r.id
        WHERE u.id NOT IN (SELECT user_id FROM employees WHERE user_id IS NOT NULL)
    """)
    users_without_employees = cursor.fetchall()

    print(
        f"\n1. Users without employee records: {len(users_without_employees)}")
    for u_id, username, email, role in users_without_employees:
        if auto_create_employee_for_user(conn, u_id, username, email):
            print(f"   ✓ Created employee for user: {username}")

    # 2. Find employees WITHOUT user accounts
    cursor.execute("""
        SELECT e.id, e.employee_code, e.first_name, e.last_name, e.email
        FROM employees e
        WHERE e.user_id IS NULL
    """)
    employees_without_users = cursor.fetchall()

    print(
        f"\n2. Employees without user accounts: {len(employees_without_users)}")
    for emp_id, code, first_name, last_name, email in employees_without_users:
        if auto_create_user_for_employee(conn, emp_id, first_name, last_name, email):
            print(f"   ✓ Created user for employee {code}")

    conn.commit()

    # 3. Show final status
    print("\n=== Final Status ===")
    cursor.execute("SELECT COUNT(*) FROM users")
    user_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM employees")
    emp_count = cursor.fetchone()[0]

    print(f"Total Users: {user_count}")
    print(f"Total Employees: {emp_count}")

    # Show all linked users
    print("\n=== All Linked Users ===")
    cursor.execute("""
        SELECT u.id, u.username, u.email, r.name as role,
               e.first_name || ' ' || e.last_name as emp_name
        FROM users u
        LEFT JOIN employees e ON u.id = e.user_id
        LEFT JOIN roles r ON u.role_id = r.id
        ORDER BY u.id
    """)
    for u_id, username, email, role, emp_name in cursor.fetchall():
        status = "✓" if emp_name else "⚠ NO EMPLOYEE"
        print(
            f"  {status} ID:{u_id} {username} ({email}) -> {emp_name or 'MISSING'}")

    conn.close()
    print("\n=== Sync Complete ===")


def run_sync_at_startup():
    """Run sync automatically at application startup"""
    try:
        sync_user_employee()
    except Exception as e:
        print(f"Sync warning: {e}")


if __name__ == "__main__":
    sync_user_employee()
