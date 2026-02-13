#!/usr/bin/env python3
"""
Vernika RLS Migration Script
Run this to enable Row Level Security on all Supabase tables

Usage:
    python3 scripts/enable_rls.py                    # Interactive mode
    python3 scripts/enable_rls.py --dry-run         # Preview without changes
    python3 scripts/enable_rls.py --env .env        # Use custom .env file
"""

from psycopg2 import sql
import psycopg2
from dotenv import load_dotenv
import os
import sys
from pathlib import Path
from typing import Optional

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))


def get_connection_string() -> str:
    """Get database connection string from environment"""
    load_dotenv()

    # Check for DATABASE_URL first
    database_url = os.getenv("DATABASE_URL", "")
    if database_url:
        return database_url

    # Build from individual components
    host = os.getenv("DB_HOST", "")
    port = os.getenv("DB_PORT", "5432")
    dbname = os.getenv("DB_NAME", "postgres")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "")

    if not host:
        raise ValueError("No DATABASE_URL or DB_HOST found in environment")

    return f"postgresql://{user}:{password}@{host}:{port}/{dbname}"


def get_action_from_statement(stmt: str) -> str:
    """Extract a human-readable action from a SQL statement"""
    for line in stmt.split('\n'):
        stripped = line.strip()
        if not stripped or stripped.startswith('--'):
            continue
        if 'ALTER TABLE' in stripped.upper():
            parts = stripped.split()
            if len(parts) >= 3:
                return f"Enable RLS on {parts[2]}"
        elif 'CREATE POLICY' in stripped.upper():
            parts = stripped.split('"')
            if len(parts) >= 2:
                return f"Create policy: {parts[1]}"
            return "Create policy"
        elif 'CREATE OR REPLACE VIEW' in stripped.upper():
            parts = stripped.split()
            for i, p in enumerate(parts):
                if p.upper() == 'VIEW':
                    if i + 1 < len(parts):
                        return f"Create view: {parts[i + 1]}"
            return "Create view"
        elif 'CREATE OR REPLACE FUNCTION' in stripped.upper():
            return "Create function"
        elif 'CREATE FUNCTION' in stripped.upper():
            return "Create function"
        elif 'GRANT' in stripped.upper():
            return f"Grant: {stripped}"
        elif 'REVOKE' in stripped.upper():
            return f"Revoke: {stripped}"
        elif 'CREATE INDEX' in stripped.upper():
            return f"Create index"
        elif 'COMMENT ON VIEW' in stripped.upper():
            return "Add view comment"
    return "Unknown"


def strip_sql_comments(text: str) -> str:
    """
    Strip SQL comments from text while preserving dollar-quoted strings.
    Only strips full-line comments, not inline comments.
    """
    lines = []
    dollar_depth = 0

    for line in text.split('\n'):
        stripped = line.strip()

        # Track dollar quote state
        has_opening = '$$' in stripped and not stripped.startswith('$$')
        has_closing = stripped.startswith('$$') and 'LANGUAGE' in stripped

        if has_opening:
            dollar_depth += 1
        elif has_closing and dollar_depth > 0:
            dollar_depth -= 1

        # Only skip full-line comments that are NOT inside dollar quotes
        if dollar_depth == 0 and stripped.startswith('--'):
            continue

        lines.append(line)

    return '\n'.join(lines)


def split_sql_statements(content: str) -> list:
    """
    Split SQL content into individual statements, handling dollar-quoted strings.

    PostgreSQL dollar-quoted functions have $$ delimiters:
    - Opening: line contains "AS $$" or "$$" followed by content
    - Closing: line starts with "$$" (followed by LANGUAGE)
    """
    statements = []
    current = []
    dollar_depth = 0

    for line in content.split('\n'):
        stripped = line.strip()

        # Track dollar quote depth
        has_opening = '$$' in stripped and not stripped.startswith('$$')
        has_closing = stripped.startswith('$$') and 'LANGUAGE' in stripped

        if has_opening:
            dollar_depth += 1
        elif has_closing and dollar_depth > 0:
            dollar_depth -= 1

        current.append(line)

        # Only split on semicolon when NOT inside dollar quotes
        if dollar_depth == 0 and stripped.endswith(';'):
            stmt = strip_sql_comments('\n'.join(current)).strip()
            if stmt:
                statements.append(stmt)
            current = []

    # Handle any remaining content
    if current:
        stmt = strip_sql_comments('\n'.join(current)).strip()
        if stmt:
            statements.append(stmt)

    return statements


def run_migration(dry_run: bool = True, verbose: bool = False):
    """
    Run the RLS migration script
    """
    sql_file = Path(__file__).parent / "supabase_rls_migration.sql"

    if not sql_file.exists():
        print(f"[ERROR] SQL migration file not found: {sql_file}")
        return False

    print("=" * 70)
    print("Vernika HRA - RLS Security Migration")
    print("=" * 70)

    # Read the SQL file
    with open(sql_file, 'r') as f:
        sql_content = f.read()

    # Split into individual statements
    statements = split_sql_statements(sql_content)

    # Get connection string
    try:
        conn_string = get_connection_string()
    except ValueError as e:
        print(f"[ERROR] {e}")
        print("\nTo configure Supabase:")
        print("1. Copy .env.example to .env")
        print("2. Add your DATABASE_URL or DB_* settings")
        print("3. Get your credentials from: https://supabase.com/dashboard")
        return False

    mode = "DRY RUN" if dry_run else "LIVE"
    print(f"\n[MODE] {mode}")
    print(f"[DB] {conn_string[:50]}...")

    if dry_run:
        print(
            f"\n[PREVIEW] {len(statements)} SQL statements would be executed:")
        for i, stmt in enumerate(statements, 1):
            action = get_action_from_statement(stmt)
            print(f"  {i}. {action}")

        print("\n" + "=" * 70)
        print("[INFO] Run without --dry-run to apply changes")
        return True

    # Connect and execute
    print(f"\n[CONNECTING] To database...")
    try:
        conn = psycopg2.connect(conn_string)
        conn.autocommit = False
        cursor = conn.cursor()

        print("[OK] Connected successfully\n")

        # Execute each statement
        success_count = 0
        error_count = 0
        errors = []

        for i, stmt in enumerate(statements, 1):
            try:
                cursor.execute(stmt)
                if verbose:
                    action = get_action_from_statement(stmt)
                    print(f"  [OK] {i}/{len(statements)}: {action}")
                success_count += 1
            except Exception as e:
                error_count += 1
                error_msg = str(e).strip()
                errors.append(f"Statement {i}: {error_msg}")
                print(f"  [ERROR] {i}/{len(statements)}: {error_msg}")

        # Commit changes
        conn.commit()
        print("\n" + "=" * 70)
        print(f"[RESULT] {success_count} statements executed successfully")

        if error_count > 0:
            print(f"[WARN] {error_count} statements had errors")
            for error in errors[:10]:
                print(f"  - {error}")
            if len(errors) > 10:
                print(f"  ... and {len(errors) - 10} more errors")

        cursor.close()
        conn.close()

        return error_count == 0

    except Exception as e:
        print(f"[ERROR] Database connection failed: {e}")
        print("\nTroubleshooting:")
        print("1. Check your .env file has correct DATABASE_URL")
        print("2. Ensure your IP is whitelisted in Supabase")
        print("3. Verify the database password is correct")
        return False


def verify_rls():
    """Verify RLS is properly configured"""
    print("\n" + "=" * 70)
    print("Verifying RLS Configuration")
    print("=" * 70)

    try:
        conn_string = get_connection_string()
    except ValueError as e:
        print(f"[ERROR] {e}")
        return False

    try:
        conn = psycopg2.connect(conn_string)
        cursor = conn.cursor()

        # Check RLS enabled tables
        cursor.execute("""
            SELECT tablename, row_security_enabled
            FROM pg_tables
            WHERE schemaname = 'public'
            ORDER BY tablename
        """)
        tables = cursor.fetchall()

        print("\n[RLS Status on Tables]")
        print("-" * 50)
        rls_enabled = 0
        rls_disabled = 0

        for table, enabled in tables:
            status = "RLS" if enabled else "NO RLS"
            print(f"  {status:10} | {table}")
            if enabled:
                rls_enabled += 1
            else:
                rls_disabled += 1

        print(f"\n[TOTAL] {rls_enabled} enabled, {rls_disabled} disabled")

        # Check policies
        cursor.execute("""
            SELECT tablename, COUNT(*) as policy_count
            FROM pg_policies
            WHERE schemaname = 'public'
            GROUP BY tablename
            ORDER BY tablename
        """)
        policies = cursor.fetchall()

        print("\n[Policies per Table]")
        print("-" * 50)
        total_policies = 0
        for table, count in policies:
            print(f"  {count:3} policies | {table}")
            total_policies += count
        print(f"\n[TOTAL] {total_policies} policies")

        # Check views
        cursor.execute(r"""
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            AND tablename LIKE '%%_safe'
        """)
        views = cursor.fetchall()

        print("\n[Safe Views Created]")
        print("-" * 50)
        for (view,) in views:
            print(f"  {view}")

        cursor.close()
        conn.close()

        return True

    except Exception as e:
        print(f"[ERROR] Verification failed: {e}")
        return False


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Enable Row Level Security on Vernika Supabase tables"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without applying them"
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify RLS configuration (no migration)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show detailed output"
    )
    parser.add_argument(
        "--env",
        default=".env",
        help="Path to .env file (default: .env)"
    )

    args = parser.parse_args()

    # Load environment
    if os.path.exists(args.env):
        load_dotenv(args.env)
        print(f"[LOADED] Environment from {args.env}")

    # If verify only
    if args.verify:
        verify_rls()
        return

    # Run migration
    success = run_migration(dry_run=args.dry_run, verbose=args.verbose)

    if success and not args.dry_run:
        print("\n" + "=" * 70)
        print("[SUCCESS] RLS migration completed!")
        print("\n[RECOMMENDED NEXT STEPS]")
        print("  1. Run verification: python3 scripts/enable_rls.py --verify")
        print("  2. Test the application with different user roles")
        print("  3. Review the safe views: employees_safe, users_safe")
        print("=" * 70)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
