"""
Add Missing Test Users (SQLAlchemy)
"""

from datetime import datetime
from database.connection import get_db_session
from database.operations import get_user_by_username, create_employee_with_user


def main():
    db = get_db_session()
    print("\n" + "="*50)
    print("Adding Test Users to Vernika Database")
    print("="*50 + "\n")

    test_users = [
        {'username': 'john_doe', 'email': 'john@vernika.com', 'password': 'john123', 'role_id': 4,
            'first_name': 'John', 'last_name': 'Doe', 'department_id': 2, 'position_id': 2, 'basic_salary': 60000},
        {'username': 'jane_smith', 'email': 'jane@vernika.com', 'password': 'jane123', 'role_id': 4,
            'first_name': 'Jane', 'last_name': 'Smith', 'department_id': 2, 'position_id': 2, 'basic_salary': 65000},
        {'username': 'mike_wilson', 'email': 'mike@vernika.com', 'password': 'mike123', 'role_id': 4,
            'first_name': 'Mike', 'last_name': 'Wilson', 'department_id': 3, 'position_id': 3, 'basic_salary': 55000},
        {'username': 'manager', 'email': 'manager@vernika.com', 'password': 'manager123', 'role_id': 3,
            'first_name': 'Michael', 'last_name': 'Chen', 'department_id': 2, 'position_id': 2, 'basic_salary': 100000},
    ]

    added_count = 0
    try:
        for u in test_users:
            if get_user_by_username(db, u['username']):
                print(f"⏩ User '{u['username']}' already exists, skipping...")
                continue

            # Use create_employee_with_user to set up user + employee atomically
            create_employee_with_user(
                db,
                username=u['username'],
                email=u['email'],
                password=u['password'],
                role_id=u['role_id'],
                first_name=u['first_name'],
                last_name=u['last_name'],
                department_id=u['department_id'],
                position_id=u['position_id'],
            )
            print(f"✅ Added user: {u['username']} / {u['password']}")
            added_count += 1

        db.commit()
    except Exception as e:
        print(f"Error adding test users: {e}")
        db.rollback()
    finally:
        try:
            db.close()
        except:
            pass

    print("\n" + "="*50)
    print(f"✅ Added {added_count} new users successfully!")
    print("="*50)


if __name__ == '__main__':
    main()
