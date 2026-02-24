#!/usr/bin/env python3
"""
Vernika - Email Groups Migration Script

Creates email_groups and email_group_members tables
for email distribution lists functionality.
"""

from sqlalchemy import text, inspect
from database.connection import get_engine
import os
import sys

# Add project root to path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)


def migrate_email_groups():
    """Create email_groups and email_group_members tables"""
    engine = get_engine()
    dialect = engine.dialect.name
    print(f"Using database dialect: {dialect}")

    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    print(f"Existing tables: {existing_tables}")

    with engine.begin() as conn:
        # Create email_groups table
        if 'email_groups' not in existing_tables:
            print("Creating email_groups table...")
            if dialect == 'sqlite':
                conn.execute(text('''
                    CREATE TABLE email_groups (
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
                    CREATE TABLE email_groups (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(100) NOT NULL,
                        description TEXT,
                        created_by INTEGER NOT NULL REFERENCES users(id),
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                '''))
            print("  ✅ email_groups table created")
        else:
            print("  ℹ️ email_groups table already exists")

        # Create email_group_members table
        if 'email_group_members' not in existing_tables:
            print("Creating email_group_members table...")
            if dialect == 'sqlite':
                conn.execute(text('''
                    CREATE TABLE email_group_members (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        group_id INTEGER NOT NULL,
                        user_id INTEGER NOT NULL,
                        role TEXT DEFAULT 'member',
                        joined_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (group_id) REFERENCES email_groups(id),
                        FOREIGN KEY (user_id) REFERENCES users(id)
                    )
                '''))
            else:
                conn.execute(text('''
                    CREATE TABLE email_group_members (
                        id SERIAL PRIMARY KEY,
                        group_id INTEGER NOT NULL REFERENCES email_groups(id),
                        user_id INTEGER NOT NULL REFERENCES users(id),
                        role VARCHAR(20) DEFAULT 'member',
                        joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                '''))
            print("  ✅ email_group_members table created")
        else:
            print("  ℹ️ email_group_members table already exists")

        # Create indexes
        print("Creating indexes...")
        try:
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_email_groups_created_by ON email_groups(created_by)"))
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_email_group_members_group ON email_group_members(group_id)"))
            conn.execute(text(
                "CREATE INDEX IF NOT EXISTS idx_email_group_members_user ON email_group_members(user_id)"))
            print("  ✅ Indexes created")
        except Exception as e:
            print(f"  ℹ️ Indexes may already exist: {e}")

    print("\n✅ Email groups migration completed successfully!")


if __name__ == "__main__":
    print("=" * 60)
    print("🔧 Vernika Email Groups Migration")
    print("=" * 60)
    migrate_email_groups()
    print("=" * 60)
