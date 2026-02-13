#!/usr/bin/env python3
"""
Vernika HRA - Database Schema Sync & Fix Script
This script syncs the PostgreSQL database schema and fixes all issues.
"""

from config import DATABASE_URL
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine, text, inspect
import os
import sys

# Set working directory
os.chdir('/Users/shashankrajput/Desktop/Vernika')

# Add to path
sys.path.insert(0, '/Users/shashankrajput/Desktop/Vernika')


def get_engine():
    return create_engine(DATABASE_URL)


def sync_schema():
    """Sync the database schema with Supabase"""
    print("=" * 60)
    print("Database Schema Sync - PostgreSQL (Supabase)")
    print("=" * 60)

    engine = get_engine()
    inspector = inspect(engine)

    # Get existing tables
    existing_tables = inspector.get_table_names()
    print(f"\nExisting tables in database: {len(existing_tables)}")
    for t in existing_tables:
        print(f"  - {t}")

    # Import all models to create them
    from database.models import Base

    # Create all missing tables
    print("\n[1] Creating missing tables...")
    Base.metadata.create_all(engine)
    print("  ✓ Tables created/verified")

    # Now fix any schema issues
    fix_schema_issues(engine)

    print("\n" + "=" * 60)
    print("✅ Schema sync complete!")
    print("=" * 60)


def fix_schema_issues(engine):
    """Fix schema issues in PostgreSQL"""
    print("\n[2] Fixing schema issues...")

    with engine.connect() as conn:
        # Fix: Add missing columns that exist in SQLite but not in PostgreSQL

        # Check and add columns for employees table
        try:
            result = conn.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_name = 'employees'"))
            existing_cols = [row[0] for row in result]

            # Add profile_photo if missing
            if 'profile_photo' not in existing_cols:
                conn.execute(
                    text("ALTER TABLE employees ADD COLUMN profile_photo TEXT"))
                print("  ✓ Added profile_photo to employees")

            # Add updated_at if missing
            if 'updated_at' not in existing_cols:
                conn.execute(
                    text("ALTER TABLE employees ADD COLUMN updated_at TIMESTAMP"))
                print("  ✓ Added updated_at to employees")

        except Exception as e:
            print(f"  ⚠ employees table issue: {e}")

        # Check and add columns for departments table
        try:
            result = conn.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_name = 'departments'"))
            existing_cols = [row[0] for row in result]

            new_cols = [
                ('budget', 'INTEGER DEFAULT 500000'),
                ('location', 'TEXT'),
                ('contact_email', 'TEXT'),
                ('contact_phone', 'TEXT'),
                ('parent_dept_id', 'INTEGER'),
                ('updated_at', 'TIMESTAMP')
            ]

            for col_name, col_type in new_cols:
                if col_name not in existing_cols:
                    conn.execute(
                        text(f"ALTER TABLE departments ADD COLUMN {col_name} {col_type}"))
                    print(f"  ✓ Added {col_name} to departments")

        except Exception as e:
            print(f"  ⚠ departments table issue: {e}")

        # Check and add columns for positions table
        try:
            result = conn.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_name = 'positions'"))
            existing_cols = [row[0] for row in result]

            if 'updated_at' not in existing_cols:
                conn.execute(
                    text("ALTER TABLE positions ADD COLUMN updated_at TIMESTAMP"))
                print("  ✓ Added updated_at to positions")

        except Exception as e:
            print(f"  ⚠ positions table issue: {e}")

        # Check and add columns for tasks table
        try:
            result = conn.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_name = 'tasks'"))
            existing_cols = [row[0] for row in result]

            new_cols = [
                ('category', 'TEXT'),
                ('project_name', 'TEXT'),
                ('estimated_hours', 'FLOAT'),
                ('actual_hours', 'FLOAT'),
                ('start_date', 'INTEGER'),
                ('end_date', 'INTEGER'),
                ('task_type', 'TEXT'),
                ('attachments', 'TEXT'),
                ('time_spent', 'INTEGER'),
                ('updated_at', 'TIMESTAMP')
            ]

            for col_name, col_type in new_cols:
                if col_name not in existing_cols:
                    conn.execute(
                        text(f"ALTER TABLE tasks ADD COLUMN {col_name} {col_type}"))
                    print(f"  ✓ Added {col_name} to tasks")

        except Exception as e:
            print(f"  ⚠ tasks table issue: {e}")

        # Check and add columns for chat_messages table
        try:
            result = conn.execute(text(
                "SELECT column_name FROM information_schema.columns WHERE table_name = 'chat_messages'"))
            existing_cols = [row[0] for row in result]

            if 'message_type' not in existing_cols:
                conn.execute(
                    text("ALTER TABLE chat_messages ADD COLUMN message_type TEXT DEFAULT 'text'"))
                print("  ✓ Added message_type to chat_messages")

        except Exception as e:
            print(f"  ⚠ chat_messages table issue: {e}")

        # Create teams table if missing
        try:
            result = conn.execute(text(
                "SELECT table_name FROM information_schema.tables WHERE table_name = 'teams'"))
            if not result.fetchone():
                conn.execute(text("""
                    CREATE TABLE teams (
                        id SERIAL PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT,
                        department_id INTEGER,
                        team_lead_id INTEGER,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        is_active BOOLEAN DEFAULT true
                    )
                """))
                print("  ✓ Created teams table")
        except Exception as e:
            print(f"  ⚠ teams table issue: {e}")

        # Create announcements table if missing
        try:
            result = conn.execute(text(
                "SELECT table_name FROM information_schema.tables WHERE table_name = 'announcements'"))
            if not result.fetchone():
                conn.execute(text("""
                    CREATE TABLE announcements (
                        id SERIAL PRIMARY KEY,
                        title TEXT NOT NULL,
                        content TEXT,
                        type TEXT DEFAULT 'general',
                        priority TEXT DEFAULT 'normal',
                        author TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        views INTEGER DEFAULT 0
                    )
                """))
                print("  ✓ Created announcements table")
        except Exception as e:
            print(f"  ⚠ announcements table issue: {e}")

        conn.commit()

    print("  ✓ Schema issues fixed")


def fix_screen_access():
    """Fix screen access table"""
    print("\n[3] Fixing screen access...")

    engine = get_engine()

    with engine.connect() as conn:
        # Ensure screen_access table has proper structure
        try:
            # Check if is_enabled is boolean or integer
            result = conn.execute(text("""
                SELECT data_type 
                FROM information_schema.columns 
                WHERE table_name = 'screen_access' AND column_name = 'is_enabled'
            """))
            row = result.fetchone()
            if row and row[0] != 'boolean':
                # Convert to boolean
                conn.execute(
                    text("ALTER TABLE screen_access ALTER COLUMN is_enabled TYPE BOOLEAN"))
                print("  ✓ Fixed screen_access is_enabled type")
        except Exception as e:
            print(f"  ⚠ {e}")

        conn.commit()

    print("  ✓ Screen access fixed")


def verify_connection():
    """Verify database connection"""
    print("\n[4] Verifying database connection...")

    try:
        engine = get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()
            print(f"  ✓ Connected to: {version[0][:50]}...")

            # Count tables
            result = conn.execute(text(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"))
            count = result.fetchone()[0]
            print(f"  ✓ Total tables: {count}")

        return True
    except Exception as e:
        print(f"  ✗ Connection failed: {e}")
        return False


def main():
    print("\n🔄 Starting Database Schema Sync...\n")

    if not verify_connection():
        print("\n❌ Cannot connect to database. Please check your configuration.")
        sys.exit(1)

    sync_schema()
    fix_screen_access()

    print("\n" + "=" * 60)
    print("✅ All database fixes complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Run: python3 main.py")
    print("  2. Test the application")
    print("=" * 60)


if __name__ == "__main__":
    main()
