"""
Vernika HRA - Add Missing Test Users
Adds test employees to the existing database
"""

import sqlite3
import bcrypt
from datetime import datetime


def get_db():
    return sqlite3.connect('vernika.db')


def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def main():
    conn = get_db()
    cursor = conn.cursor()

    print("\n" + "="*50)
    print("Adding Test Users to Vernika Database")
    print("="*50 + "\n")

    # Test users to add
    test_users = [
        {
            'username': 'john_doe',
            'email': 'john@vernika.com',
            'password': 'john123',
            'role_id': 4,  # employee
            'first_name': 'John',
            'last_name': 'Doe',
            'department_id': 2,  # IT
            'position_id': 2,  # Developer
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
            'position_id': 2,
            'basic_salary': 65000,
        },
        {
            'username': 'mike_wilson',
            'email': 'mike@vernika.com',
            'password': 'mike123',
            'role_id': 4,
            'first_name': 'Mike',
            'last_name': 'Wilson',
            'department_id': 3,  # Finance
            'position_id': 3,  # Accountant
            'basic_salary': 55000,
        },
        {
            'username': 'manager',
            'email': 'manager@vernika.com',
            'password': 'manager123',
            'role_id': 3,  # manager
            'first_name': 'Michael',
            'last_name': 'Chen',
            'department_id': 2,
            'position_id': 2,
            'basic_salary': 100000,
        },
    ]

    added_count = 0
    for user_data in test_users:
        # Check if user already exists
        cursor.execute("SELECT id FROM users WHERE username = ?",
                       (user_data['username'],))
        if cursor.fetchone():
            print(
                f"⏩ User '{user_data['username']}' already exists, skipping...")
            continue

        # Create user with bcrypt hash
        hashed_password = hash_password(user_data['password'])
        cursor.execute(
            """INSERT INTO users (username, email, password_hash, role_id, status, created_at) 
               VALUES (?, ?, ?, ?, ?, ?)""",
            (user_data['username'], user_data['email'], hashed_password,
             user_data['role_id'], 'active', datetime.now().isoformat())
        )
        user_id = cursor.lastrowid

        # Generate employee code
        cursor.execute("SELECT MAX(id) FROM employees")
        result = cursor.fetchone()[0]
        emp_code = f"EMP{(result or 0) + 1:03d}"

        # Create employee
        cursor.execute(
            """INSERT INTO employees (
                employee_code, user_id, first_name, last_name, email,
                department_id, position_id, basic_salary, employment_type, 
                employment_status, date_of_joining, is_active, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                emp_code, user_id, user_data['first_name'], user_data['last_name'],
                user_data['email'], user_data['department_id'], user_data['position_id'],
                user_data['basic_salary'], 'full_time', 'active',
                datetime.now().strftime('%Y-%m-%d'), 1, datetime.now().isoformat()
            )
        )

        print(
            f"✅ Added user: {user_data['username']} / {user_data['password']}")
        added_count += 1

    conn.commit()

    # Add sample chat groups and messages
    print("\n📝 Adding sample chat data...")

    # Check if groups exist
    cursor.execute("SELECT COUNT(*) FROM chat_groups")
    if cursor.fetchone()[0] == 0:
        groups = [
            ('General', 'General company discussions', 1),
            ('IT Team', 'IT Department channel', 1),
            ('HR Updates', 'HR announcements', 1),
        ]
        for name, desc, created_by in groups:
            cursor.execute(
                "INSERT INTO chat_groups (name, description, created_by, is_active, created_at) VALUES (?, ?, ?, ?, ?)",
                (name, desc, created_by, 1, datetime.now().isoformat())
            )

        # Add members to General group
        cursor.execute("SELECT id FROM users")
        for (user_id,) in cursor.fetchall():
            cursor.execute(
                "INSERT INTO chat_group_members (group_id, user_id, role, joined_at) VALUES (?, ?, ?, ?)",
                (1, user_id, 'member' if user_id !=
                 1 else 'admin', datetime.now().isoformat())
            )

        print("✅ Added chat groups")
    else:
        print("⏩ Chat groups already exist")

    # Add sample messages
    cursor.execute("SELECT COUNT(*) FROM chat_messages")
    if cursor.fetchone()[0] == 0:
        messages = [
            (1, 1, None, 'Welcome to Vernika HRA Chat! Feel free to introduce yourself.',
             datetime.now().isoformat()),
            (1, 3, None, 'Hello everyone! Happy to be here!',
             datetime.now().isoformat()),
            (1, 4, None, 'Hi all, ready to work!', datetime.now().isoformat()),
        ]
        for sender_id, group_id, receiver_id, content, created_at in messages:
            cursor.execute(
                "INSERT INTO chat_messages (sender_id, group_id, receiver_id, content, message_type, is_read, created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (sender_id, group_id, receiver_id, content, 'text', 1, created_at)
            )
        print("✅ Added sample messages")
    else:
        print("⏩ Messages already exist")

    conn.commit()
    conn.close()

    print("\n" + "="*50)
    print(f"✅ Added {added_count} new users successfully!")
    print("="*50)
    print("\n📋 Login Credentials:")
    print("-" * 40)
    print("Username       | Password    | Role")
    print("-" * 40)
    print("admin          | admin123    | Administrator")
    print("rajat          | (existing)  | HR Manager")
    print("john_doe       | john123     | Employee")
    print("jane_smith     | jane123     | Employee")
    print("mike_wilson    | mike123     | Employee")
    print("manager        | manager123  | Manager")
    print("-" * 40)
    print("\n💡 All users can login with username and their password")


if __name__ == "__main__":
    main()
