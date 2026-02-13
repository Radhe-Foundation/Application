#!/usr/bin/env python3
"""
Vernika - Database Migration Script
Add user presence tracking columns for multi-user support
Supports both SQLite and PostgreSQL databases
"""

import sqlite3
from config import DATABASE_TYPE, DATABASE_URL
import os
import sys

# CRITICAL: Add the project root to the path FIRST, before any other imports
# This ensures we import from the local config.py, not the Python config package
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

# Now import from local config module


def migrate_sqlite():
    """Add presence tracking columns to users table for SQLite"""
    db_path = os.path.join(os.path.dirname(__file__), '..', 'vernika.db')
    db_path = os.path.abspath(db_path)

    print(f"📂 SQLite Database path: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check current schema
    cursor.execute("PRAGMA table_info(users)")
    columns = {row[1]: row for row in cursor.fetchall()}
    print(f"📋 Current users table columns: {list(columns.keys())}")

    # Add new columns if they don't exist
    migrations = [
        ("last_seen", "DATETIME"),
        ("is_online", "BOOLEAN DEFAULT 0"),
        ("session_token", "TEXT"),
        ("last_login", "DATETIME"),
        ("last_ip", "TEXT"),
    ]

    for col_name, col_type in migrations:
        if col_name not in columns:
            try:
                cursor.execute(
                    f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
                print(f"  ✅ Added column: {col_name}")
            except Exception as e:
                print(f"  ❌ Error adding {col_name}: {e}")
        else:
            print(f"  ✅ Column already exists: {col_name}")

    # Also ensure roles table exists and has proper structure
    cursor.execute("""CREATE TABLE IF NOT EXISTS roles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        display_name TEXT NOT NULL,
        description TEXT,
        is_active BOOLEAN DEFAULT 1,
        level INTEGER DEFAULT 1,
        permissions TEXT
    )""")

    # Ensure default roles exist
    cursor.execute("SELECT COUNT(*) FROM roles")
    result = cursor.fetchone()
    if result and result[0] == 0:
        roles = [
            ("admin", "Administrator", "Full system access", 100,
             '{"manage_users": true, "manage_employees": true, "manage_departments": true, "view_reports": true}'),
            ("employee", "Employee", "Basic employee access",
             10, '{"view_profile": true, "apply_leave": true}'),
        ]
        for name, display_name, description, level, permissions in roles:
            cursor.execute(
                "INSERT INTO roles (name, display_name, description, level, permissions) VALUES (?, ?, ?, ?, ?)",
                (name, display_name, description, level, permissions)
            )
        print("  ✅ Added default roles")

    conn.commit()
    conn.close()
    print("✅ SQLite migration completed successfully!")


def migrate_postgresql():
    """Add presence tracking columns to users table for PostgreSQL"""
    try:
        import psycopg2
    except ImportError:
        print("❌ psycopg2 not installed. Install it with: pip install psycopg2-binary")
        return False

    print(f"📂 PostgreSQL Database URL: {DATABASE_URL[:50]}...")

    # Parse the DATABASE_URL to get connection parameters
    # Format: postgresql://username:password@host:port/database
    try:
        # Use urllib to properly parse the URL
        from urllib.parse import urlparse
        parsed = urlparse(DATABASE_URL)

        user = parsed.username
        password = parsed.password
        host = parsed.hostname
        port = parsed.port or 5432
        database = parsed.path.strip('/')
    except Exception as e:
        print(f"❌ Error parsing DATABASE_URL: {e}")
        return False

    print(f"   Host: {host}, Port: {port}, Database: {database}, User: {user}")

    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # Check current schema
        cursor.execute("""
            SELECT column_name FROM information_schema.columns
            WHERE table_name = 'users'
        """)
        columns = [row[0] for row in cursor.fetchall()]
        print(f"📋 Current users table columns: {columns}")

        # Add new columns if they don't exist
        migrations = [
            ("last_seen", "TIMESTAMP"),
            ("is_online", "BOOLEAN DEFAULT FALSE"),
            ("session_token", "VARCHAR(255)"),
            ("last_login", "TIMESTAMP"),
            ("last_ip", "VARCHAR(50)"),
        ]

        for col_name, col_type in migrations:
            if col_name not in columns:
                try:
                    cursor.execute(
                        f"ALTER TABLE users ADD COLUMN {col_name} {col_type}")
                    print(f"  ✅ Added column: {col_name}")
                except Exception as e:
                    print(f"  ❌ Error adding {col_name}: {e}")
            else:
                print(f"  ✅ Column already exists: {col_name}")

        # Ensure roles table exists and has proper structure
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'roles'
            )
        """)
        result = cursor.fetchone()
        if result and not result[0]:
            print("  📋 Creating roles table...")
            cursor.execute("""
                CREATE TABLE roles (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(50) UNIQUE NOT NULL,
                    display_name VARCHAR(100) NOT NULL,
                    description TEXT,
                    is_active BOOLEAN DEFAULT TRUE,
                    level INTEGER DEFAULT 1,
                    permissions JSONB DEFAULT '{}'
                )
            """)
            print("  ✅ Created roles table")

        # Ensure default roles exist
        cursor.execute("SELECT COUNT(*) FROM roles")
        result = cursor.fetchone()
        if result and result[0] == 0:
            roles = [
                ("admin", "Administrator", "Full system access", 100,
                 '{"manage_users": true, "manage_employees": true, "manage_departments": true, "view_reports": true}'),
                ("employee", "Employee", "Basic employee access",
                 10, '{"view_profile": true, "apply_leave": true}'),
            ]
            for name, display_name, description, level, permissions in roles:
                cursor.execute(
                    "INSERT INTO roles (name, display_name, description, level, permissions) VALUES (%s, %s, %s, %s, %s)",
                    (name, display_name, description, level, permissions)
                )
            print("  ✅ Added default roles")

        conn.close()
        print("✅ PostgreSQL migration completed successfully!")
        return True

    except Exception as e:
        print(f"❌ PostgreSQL migration failed: {e}")
        return False


def create_sample_groups_sqlite():
    """Create sample chat groups for SQLite"""

    db_path = os.path.join(os.path.dirname(__file__), '..', 'vernika.db')
    db_path = os.path.abspath(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Create chat_groups table
    cursor.execute("""CREATE TABLE IF NOT EXISTS chat_groups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT,
        created_by INTEGER NOT NULL,
        is_active BOOLEAN DEFAULT 1,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (created_by) REFERENCES users(id)
    )""")

    # Create chat_group_members table
    cursor.execute("""CREATE TABLE IF NOT EXISTS chat_group_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        group_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        role TEXT DEFAULT 'member',
        joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (group_id) REFERENCES chat_groups(id),
        FOREIGN KEY (user_id) REFERENCES users(id)
    )""")

    # Create chat_messages table
    cursor.execute("""CREATE TABLE IF NOT EXISTS chat_messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER NOT NULL,
        group_id INTEGER,
        receiver_id INTEGER,
        content TEXT NOT NULL,
        message_type TEXT DEFAULT 'text',
        is_read BOOLEAN DEFAULT 0,
        has_attachment BOOLEAN DEFAULT 0,
        attachment_path TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (sender_id) REFERENCES users(id),
        FOREIGN KEY (group_id) REFERENCES chat_groups(id),
        FOREIGN KEY (receiver_id) REFERENCES users(id)
    )""")

    # Create sample groups if none exist
    cursor.execute("SELECT COUNT(*) FROM chat_groups")
    result = cursor.fetchone()
    if result and result[0] == 0:
        # Create General group
        cursor.execute(
            "INSERT INTO chat_groups (name, description, created_by) VALUES (?, ?, ?)",
            ("General", "General discussion for all employees", 1)
        )
        group_id = cursor.lastrowid

        # Add all users to General group
        cursor.execute("SELECT id FROM users")
        for (user_id,) in cursor.fetchall():
            role = "admin" if user_id == 1 else "member"
            cursor.execute(
                "INSERT INTO chat_group_members (group_id, user_id, role) VALUES (?, ?, ?)",
                (group_id, user_id, role)
            )

        # Create IT Team group
        cursor.execute(
            "INSERT INTO chat_groups (name, description, created_by) VALUES (?, ?, ?)",
            ("IT Team", "Discussion for IT department members", 1)
        )
        group_id = cursor.lastrowid

        # Add admin and some members
        for user_id in [1, 2, 3]:
            role = "admin" if user_id == 1 else "member"
            cursor.execute(
                "INSERT INTO chat_group_members (group_id, user_id, role) VALUES (?, ?, ?)",
                (group_id, user_id, role)
            )

        print("✅ Created sample chat groups")

    conn.commit()
    conn.close()
    print("✅ Chat tables created successfully!")


def create_sample_groups_postgresql():
    """Create sample chat groups for PostgreSQL"""
    try:
        import psycopg2
    except ImportError:
        print("❌ psycopg2 not installed. Install it with: pip install psycopg2-binary")
        return False

    # Parse the DATABASE_URL
    try:
        from urllib.parse import urlparse
        parsed = urlparse(DATABASE_URL)

        user = parsed.username
        password = parsed.password
        host = parsed.hostname
        port = parsed.port or 5432
        database = parsed.path.strip('/')
    except Exception as e:
        print(f"❌ Error parsing DATABASE_URL: {e}")
        return False

    try:
        conn = psycopg2.connect(
            host=host,
            port=port,
            database=database,
            user=user,
            password=password
        )
        conn.autocommit = True
        cursor = conn.cursor()

        # Create chat_groups table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_groups (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                description TEXT,
                created_by INTEGER NOT NULL REFERENCES users(id),
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create chat_group_members table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_group_members (
                id SERIAL PRIMARY KEY,
                group_id INTEGER NOT NULL REFERENCES chat_groups(id),
                user_id INTEGER NOT NULL REFERENCES users(id),
                role VARCHAR(20) DEFAULT 'member',
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create chat_messages table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_messages (
                id SERIAL PRIMARY KEY,
                sender_id INTEGER NOT NULL REFERENCES users(id),
                group_id INTEGER REFERENCES chat_groups(id),
                receiver_id INTEGER REFERENCES users(id),
                content TEXT NOT NULL,
                message_type VARCHAR(20) DEFAULT 'text',
                is_read BOOLEAN DEFAULT FALSE,
                has_attachment BOOLEAN DEFAULT FALSE,
                attachment_path VARCHAR(500),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Create sample groups if none exist
        cursor.execute("SELECT COUNT(*) FROM chat_groups")
        result = cursor.fetchone()
        if result and result[0] == 0:
            # Create General group
            cursor.execute(
                "INSERT INTO chat_groups (name, description, created_by) VALUES (%s, %s, %s) RETURNING id",
                ("General", "General discussion for all employees", 1)
            )
            group_id_result = cursor.fetchone()
            if group_id_result:
                group_id = group_id_result[0]

                # Add all users to General group
                cursor.execute("SELECT id FROM users")
                for (user_id,) in cursor.fetchall():
                    role = "admin" if user_id == 1 else "member"
                    cursor.execute(
                        "INSERT INTO chat_group_members (group_id, user_id, role) VALUES (%s, %s, %s)",
                        (group_id, user_id, role)
                    )

            # Create IT Team group
            cursor.execute(
                "INSERT INTO chat_groups (name, description, created_by) VALUES (%s, %s, %s) RETURNING id",
                ("IT Team", "Discussion for IT department members", 1)
            )
            group_id_result = cursor.fetchone()
            if group_id_result:
                group_id = group_id_result[0]

                # Add admin and some members
                for user_id in [1, 2, 3]:
                    role = "admin" if user_id == 1 else "member"
                    cursor.execute(
                        "INSERT INTO chat_group_members (group_id, user_id, role) VALUES (%s, %s, %s)",
                        (group_id, user_id, role)
                    )

            print("✅ Created sample chat groups")

        conn.close()
        print("✅ PostgreSQL chat tables created successfully!")
        return True

    except Exception as e:
        print(f"❌ PostgreSQL chat table creation failed: {e}")
        return False


def run_all_migrations():
    """Run all migrations based on database type"""
    print("=" * 60)
    print("🔧 Vernika Database Migration Script")
    print("=" * 60)
    print(f"📊 Database type: {DATABASE_TYPE}")

    if DATABASE_TYPE == "sqlite":
        migrate_sqlite()
        print("=" * 60)
        create_sample_groups_sqlite()
    elif DATABASE_TYPE == "postgresql":
        success = migrate_postgresql()
        if success:
            print("=" * 60)
            create_sample_groups_postgresql()
    else:
        print(f"❌ Unsupported database type: {DATABASE_TYPE}")
        print("   Supported types: sqlite, postgresql")

    print("=" * 60)
    print("✅ All migrations completed!")


if __name__ == "__main__":
    run_all_migrations()
