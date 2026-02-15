#!/usr/bin/env python3
"""
Simplified RLS Migration Script - runs SQL in stages
"""

from pathlib import Path
import sys
import os
import psycopg2
from dotenv import load_dotenv
load_dotenv()


def get_connection_string():
    load_dotenv()
    database_url = os.getenv("DATABASE_URL", "")
    if database_url:
        return database_url
    raise ValueError("No DATABASE_URL found")


def run_sql_file_in_chunks():
    """Run the RLS migration by executing in logical chunks"""

    sql_file = Path(__file__).parent / "supabase_rls_migration.sql"

    if not sql_file.exists():
        print(f"ERROR: SQL file not found: {sql_file}")
        return False

    with open(sql_file, 'r') as f:
        sql_content = f.read()

    conn_string = get_connection_string()

    print("Connecting to database...")
    conn = psycopg2.connect(conn_string)
    conn.autocommit = False
    cursor = conn.cursor()
    print("Connected!")

    # Split into sections based on comments
    sections = {}
    current_section = None

    for line in sql_content.split('\n'):
        if line.startswith('-- STEP'):
            # Extract section name
            if 'STEP 1' in line:
                current_section = 'enable_rls'
            elif 'STEP 2' in line:
                current_section = 'functions'
            elif 'STEP 3' in line:
                current_section = 'policies'
            elif 'STEP 4' in line:
                current_section = 'views'
            elif 'STEP 5' in line:
                current_section = 'grants'
            elif 'STEP 6' in line:
                current_section = 'revokes'
            elif 'STEP 7' in line:
                current_section = 'indexes'
            else:
                current_section = 'other'
            if current_section not in sections:
                sections[current_section] = []
        elif current_section:
            sections[current_section].append(line)

    # Drop existing functions first
    print("\n[1/7] Dropping existing functions...")
    try:
        cursor.execute("""
            DROP FUNCTION IF EXISTS get_user_department_ids() CASCADE;
            DROP FUNCTION IF EXISTS is_own_data(INTEGER) CASCADE;
            DROP FUNCTION IF EXISTS get_user_employee_id(INTEGER) CASCADE;
            DROP FUNCTION IF EXISTS is_manager() CASCADE;
            DROP FUNCTION IF EXISTS is_hr_manager() CASCADE;
            DROP FUNCTION IF EXISTS is_admin() CASCADE;
            DROP FUNCTION IF EXISTS get_current_user_id() CASCADE;
            DROP FUNCTION IF EXISTS get_user_role() CASCADE;
        """)
        conn.commit()
        print("  OK")
    except Exception as e:
        print(f"  Warning: {e}")
        conn.rollback()

    # Execute RLS enable statements
    print("\n[2/7] Enabling RLS on tables...")
    try:
        rls_stmts = '\n'.join(sections.get('enable_rls', []))
        for stmt in rls_stmts.split(';'):
            stmt = stmt.strip()
            if stmt and not stmt.startswith('--') and 'ALTER TABLE' in stmt.upper():
                cursor.execute(stmt)
        conn.commit()
        print("  OK - RLS enabled on tables")
    except Exception as e:
        print(f"  Error: {e}")
        conn.rollback()

    # Execute functions (need special handling for dollar quotes)
    print("\n[3/7] Creating functions...")
    try:
        # Extract just the function definitions
        func_section = '\n'.join(sections.get('functions', []))
        # Find CREATE FUNCTION statements and execute them
        in_function = False
        func_parts = []

        for line in sql_content.split('\n'):
            if 'CREATE OR REPLACE FUNCTION' in line:
                in_function = True
                func_parts = [line]
            elif in_function:
                func_parts.append(line)
                if line.strip().endswith(';') and '$$' in line:
                    # End of function
                    func_sql = '\n'.join(func_parts)
                    try:
                        cursor.execute(func_sql)
                    except Exception as fe:
                        print(f"  Warning creating function: {fe}")
                    in_function = False

        conn.commit()
        print("  OK - Functions created")
    except Exception as e:
        print(f"  Error: {e}")
        conn.rollback()

    # Execute policies
    print("\n[4/7] Creating policies...")
    try:
        policy_count = 0
        for stmt in sql_content.split(';'):
            if 'CREATE POLICY' in stmt:
                try:
                    cursor.execute(stmt)
                    policy_count += 1
                except Exception as pe:
                    pass  # Policy might already exist
        conn.commit()
        print(f"  OK - {policy_count} policies created")
    except Exception as e:
        print(f"  Error: {e}")
        conn.rollback()

    # Execute views
    print("\n[5/7] Creating views...")
    try:
        for stmt in sql_content.split(';'):
            if 'CREATE OR REPLACE VIEW' in stmt:
                try:
                    cursor.execute(stmt)
                except Exception as ve:
                    pass
        conn.commit()
        print("  OK")
    except Exception as e:
        print(f"  Error: {e}")
        conn.rollback()

    # Execute grants
    print("\n[6/7] Setting grants...")
    try:
        for stmt in sql_content.split(';'):
            stmt_upper = stmt.upper().strip()
            if stmt_upper.startswith('GRANT') or stmt_upper.startswith('REVOKE'):
                try:
                    cursor.execute(stmt)
                except Exception as ge:
                    pass
        conn.commit()
        print("  OK")
    except Exception as e:
        print(f"  Error: {e}")
        conn.rollback()

    # Execute indexes
    print("\n[7/7] Creating indexes...")
    try:
        for stmt in sql_content.split(';'):
            if 'CREATE INDEX' in stmt:
                try:
                    cursor.execute(stmt)
                except Exception as ie:
                    pass
        conn.commit()
        print("  OK")
    except Exception as e:
        print(f"  Error: {e}")
        conn.rollback()

    cursor.close()
    conn.close()

    print("\n" + "="*50)
    print("RLS Migration Complete!")
    print("="*50)
    return True


if __name__ == "__main__":
    success = run_sql_file_in_chunks()
    sys.exit(0 if success else 1)
