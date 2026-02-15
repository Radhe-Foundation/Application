"""
User-Employee Synchronization Utility (SQLAlchemy)
Ensures all users have employee records and all employees have user accounts
"""

from datetime import date
from sqlalchemy import text

from database.connection import get_db_session
from sqlalchemy.exc import SQLAlchemyError


def auto_create_employee_for_user(db, user_id, username, email):
    """Auto-create employee record when a user is created"""
    # Check if employee already exists for this user
    res = db.execute(text("SELECT id FROM employees WHERE user_id = :uid"), {
                     "uid": user_id}).fetchone()
    if res:
        return False

    max_id_row = db.execute(text("SELECT MAX(id) FROM employees")).fetchone()
    max_id = max_id_row[0] if max_id_row and max_id_row[0] else 0
    emp_code = f"EMP{str(max_id + 1).zfill(4)}"

    name_parts = username.replace('_', ' ').title().split()
    first_name = name_parts[0] if name_parts else username
    last_name = ' '.join(name_parts[1:]) if len(name_parts) > 1 else ''

    db.execute(text("""
        INSERT INTO employees (employee_code, user_id, first_name, last_name, email, 
                                date_of_joining, is_active, employment_type, employment_status)
        VALUES (:code, :uid, :first, :last, :email, :doj, :active, :etype, :estatus)
    """), {
        "code": emp_code,
        "uid": user_id,
        "first": first_name,
        "last": last_name,
        "email": email,
        "doj": date.today(),
        "active": True,
        "etype": 'full_time',
        "estatus": 'active'
    })
    return True


def auto_create_user_for_employee(db, emp_id, first_name, last_name, email):
    """Auto-create user account when an employee is created without user"""
    res = db.execute(text("SELECT user_id FROM employees WHERE id = :eid"), {
                     "eid": emp_id}).fetchone()
    if res and res[0]:
        return False

    username = f"{first_name.lower()}_{last_name.lower()}" if last_name else first_name.lower()
    exists = db.execute(text("SELECT id FROM users WHERE username = :uname"), {
                        "uname": username}).fetchone()
    if exists:
        username = first_name.lower()

    password = 'password123'
    import bcrypt
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    role_row = db.execute(text("SELECT id FROM roles WHERE name = :rname"), {
                          "rname": 'employee'}).fetchone()
    role_id = role_row[0] if role_row else 2

    db.execute(text("""
        INSERT INTO users (username, email, password_hash, role_id, status)
        VALUES (:username, :email, :phash, :role, :status)
    """), {"username": username, "email": email, "phash": password_hash, "role": role_id, "status": 'active'})

    user_id = db.execute(text("SELECT last_insert_rowid()")
                         ) if db.bind.dialect.name == 'sqlite' else None
    if not user_id:
        # Fallback: fetch by username
        row = db.execute(text("SELECT id FROM users WHERE username = :uname"), {
                         "uname": username}).fetchone()
        if row:
            user_id = row[0]

    if user_id:
        db.execute(text("UPDATE employees SET user_id = :uid WHERE id = :eid"), {
                   "uid": user_id, "eid": emp_id})
    return True


def sync_user_employee():
    db = get_db_session()
    try:
        print("=== User-Employee Sync ===\n")

        roles_rows = db.execute(text("SELECT id, name FROM roles")).fetchall()
        roles = {r[1]: r[0] for r in roles_rows}
        print(f"Roles: {roles}")

        users_without_employees = db.execute(text("""
            SELECT u.id, u.username, u.email, r.name as role_name
            FROM users u
            LEFT JOIN roles r ON u.role_id = r.id
            WHERE u.id NOT IN (SELECT user_id FROM employees WHERE user_id IS NOT NULL)
        """)).fetchall()

        print(
            f"\n1. Users without employee records: {len(users_without_employees)}")
        for row in users_without_employees:
            u_id, username, email, role = row[0], row[1], row[2], row[3]
            if auto_create_employee_for_user(db, u_id, username, email):
                print(f"   ✓ Created employee for user: {username}")

        employees_without_users = db.execute(text("""
            SELECT e.id, e.employee_code, e.first_name, e.last_name, e.email
            FROM employees e
            WHERE e.user_id IS NULL
        """)).fetchall()

        print(
            f"\n2. Employees without user accounts: {len(employees_without_users)}")
        for emp_id, code, first_name, last_name, email in employees_without_users:
            if auto_create_user_for_employee(db, emp_id, first_name, last_name, email):
                print(f"   ✓ Created user for employee {code}")

        db.commit()

        print("\n=== Final Status ===")
        user_count = db.execute(
            text("SELECT COUNT(*) FROM users")).fetchone()[0]
        emp_count = db.execute(
            text("SELECT COUNT(*) FROM employees")).fetchone()[0]

        print(f"Total Users: {user_count}")
        print(f"Total Employees: {emp_count}")

        print("\n=== All Linked Users ===")
        rows = db.execute(text("""
            SELECT u.id, u.username, u.email, r.name as role,
                   COALESCE(e.first_name, '') || ' ' || COALESCE(e.last_name, '') as emp_name
            FROM users u
            LEFT JOIN employees e ON u.id = e.user_id
            LEFT JOIN roles r ON u.role_id = r.id
            ORDER BY u.id
        """)).fetchall()

        for u_id, username, email, role, emp_name in rows:
            status = "✓" if emp_name and emp_name.strip() else "⚠ NO EMPLOYEE"
            print(
                f"  {status} ID:{u_id} {username} ({email}) -> {emp_name.strip() or 'MISSING'}")

    except SQLAlchemyError as e:
        print(f"Sync failed: {e}")
    finally:
        try:
            db.close()
        except:
            pass


def run_sync_at_startup():
    try:
        sync_user_employee()
    except Exception as e:
        print(f"Sync warning: {e}")


if __name__ == "__main__":
    sync_user_employee()
