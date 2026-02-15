#!/usr/bin/env python3
"""
Vernika - Database Migration Script (SQLAlchemy-backed)

This revised migration script uses the application's SQLAlchemy engine
from `database.connection` so it works for both SQLite and PostgreSQL
backends configured via `config.py`.

It avoids direct `sqlite3` or `psycopg2` imports and performs schema
updates using raw SQL `ALTER TABLE` statements appropriate for the
current dialect. Always take backups before running migrations.
"""

from database.connection import get_engine
import os
import sys
from sqlalchemy import text, inspect

# Ensure project root is on path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


def migrate_with_sqlalchemy():
    engine = get_engine()
    dialect = engine.dialect.name
    print(f"Using SQLAlchemy engine - dialect: {dialect}")

    # Determine column types per dialect
    if dialect == 'sqlite':
        col_types = {
            'last_seen': 'DATETIME',
            'is_online': 'BOOLEAN DEFAULT 0',
            'session_token': 'TEXT',
            'last_login': 'DATETIME',
            'last_ip': 'TEXT',
        }
    else:
        # default to postgres-compatible types
        col_types = {
            'last_seen': 'TIMESTAMP',
            'is_online': 'BOOLEAN DEFAULT FALSE',
            'session_token': 'VARCHAR(255)',
            'last_login': 'TIMESTAMP',
            'last_ip': 'VARCHAR(50)',
        }

    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    # Ensure roles table exists
    if 'roles' not in existing_tables:
        print("Creating roles table")
        create_roles_sql = (
            "CREATE TABLE roles ("
            "id SERIAL PRIMARY KEY,"
            "name VARCHAR(50) UNIQUE NOT NULL,"
            "display_name VARCHAR(100) NOT NULL,"
            "description TEXT,"
            "is_active BOOLEAN DEFAULT TRUE,"
            "level INTEGER DEFAULT 1,"
            "permissions TEXT"
            ")"
        )
        # For sqlite, SERIAL is not supported; use INTEGER PRIMARY KEY AUTOINCREMENT
        if dialect == 'sqlite':
            create_roles_sql = (
                "CREATE TABLE roles ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT,"
                "name TEXT UNIQUE NOT NULL,"
                "display_name TEXT NOT NULL,"
                "description TEXT,"
                "is_active BOOLEAN DEFAULT 1,"
                "level INTEGER DEFAULT 1,"
                "permissions TEXT"
                ")"
            )

        with engine.begin() as conn:
            conn.execute(text(create_roles_sql))
        print("  ✅ Roles table ensured")

    # Ensure users table has new columns
    if 'users' not in existing_tables:
        print("Warning: 'users' table not found. Create tables via migrations before running this script.")
        return

    columns = {col['name'] for col in inspector.get_columns('users')}
    print(f"Current users columns: {sorted(columns)}")

    with engine.begin() as conn:
        for col_name, col_type in col_types.items():
            if col_name not in columns:
                try:
                    # SQLite has limited ALTER TABLE support but ADD COLUMN works
                    alter_sql = f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"
                    conn.execute(text(alter_sql))
                    print(f"  ✅ Added column: {col_name}")
                except Exception as e:
                    print(f"  ❌ Error adding {col_name}: {e}")
            else:
                print(f"  ✅ Column already exists: {col_name}")

    print("✅ Migration completed")


def create_sample_groups():
    engine = get_engine()
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    with engine.begin() as conn:
        # Create chat_groups if missing
        if 'chat_groups' not in existing_tables:
            if engine.dialect.name == 'sqlite':
                conn.execute(text('''
                CREATE TABLE chat_groups (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    created_by INTEGER NOT NULL,
                    is_active BOOLEAN DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                '''))
            else:
                conn.execute(text('''
                CREATE TABLE chat_groups (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    description TEXT,
                    created_by INTEGER NOT NULL REFERENCES users(id),
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                '''))
            print("  ✅ chat_groups created")

        if 'chat_group_members' not in existing_tables:
            if engine.dialect.name == 'sqlite':
                conn.execute(text('''
                CREATE TABLE chat_group_members (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    role TEXT DEFAULT 'member',
                    joined_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                '''))
            else:
                conn.execute(text('''
                CREATE TABLE chat_group_members (
                    id SERIAL PRIMARY KEY,
                    group_id INTEGER NOT NULL REFERENCES chat_groups(id),
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    role VARCHAR(20) DEFAULT 'member',
                    joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                '''))
            print("  ✅ chat_group_members created")

        if 'chat_messages' not in existing_tables:
            if engine.dialect.name == 'sqlite':
                conn.execute(text('''
                CREATE TABLE chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender_id INTEGER NOT NULL,
                    group_id INTEGER,
                    receiver_id INTEGER,
                    content TEXT NOT NULL,
                    message_type TEXT DEFAULT 'text',
                    is_read BOOLEAN DEFAULT 0,
                    has_attachment BOOLEAN DEFAULT 0,
                    attachment_path TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
                '''))
            else:
                conn.execute(text('''
                CREATE TABLE chat_messages (
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
                '''))
            print("  ✅ chat_messages created")

    print("✅ Chat tables ensured")


if __name__ == '__main__':
    migrate_with_sqlalchemy()

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
