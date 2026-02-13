#!/usr/bin/env python3
"""
Update all screen files to use PostgreSQL instead of SQLite
This script replaces sqlite3.connect with SQLAlchemy-based database operations
"""

import os
import re

# Files to update
SCREEN_FILES = [
    'screens/employees_screen.py',
    'screens/dashboard_screen.py',
    'screens/attendance_screen.py',
    'screens/leaves_screen.py',
    'screens/tasks_screen.py',
    'screens/departments_screen.py',
    'screens/positions_screen.py',
    'screens/announcements_screen.py',
    'screens/documents_screen.py',
    'screens/profile_screen.py',
    'screens/chat_screen.py',
    'screens/reports_screen.py',
    'screens/settings_screen.py',
    'screens/admin_screen.py',
    'utils/screen_access.py',
]


def replace_sqlite_with_postgres(content, file_path):
    """Replace sqlite3.connect with PostgreSQL connection"""

    # Pattern to find sqlite3.connect
    pattern = r"sqlite3\.connect\(['\"]([^'\"]+)['\"]\)"

    # Replace with get_db_session
    # First, ensure we have the import
    if 'from database.connection import get_db_session' not in content:
        # Add import after other imports
        content = re.sub(
            r'(from database\.operations import)',
            r'from database.connection import get_db_session\n\\1',
            content
        )

    # Replace sqlite3.connect with get_db_session
    content = re.sub(
        r"sqlite3\.connect\(['\"][^'\"]+['\"]\)",
        "get_db_session()",
        content
    )

    # Replace sqlite3.Row with None (SQLAlchemy doesn't need this)
    content = re.sub(r"\.row_factory\s*=\s*sqlite3\.Row", "", content)

    # Replace cursor.fetchone/fetchall with SQLAlchemy queries
    # This is more complex - we'll handle common patterns

    # Replace conn.close() with db.close()
    content = re.sub(r"conn\.close\(\)", "db.close()", content)

    # Replace cursor = conn.cursor() - not needed in SQLAlchemy
    content = re.sub(r"cursor\s*=\s*conn\.cursor\(\)\s*\n", "", content)

    return content


def main():
    print("=" * 60)
    print("Updating screens to use PostgreSQL")
    print("=" * 60)

    base_path = '/Users/shashankrajput/Desktop/Vernika'

    for file_path in SCREEN_FILES:
        full_path = os.path.join(base_path, file_path)
        if not os.path.exists(full_path):
            print(f"  ⚠ File not found: {file_path}")
            continue

        try:
            with open(full_path, 'r') as f:
                content = f.read()

            # Check if file uses sqlite3
            if 'sqlite3.connect' not in content:
                print(f"  ✓ No SQLite in {file_path}")
                continue

            # Replace SQLite with PostgreSQL
            new_content = replace_sqlite_with_postgres(content, file_path)

            # Write back
            with open(full_path, 'w') as f:
                f.write(new_content)

            print(f"  ✓ Updated {file_path}")

        except Exception as e:
            print(f"  ✗ Error updating {file_path}: {e}")

    print("\n" + "=" * 60)
    print("⚠️  IMPORTANT: Manual updates still needed!")
    print("=" * 60)
    print("""
The following changes need to be done manually:

1. Update all cursor.execute() calls to use SQLAlchemy queries
2. Replace cursor.fetchone() with db.query().first()  
3. Replace cursor.fetchall() with db.query().all()
4. Replace cursor.lastrowid with None and use db.flush() + model.id
5. Replace conn.commit() with db.commit()
6. Replace conn.rollback() with db.rollback()

Example transformation:
    
    # OLD (SQLite):
    cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    
    # NEW (PostgreSQL):
    user = db.query(User).filter(User.id == user_id).first()

For complex queries, consider using database/operations.py functions.
""")


if __name__ == "__main__":
    main()
