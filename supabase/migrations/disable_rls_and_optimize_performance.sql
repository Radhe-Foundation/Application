-- ===================================================================
-- Vernika HR Application - Performance Optimization Migration
-- This migration disables RLS and adds comprehensive indexes
-- for maximum database performance
-- ===================================================================

BEGIN;

-- ===================================================================
-- STEP 1: Disable RLS on all tables for performance
-- ===================================================================

-- Disable RLS on core tables
ALTER TABLE IF EXISTS users DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS roles DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS companies DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS departments DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS teams DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS positions DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS employees DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS attendances DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS leave_type_configs DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS leave_balances DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS leave_requests DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS tasks DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS task_comments DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS audit_logs DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS messages DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS time_off_requests DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS chat_groups DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS chat_group_members DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS chat_messages DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS email_messages DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS email_recipients DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS email_groups DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS email_group_members DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS meetings DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS meeting_participants DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS call_logs DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS app_notifications DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS documents DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS user_permissions DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS screen_access DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS button_access DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS org_hierarchy DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS team_members DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS project_members DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS projects DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS inventory_categories DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS products DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS product_images DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS inventory_transactions DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS suppliers DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS transactions DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS transaction_attachments DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS data_sheets DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS data_sheet_columns DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS data_sheet_rows DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS timesheets DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS time_entries DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS billing_requests DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS billing_request_attachments DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS crm_leads DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS crm_contacts DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS calendar_events DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS warehouses DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS assets DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS contracts DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS invoices DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS invoice_items DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS etl_projects DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS etl_datasets DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS etl_transformations DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS company_documents DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS holidays DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS todo_items DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS app_settings DISABLE ROW LEVEL SECURITY;
ALTER TABLE IF EXISTS announcements DISABLE ROW LEVEL SECURITY;

-- ===================================================================
-- STEP 2: Drop existing RLS policies (cleanup)
-- ===================================================================

DROP POLICY IF EXISTS "Users can view own data" ON users;
DROP POLICY IF EXISTS "Users can update own data" ON users;
DROP POLICY IF EXISTS "Employees can view all" ON employees;
DROP POLICY IF EXISTS "Anyone can view departments" ON departments;
-- Add more policy drops as needed

-- ===================================================================
-- STEP 3: Create comprehensive indexes for performance
-- ===================================================================

-- USERS table indexes
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_users_is_online ON users(is_online);
CREATE INDEX IF NOT EXISTS idx_users_role_id ON users(role_id);

-- ROLES table indexes
CREATE INDEX IF NOT EXISTS idx_roles_name ON roles(name);

-- EMPLOYEES table indexes
CREATE INDEX IF NOT EXISTS idx_employees_user_id ON employees(user_id);
CREATE INDEX IF NOT EXISTS idx_employees_department_id ON employees(department_id);
CREATE INDEX IF NOT EXISTS idx_employees_position_id ON positions(id);
CREATE INDEX IF NOT EXISTS idx_employees_is_active ON employees(is_active);
CREATE INDEX IF NOT EXISTS idx_employees_employee_code ON employees(employee_code);
CREATE INDEX IF NOT EXISTS idx_employees_email ON employees(email);

-- DEPARTMENTS table indexes
CREATE INDEX IF NOT EXISTS idx_departments_code ON departments(code);
CREATE INDEX IF NOT EXISTS idx_departments_is_active ON departments(is_active);

-- POSITIONS table indexes
CREATE INDEX IF NOT EXISTS idx_positions_department_id ON positions(department_id);
CREATE INDEX IF NOT EXISTS idx_positions_code ON positions(code);
CREATE INDEX IF NOT EXISTS idx_positions_is_active ON positions(is_active);

-- ATTENDANCES table indexes (CRITICAL FOR PERFORMANCE)
CREATE INDEX IF NOT EXISTS idx_attendances_employee_id ON attendances(employee_id);
CREATE INDEX IF NOT EXISTS idx_attendances_date ON attendances(date);
CREATE INDEX IF NOT EXISTS idx_attendances_status ON attendances(status);
-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_attendances_employee_date ON attendances(employee_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_attendances_date_status ON attendances(date, status);

-- LEAVE REQUESTS table indexes (CRITICAL)
CREATE INDEX IF NOT EXISTS idx_leave_requests_employee_id ON leave_requests(employee_id);
CREATE INDEX IF NOT EXISTS idx_leave_requests_status ON leave_requests(status);
CREATE INDEX IF NOT EXISTS idx_leave_requests_start_date ON leave_requests(start_date);
CREATE INDEX IF NOT EXISTS idx_leave_requests_end_date ON leave_requests(end_date);

-- LEAVE BALANCES indexes
CREATE INDEX IF NOT EXISTS idx_leave_balances_employee_year ON leave_balances(employee_id, year);

-- TASKS table indexes (CRITICAL)
CREATE INDEX IF NOT EXISTS idx_tasks_assigned_to_id ON tasks(assigned_to_id);
CREATE INDEX IF NOT EXISTS idx_tasks_created_by_id ON tasks(created_by_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date);
CREATE INDEX IF NOT EXISTS idx_tasks_assigned_status ON tasks(assigned_to_id, status);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);

-- CHAT MESSAGES indexes (HIGH TRAFFIC)
CREATE INDEX IF NOT EXISTS idx_chat_messages_sender_id ON chat_messages(sender_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_receiver_id ON chat_messages(receiver_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_group_id ON chat_messages(group_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_messages_conversation ON chat_messages(sender_id, receiver_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_messages_group_time ON chat_messages(group_id, created_at DESC);

-- EMAIL MESSAGES indexes
CREATE INDEX IF NOT EXISTS idx_email_messages_sender_id ON email_messages(sender_id);
CREATE INDEX IF NOT EXISTS idx_email_messages_created_at ON email_messages(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_email_messages_category ON email_messages(category);

-- EMAIL RECIPIENTS indexes
CREATE INDEX IF NOT EXISTS idx_email_recipients_recipient_id ON email_recipients(recipient_id);
CREATE INDEX IF NOT EXISTS idx_email_recipients_email_id ON email_recipients(email_id);

-- MEETINGS indexes
CREATE INDEX IF NOT EXISTS idx_meetings_organizer_id ON meetings(organizer_id);
CREATE INDEX IF NOT EXISTS idx_meetings_start_time ON meetings(start_time);
CREATE INDEX IF NOT EXISTS idx_meetings_status ON meetings(status);

-- MEETING PARTICIPANTS indexes
CREATE INDEX IF NOT EXISTS idx_meeting_participants_meeting_id ON meeting_participants(meeting_id);
CREATE INDEX IF NOT EXISTS idx_meeting_participants_user_id ON meeting_participants(user_id);

-- APP NOTIFICATIONS indexes
CREATE INDEX IF NOT EXISTS idx_app_notifications_user_id ON app_notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_app_notifications_is_read ON app_notifications(is_read);
CREATE INDEX IF NOT EXISTS idx_app_notifications_user_read ON app_notifications(user_id, is_read);
CREATE INDEX IF NOT EXISTS idx_app_notifications_created_at ON app_notifications(created_at DESC);

-- PROJECTS indexes
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);

-- PRODUCTS indexes
CREATE INDEX IF NOT EXISTS idx_products_category_id ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku);

-- TRANSACTIONS indexes
CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(transaction_type);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(transaction_date);
CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category);
CREATE INDEX IF NOT EXISTS idx_transactions_status ON transactions(status);
CREATE INDEX IF NOT EXISTS idx_transactions_type_date ON transactions(transaction_type, transaction_date);

-- TIMESHEETS indexes
CREATE INDEX IF NOT EXISTS idx_timesheets_employee_id ON timesheets(employee_id);
CREATE INDEX IF NOT EXISTS idx_timesheets_week ON timesheets(week_start, week_end);
CREATE INDEX IF NOT EXISTS idx_timesheets_status ON timesheets(status);

-- CRM LEADS indexes
CREATE INDEX IF NOT EXISTS idx_crm_leads_status ON crm_leads(status);
CREATE INDEX IF NOT EXISTS idx_crm_leads_assigned ON crm_leads(assigned_to_id);

-- ===================================================================
-- STEP 4: Create optimized functions for common queries
-- ===================================================================

-- Function to get all employees with relationships (replaces N+1 queries)
CREATE OR REPLACE FUNCTION get_employees_with_details()
RETURNS TABLE (
    id INTEGER,
    employee_code VARCHAR(20),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    email VARCHAR(100),
    phone VARCHAR(20),
    is_active BOOLEAN,
    department_name VARCHAR(100),
    department_code VARCHAR(20),
    position_title VARCHAR(100),
    position_code VARCHAR(20)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        e.id,
        e.employee_code,
        e.first_name,
        e.last_name,
        e.email,
        e.phone,
        e.is_active,
        d.name as department_name,
        d.code as department_code,
        p.title as position_title,
        p.code as position_code
    FROM employees e
    LEFT JOIN departments d ON e.department_id = d.id
    LEFT JOIN positions p ON e.position_id = p.id
    ORDER BY e.first_name, e.last_name;
END;
$$ LANGUAGE plpgsql;

-- Function to get dashboard stats in a single call
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
        (SELECT COUNT(*) FROM users WHERE status = 'active')::BIGINT as active_users,
        (SELECT COUNT(*) FROM employees)::BIGINT as total_employees,
        (SELECT COUNT(*) FROM employees WHERE is_active = true)::BIGINT as active_employees,
        (SELECT COUNT(*) FROM departments WHERE is_active = true)::BIGINT as departments_count,
        (SELECT COUNT(*) FROM positions WHERE is_active = true)::BIGINT as positions_count,
        (SELECT COUNT(*) FROM attendances WHERE date = current_date AND status = 'present')::BIGINT as present_today,
        (SELECT COUNT(*) FROM attendances WHERE date = current_date AND status = 'absent')::BIGINT as absent_today,
        (SELECT COUNT(*) FROM leave_requests WHERE status = 'approved' AND start_date <= current_date AND end_date >= current_date)::BIGINT as on_leave_today,
        (SELECT COUNT(*) FROM leave_requests WHERE status = 'pending')::BIGINT as pending_leaves,
        (SELECT COUNT(*) FROM tasks WHERE status = 'todo')::BIGINT as pending_tasks,
        (SELECT COUNT(*) FROM tasks WHERE status = 'in_progress')::BIGINT as in_progress_tasks,
        (SELECT COUNT(*) FROM tasks WHERE status = 'completed')::BIGINT as completed_tasks;
END;
$$ LANGUAGE plpgsql;

-- Function to get today's attendance summary
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
        (SELECT COUNT(*) FROM attendances WHERE date = current_date AND status = 'present')::BIGINT as present_count,
        (SELECT COUNT(*) FROM attendances WHERE date = current_date AND status = 'absent')::BIGINT as absent_count,
        (SELECT COUNT(*) FROM attendances WHERE date = current_date AND status = 'late')::BIGINT as late_count,
        (SELECT COUNT(*) FROM leave_requests WHERE status = 'approved' AND start_date <= current_date AND end_date >= current_date)::BIGINT as on_leave_count,
        (SELECT COUNT(*) FROM attendances WHERE date = current_date AND status = 'half_day')::BIGINT as half_day_count;
END;
$$ LANGUAGE plpgsql;

-- Function to get user with employee details
CREATE OR REPLACE FUNCTION get_user_employee_details(p_user_id INTEGER)
RETURNS TABLE (
    user_id INTEGER,
    username VARCHAR(50),
    email VARCHAR(100),
    role_name VARCHAR(50),
    employee_id INTEGER,
    employee_code VARCHAR(20),
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    department_name VARCHAR(100),
    position_title VARCHAR(100)
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        u.id as user_id,
        u.username,
        u.email,
        r.name as role_name,
        e.id as employee_id,
        e.employee_code,
        e.first_name,
        e.last_name,
        d.name as department_name,
        p.title as position_title
    FROM users u
    LEFT JOIN roles r ON u.role_id = r.id
    LEFT JOIN employees e ON u.id = e.user_id
    LEFT JOIN departments d ON e.department_id = d.id
    LEFT JOIN positions p ON e.position_id = p.id
    WHERE u.id = p_user_id;
END;
$$ LANGUAGE plpgsql;

-- ===================================================================
-- STEP 5: Remove materialized view (not essential for performance)
-- We'll use PostgreSQL functions instead
-- ===================================================================

-- Note: Materialized view removed - using functions instead

-- ===================================================================
-- STEP 6: Update comment
-- ===================================================================

COMMENT ON FUNCTION get_employees_with_details() IS 'Returns all employees with their department and position details in a single query';
COMMENT ON FUNCTION get_dashboard_statistics() IS 'Returns all dashboard statistics in a single call for maximum performance';
COMMENT ON FUNCTION get_today_attendance_summary() IS 'Returns today attendance summary with counts';
COMMENT ON FUNCTION get_user_employee_details(INTEGER) IS 'Returns user details along with employee information';

COMMIT;

-- ===================================================================
-- Verification
-- ===================================================================
SELECT 'Performance optimization migration completed successfully!' as status;

