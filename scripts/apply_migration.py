#!/usr/bin/env python3
"""
Script to apply the userstatus enum fix migration
Run this script to fix the dashboard statistics function
"""

from database.connection import get_engine
from sqlalchemy import text
import os
import sys
from pathlib import Path

# Add parent directory to path (required for imports)
sys.path.insert(0, '/Users/shashankrajput/Desktop/RadheFoundation')


def apply_enum_fix():
    """Apply the userstatus enum fix migration"""

    engine = get_engine()

    # SQL to fix the function
    fix_sql = """
CREATE OR REPLACE FUNCTION get_dashboard_statistics()
RETURNS TABLE (
    total_users BIGINT,
    active_users BIGINT,
    total_employees BIGINT,
    active_employees BIGINT,
    departments_count BIGINT,
    positions_count BIGINT,
    present_today BIGINT,
    absent_today BIGINT,
    on_leave_today BIGINT,
    pending_leaves BIGINT,
    pending_tasks BIGINT,
    in_progress_tasks BIGINT,
    completed_tasks BIGINT
) AS $$
DECLARE
    current_date DATE := CURRENT_DATE;
BEGIN
    RETURN QUERY
    SELECT 
        (SELECT COUNT(*) FROM users)::BIGINT as total_users,
        -- Fix: Cast 'ACTIVE' string to userstatus enum (uppercase)
        (SELECT COUNT(*) FROM users WHERE status = 'ACTIVE'::userstatus)::BIGINT as active_users,
        (SELECT COUNT(*) FROM employees)::BIGINT as total_employees,
        (SELECT COUNT(*) FROM employees WHERE is_active = true)::BIGINT as active_employees,
        (SELECT COUNT(*) FROM departments WHERE is_active = true)::BIGINT as departments_count,
        (SELECT COUNT(*) FROM positions WHERE is_active = true)::BIGINT as positions_count,
        -- Fix: Cast attendance status strings to enum (uppercase)
        (SELECT COUNT(*) FROM attendances WHERE date = current_date AND status = 'PRESENT'::attendancestatus)::BIGINT as present_today,
        (SELECT COUNT(*) FROM attendances WHERE date = current_date AND status = 'ABSENT'::attendancestatus)::BIGINT as absent_today,
        -- Fix: Cast leave status strings to enum (uppercase)
        (SELECT COUNT(*) FROM leave_requests WHERE status = 'APPROVED'::leavestatus AND start_date <= current_date AND end_date >= current_date)::BIGINT as on_leave_today,
        (SELECT COUNT(*) FROM leave_requests WHERE status = 'PENDING'::leavestatus)::BIGINT as pending_leaves,
        -- Fix: Cast task status strings to enum (uppercase with underscore)
        (SELECT COUNT(*) FROM tasks WHERE status = 'TODO'::taskstatus)::BIGINT as pending_tasks,
        (SELECT COUNT(*) FROM tasks WHERE status = 'IN_PROGRESS'::taskstatus)::BIGINT as in_progress_tasks,
        (SELECT COUNT(*) FROM tasks WHERE status = 'COMPLETED'::taskstatus)::BIGINT as completed_tasks;
END;
$$ LANGUAGE plpgsql;
"""

    # Also fix get_today_attendance_summary
    attendance_sql = """
CREATE OR REPLACE FUNCTION get_today_attendance_summary()
RETURNS TABLE (
    total_employees BIGINT,
    present_count BIGINT,
    absent_count BIGINT,
    late_count BIGINT,
    on_leave_count BIGINT,
    half_day_count BIGINT
) AS $$
DECLARE
    current_date DATE := CURRENT_DATE;
BEGIN
    RETURN QUERY
    SELECT 
        (SELECT COUNT(*) FROM employees WHERE is_active = true)::BIGINT as total_employees,
        (SELECT COUNT(*) FROM attendances WHERE date = current_date AND status = 'PRESENT'::attendancestatus)::BIGINT as present_count,
        (SELECT COUNT(*) FROM attendances WHERE date = current_date AND status = 'ABSENT'::attendancestatus)::BIGINT as absent_count,
        (SELECT COUNT(*) FROM attendances WHERE date = current_date AND status = 'LATE'::attendancestatus)::BIGINT as late_count,
        (SELECT COUNT(*) FROM leave_requests WHERE status = 'APPROVED'::leavestatus AND start_date <= current_date AND end_date >= current_date)::BIGINT as on_leave_count,
        (SELECT COUNT(*) FROM attendances WHERE date = current_date AND status = 'HALF_DAY'::attendancestatus)::BIGINT as half_day_count;
END;
$$ LANGUAGE plpgsql;
"""

    try:
        with engine.begin() as conn:
            print("Applying dashboard statistics function fix...")
            conn.execute(text(fix_sql))
            print("✅ Fixed get_dashboard_statistics() function")

            print("Applying attendance summary function fix...")
            conn.execute(text(attendance_sql))
            print("✅ Fixed get_today_attendance_summary() function")

        print("\n✅ Migration applied successfully!")
        return True

    except Exception as e:
        print(f"\n❌ Error applying migration: {e}")
        return False


if __name__ == "__main__":
    print("="*60)
    print("RadheFoundation - User Status Enum Fix Migration")
    print("="*60)

    success = apply_enum_fix()

    if success:
        # Test the function
        print("\nTesting the fixed function...")
        try:
            engine = get_engine()
            with engine.connect() as conn:
                result = conn.execute(
                    text("SELECT * FROM get_dashboard_statistics()"))
                row = result.fetchone()
                print(f"✅ Function test successful!")
                print(
                    f"   Result: total_users={row[0]}, active_users={row[1]}")
        except Exception as e:
            print(f"⚠️  Function test failed: {e}")

    sys.exit(0 if success else 1)
