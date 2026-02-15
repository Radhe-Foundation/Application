#!/usr/bin/env python3
"""Verify RLS is properly configured"""

import os
import psycopg2
from dotenv import load_dotenv
load_dotenv()


def verify_rls():
    conn_string = os.getenv("DATABASE_URL")

    print("=" * 60)
    print("RLS Configuration Verification")
    print("=" * 60)

    conn = psycopg2.connect(conn_string)
    cursor = conn.cursor()

    # Check RLS enabled tables
    print("\n[RLS Status on Tables]")
    print("-" * 50)
    cursor.execute("""
        SELECT relname, relrowsecurity
        FROM pg_class
        WHERE relnamespace = 'public'::regnamespace
        AND relkind = 'r'
        AND relname NOT LIKE 'pg_%'
        AND relname NOT LIKE 'sql_%'
        ORDER BY relname
    """)
    tables = cursor.fetchall()

    rls_enabled = 0
    rls_disabled = 0

    for table, enabled in tables:
        status = "RLS ✓" if enabled else "NO RLS"
        print(f"  {status:10} | {table}")
        if enabled:
            rls_enabled += 1
        else:
            rls_disabled += 1

    print(f"\n[TOTAL] {rls_enabled} enabled, {rls_disabled} disabled")

    # Check policies
    print("\n[Policies Count]")
    print("-" * 50)
    cursor.execute("""
        SELECT tablename, COUNT(*) as policy_count
        FROM pg_policies
        WHERE schemaname = 'public'
        GROUP BY tablename
        ORDER BY tablename
    """)
    policies = cursor.fetchall()

    total_policies = 0
    for table, count in policies:
        print(f"  {count:3} policies | {table}")
        total_policies += count
    print(f"\n[TOTAL] {total_policies} policies")

    # Check views
    print("\n[Safe Views]")
    print("-" * 50)
    cursor.execute("""
        SELECT viewname
        FROM pg_views
        WHERE schemaname = 'public'
        AND viewname IN ('employees_safe', 'users_safe')
    """)
    views = cursor.fetchall()

    for (view,) in views:
        print(f"  ✓ {view}")

    # Check functions
    print("\n[RLS Functions]")
    print("-" * 50)
    cursor.execute("""
        SELECT proname
        FROM pg_proc
        WHERE proname IN ('get_user_role', 'is_admin', 'is_hr_manager', 
                        'is_manager', 'get_user_department_ids', 'is_own_data',
                        'get_user_employee_id', 'get_current_user_id')
        AND pronamespace = 'public'::regnamespace
    """)
    funcs = cursor.fetchall()

    for (name,) in funcs:
        print(f"  ✓ {name}")

    cursor.close()
    conn.close()

    print("\n" + "=" * 60)
    print("Verification Complete!")
    print("=" * 60)


if __name__ == "__main__":
    verify_rls()
