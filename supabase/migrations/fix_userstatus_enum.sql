-- ===================================================================
-- Fix userstatus enum cast in get_dashboard_statistics function
-- The function was failing because it used string 'active' but the 
-- users.status column is an enum type (userstatus)
-- ===================================================================

BEGIN;

-- Drop and recreate the function with proper enum casting
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
        -- Fix: Cast 'active' string to userstatus enum
        (SELECT COUNT(*) FROM users WHERE status = 'active'::userstatus)::BIGINT as active_users,
        (SELECT COUNT(*) FROM employees)::BIGINT as total_employees,
        (SELECT COUNT(*) FROM employees WHERE is_active = true)::BIGINT as active_employees,
        (SELECT COUNT(*) FROM departments WHERE is_active = true)::BIGINT as departments_count,
        (SELECT COUNT(*) FROM positions WHERE is_active = true)::BIGINT as positions_count,
        -- Fix: Cast attendance status strings to enum
        (SELECT COUNT(*) FROM attendances WHERE date = current_date AND status = 'present'::attendancestatus)::BIGINT as present_today,
        (SELECT COUNT(*) FROM attendances WHERE date = current_date AND status = 'absent'::attendancestatus)::BIGINT as absent_today,
        -- Fix: Cast leave status strings to enum
        (SELECT COUNT(*) FROM leave_requests WHERE status = 'approved'::leavestatus AND start_date <= current_date AND end_date >= current_date)::BIGINT as on_leave_today,
        (SELECT COUNT(*) FROM leave_requests WHERE status = 'pending'::leavestatus)::BIGINT as pending_leaves,
        -- Fix: Cast task status strings to enum
        (SELECT COUNT(*) FROM tasks WHERE status = 'todo'::taskstatus)::BIGINT as pending_tasks,
        (SELECT COUNT(*) FROM tasks WHERE status = 'in_progress'::taskstatus)::BIGINT as in_progress_tasks,
        (SELECT COUNT(*) FROM tasks WHERE status = 'completed'::taskstatus)::BIGINT as completed_tasks;
END;
$$ LANGUAGE plpgsql;

-- Also update get_today_attendance_summary function
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
        (SELECT COUNT(*) FROM attendances WHERE date = current_date AND status = 'present'::attendancestatus)::BIGINT as present_count,
        (SELECT COUNT(*) FROM attendances WHERE date = current_date AND status = 'absent'::attendancestatus)::BIGINT as absent_count,
        (SELECT COUNT(*) FROM attendances WHERE date = current_date AND status = 'late'::attendancestatus)::BIGINT as late_count,
        (SELECT COUNT(*) FROM leave_requests WHERE status = 'approved'::leavestatus AND start_date <= current_date AND end_date >= current_date)::BIGINT as on_leave_count,
        (SELECT COUNT(*) FROM attendances WHERE date = current_date AND status = 'half_day'::attendancestatus)::BIGINT as half_day_count;
END;
$$ LANGUAGE plpgsql;

COMMIT;

-- Verification
SELECT 'User status enum fix applied successfully!' as status;

