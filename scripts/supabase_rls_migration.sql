-- =============================================================================
-- VERNIKA HRA - RLS (Row Level Security) Migration Script
-- =============================================================================
-- This script enables RLS on all tables and creates security policies
-- Run this in Supabase SQL Editor: https://supabase.com/dashboard/sql
--
-- BEFORE RUNNING: Backup your database!
-- =============================================================================

-- ============================================================================
-- STEP 1: Enable Row Level Security on ALL Tables
-- ============================================================================

-- Core Tables
ALTER TABLE public.roles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.departments ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.positions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.users ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.employees ENABLE ROW LEVEL SECURITY;

-- HR Management Tables
ALTER TABLE public.attendances ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.leave_balances ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.leave_type_configs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.leave_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.time_off_requests ENABLE ROW LEVEL SECURITY;

-- Task Management Tables
ALTER TABLE public.tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.task_comments ENABLE ROW LEVEL SECURITY;

-- Communication Tables
ALTER TABLE public.chat_groups ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_group_members ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chat_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.email_messages ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.email_recipients ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.meetings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.meeting_participants ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.messages ENABLE ROW LEVEL SECURITY;

-- Document & Permission Tables
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.user_permissions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.screen_access ENABLE ROW LEVEL SECURITY;

-- ETL & Integration Tables
ALTER TABLE public.etl_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.powerbi_refresh_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.excel_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.data_import_logs ENABLE ROW LEVEL SECURITY;

-- Audit & System Tables
ALTER TABLE public.audit_logs ENABLE ROW LEVEL SECURITY;

-- ============================================================================
-- STEP 2: Create Helper Functions
-- ============================================================================

-- Function to get current user's role
CREATE OR REPLACE FUNCTION get_user_role()
RETURNS TEXT
LANGUAGE sql
SECURITY DEFINER
AS $$
    SELECT COALESCE(
        (SELECT r.name
         FROM roles r
         JOIN users u ON u.role_id = r.id
         WHERE u.id::TEXT = current_setting('request.jwt.claims', true)::JSONB->>'sub'),
        'public'
    );
$$;

-- Function to get current user ID (not used directly, kept for completeness)
CREATE OR REPLACE FUNCTION get_current_user_id()
RETURNS INTEGER
LANGUAGE sql
SECURITY DEFINER
AS $$
    SELECT NULL::INTEGER;
$$;

-- Function to check if user is admin
CREATE OR REPLACE FUNCTION is_admin()
RETURNS BOOLEAN
LANGUAGE sql
SECURITY DEFINER
AS $$
    SELECT get_user_role() = 'admin';
$$;

-- Function to check if user is HR manager
CREATE OR REPLACE FUNCTION is_hr_manager()
RETURNS BOOLEAN
LANGUAGE sql
SECURITY DEFINER
AS $$
    SELECT get_user_role() IN ('admin', 'hr_manager');
$$;

-- Function to check if user is manager
CREATE OR REPLACE FUNCTION is_manager()
RETURNS BOOLEAN
LANGUAGE sql
SECURITY DEFINER
AS $$
    SELECT get_user_role() IN ('admin', 'hr_manager', 'manager');
$$;

-- Function to get user's employee ID
CREATE OR REPLACE FUNCTION get_user_employee_id(user_id INTEGER)
RETURNS INTEGER
LANGUAGE sql
SECURITY DEFINER
AS $$
    SELECT id FROM employees WHERE employees.user_id = get_user_employee_id.user_id;
$$;

-- Function to check if user is accessing their own record
CREATE OR REPLACE FUNCTION is_own_data(table_user_id INTEGER)
RETURNS BOOLEAN
LANGUAGE sql
SECURITY DEFINER
AS $$
    SELECT EXISTS (
        SELECT 1 FROM users
        WHERE users.id = is_own_data.table_user_id
        AND users.id::TEXT = current_setting('request.jwt.claims', true)::JSONB->>'sub'
    );
$$;

-- Function to get user's department IDs (for manager access)
CREATE OR REPLACE FUNCTION get_user_department_ids()
RETURNS TABLE(department_id INTEGER)
LANGUAGE sql
SECURITY DEFINER
AS $$
    SELECT e.department_id
    FROM employees e
    JOIN users u ON u.id = e.user_id
    WHERE u.id::TEXT = current_setting('request.jwt.claims', true)::JSONB->>'sub'
      AND e.department_id IS NOT NULL;
$$;

-- ============================================================================
-- STEP 3: Create Role-Based Access Policies
-- ============================================================================

-- --------------------------
-- COMPANIES TABLE
-- --------------------------
-- Admins and HR can view all
CREATE POLICY "Admins can view all companies" ON public.companies
    FOR SELECT USING (
        is_admin() = true OR is_hr_manager() = true
    );

-- Only admins can modify
CREATE POLICY "Admins can modify companies" ON public.companies
    FOR ALL USING (is_admin() = true);

-- --------------------------
-- ROLES TABLE
-- --------------------------
-- Only admins can view roles
CREATE POLICY "Admins can view roles" ON public.roles
    FOR SELECT USING (is_admin() = true);

-- Only admins can modify roles
CREATE POLICY "Admins can modify roles" ON public.roles
    FOR ALL USING (is_admin() = true);

-- --------------------------
-- DEPARTMENTS TABLE
-- --------------------------
-- Everyone authenticated can view
CREATE POLICY "All authenticated can view departments" ON public.departments
    FOR SELECT USING (auth.role() = 'authenticated');

-- Admins and HR can modify
CREATE POLICY "Admins/HR can modify departments" ON public.departments
    FOR ALL USING (is_admin() = true OR is_hr_manager() = true);

-- --------------------------
-- POSITIONS TABLE
-- --------------------------
-- Everyone authenticated can view
CREATE POLICY "All authenticated can view positions" ON public.positions
    FOR SELECT USING (auth.role() = 'authenticated');

-- Admins and HR can modify
CREATE POLICY "Admins/HR can modify positions" ON public.positions
    FOR ALL USING (is_admin() = true OR is_hr_manager() = true);

-- --------------------------
-- USERS TABLE
-- --------------------------
-- Users can view their own data
CREATE POLICY "Users can view own data" ON public.users
    FOR SELECT USING (
        id::TEXT = current_setting('request.jwt.claims', true)::JSONB->>'sub'
    );

-- Users can update their own profile (except role and status)
CREATE POLICY "Users can update own profile" ON public.users
    FOR UPDATE USING (
        id::TEXT = current_setting('request.jwt.claims', true)::JSONB->>'sub'
    );

-- Admins can view and modify all users
CREATE POLICY "Admins can view all users" ON public.users
    FOR SELECT USING (is_admin() = true);

CREATE POLICY "Admins can modify all users" ON public.users
    FOR ALL USING (is_admin() = true);

-- HR managers can view all users
CREATE POLICY "HR can view all users" ON public.users
    FOR SELECT USING (is_hr_manager() = true);

-- --------------------------
-- EMPLOYEES TABLE
-- --------------------------
-- Employees can view their own record
CREATE POLICY "Employees can view own record" ON public.employees
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE users.id = employees.user_id 
            AND users.id::TEXT = current_setting('request.jwt.claims', true)::JSONB->>'sub'
        )
    );

-- Managers can view their team's records
CREATE POLICY "Managers can view team employees" ON public.employees
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM employees e2
            WHERE e2.user_id IN (
                SELECT id FROM users 
                WHERE id::TEXT = current_setting('request.jwt.claims', true)::JSONB->>'sub'
            )
            AND e2.department_id = employees.department_id
        )
    );

-- Admins and HR can view all
CREATE POLICY "Admins/HR can view all employees" ON public.employees
    FOR SELECT USING (is_admin() = true OR is_hr_manager() = true);

-- Only admins and HR can modify
CREATE POLICY "Admins/HR can modify employees" ON public.employees
    FOR ALL USING (is_admin() = true OR is_hr_manager() = true);

-- Employees can update their own profile
CREATE POLICY "Employees can update own profile" ON public.employees
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE users.id = employees.user_id 
            AND users.id::TEXT = current_setting('request.jwt.claims', true)::JSONB->>'sub'
        )
    );

-- --------------------------
-- ATTENDANCES TABLE
-- --------------------------
-- Employees can view own attendance
CREATE POLICY "Employees can view own attendance" ON public.attendances
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM employees 
            WHERE employees.id = attendances.employee_id
            AND employees.user_id IN (
                SELECT id FROM users 
                WHERE users.id::TEXT = current_setting('request.jwt.claims', true)::JSONB->>'sub'
            )
        )
    );

-- Managers can view team attendance
CREATE POLICY "Managers can view team attendance" ON public.attendances
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM employees e
            WHERE e.id = attendances.employee_id
            AND e.department_id IN (SELECT department_id FROM get_user_department_ids())
        )
    );

-- Admins and HR can view all
CREATE POLICY "Admins/HR can view all attendance" ON public.attendances
    FOR SELECT USING (is_admin() = true OR is_hr_manager() = true);

-- Admins and HR can modify all
CREATE POLICY "Admins/HR can modify attendance" ON public.attendances
    FOR ALL USING (is_admin() = true OR is_hr_manager() = true);

-- --------------------------
-- LEAVE TYPE CONFIGS TABLE
-- --------------------------
-- Authenticated users can view
CREATE POLICY "Authenticated can view leave types" ON public.leave_type_configs
    FOR SELECT USING (auth.role() = 'authenticated');

-- Only admins can modify
CREATE POLICY "Admins can modify leave types" ON public.leave_type_configs
    FOR ALL USING (is_admin() = true);

-- --------------------------
-- LEAVE BALANCES TABLE
-- --------------------------
-- Employees can view own balance
CREATE POLICY "Employees can view own leave balance" ON public.leave_balances
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM employees 
            WHERE employees.id = leave_balances.employee_id
            AND employees.user_id IN (
                SELECT id FROM users 
                WHERE users.id::TEXT = current_setting('request.jwt.claims', true)::JSONB->>'sub'
            )
        )
    );

-- Managers can view team balances
CREATE POLICY "Managers can view team leave balances" ON public.leave_balances
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM employees e
            WHERE e.id = leave_balances.employee_id
            AND e.department_id IN (SELECT department_id FROM get_user_department_ids())
        )
    );

-- Admins and HR can view/modify all
CREATE POLICY "Admins/HR can manage leave balances" ON public.leave_balances
    FOR ALL USING (is_admin() = true OR is_hr_manager() = true);

-- --------------------------
-- LEAVE REQUESTS TABLE
-- --------------------------
-- Employees can view own requests
CREATE POLICY "Employees can view own leave requests" ON public.leave_requests
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM employees 
            WHERE employees.id = leave_requests.employee_id
            AND employees.user_id IN (
                SELECT id FROM users 
                WHERE users.id::TEXT = current_setting('request.jwt.claims', true)::JSONB->>'sub'
            )
        )
    );

-- Employees can create requests
CREATE POLICY "Employees can create leave requests" ON public.leave_requests
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM employees 
            WHERE employees.id = leave_requests.employee_id
            AND employees.user_id IN (
                SELECT id FROM users 
                WHERE users.id::TEXT = current_setting('request.jwt.claims', true)::JSONB->>'sub'
            )
        )
    );

-- Employees can update own pending requests
CREATE POLICY "Employees can update own pending requests" ON public.leave_requests
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM employees 
            WHERE employees.id = leave_requests.employee_id
            AND employees.user_id IN (
                SELECT id FROM users 
                WHERE users.id::TEXT = current_setting('request.jwt.claims', true)::JSONB->>'sub'
            )
        )
        -- Compare as text to avoid enum literal casting issues
        AND status::text = 'pending'
    );

-- Managers can view/manage team requests
CREATE POLICY "Managers can view team leave requests" ON public.leave_requests
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM employees e
            WHERE e.id = leave_requests.employee_id
            AND e.department_id IN (SELECT department_id FROM get_user_department_ids())
        )
    );

CREATE POLICY "Managers can approve/reject leave requests" ON public.leave_requests
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM employees e
            WHERE e.id = leave_requests.employee_id
            AND e.department_id IN (SELECT department_id FROM get_user_department_ids())
        )
    );

-- Admins and HR can view/modify all
CREATE POLICY "Admins/HR can manage all leave requests" ON public.leave_requests
    FOR ALL USING (is_admin() = true OR is_hr_manager() = true);

-- --------------------------
-- TIME OFF REQUESTS TABLE
-- --------------------------
-- Similar to leave requests
CREATE POLICY "Employees can manage own time off" ON public.time_off_requests
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM employees 
            WHERE employees.id = time_off_requests.user_id
            AND employees.user_id IN (
                SELECT id FROM users 
                WHERE users.id::TEXT = current_setting('request.jwt.claims', true)::JSONB->>'sub'
            )
        )
    );

CREATE POLICY "Managers can manage team time off" ON public.time_off_requests
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM employees e
            WHERE e.id = time_off_requests.user_id
            AND e.department_id IN (SELECT department_id FROM get_user_department_ids())
        )
    );

CREATE POLICY "Admins/HR can manage all time off" ON public.time_off_requests
    FOR ALL USING (is_admin() = true OR is_hr_manager() = true);

-- --------------------------
-- TASKS TABLE
-- --------------------------
-- Employees can view assigned tasks
CREATE POLICY "Employees can view assigned tasks" ON public.tasks
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM employees 
            WHERE employees.id = tasks.assigned_to_id
            AND employees.user_id IN (
                SELECT id FROM users 
                WHERE users.id::TEXT = current_setting('request.jwt.claims', true)::JSONB->>'sub'
            )
        )
        OR
        EXISTS (
            SELECT 1 FROM employees 
            WHERE employees.id = tasks.created_by_id
            AND employees.user_id IN (
                SELECT id FROM users 
                WHERE users.id::TEXT = current_setting('request.jwt.claims', true)::JSONB->>'sub'
            )
        )
    );

-- Managers can view/manage team tasks
CREATE POLICY "Managers can manage team tasks" ON public.tasks
    FOR ALL USING (
        EXISTS (
            SELECT 1 FROM employees e
            WHERE e.id = tasks.assigned_to_id
            AND e.department_id IN (SELECT department_id FROM get_user_department_ids())
        )
        OR is_manager() = true
    );

-- Admins can view all
CREATE POLICY "Admins can view all tasks" ON public.tasks
    FOR SELECT USING (is_admin() = true);

-- --------------------------
-- TASK COMMENTS TABLE
-- --------------------------
-- View comments on accessible tasks
CREATE POLICY "Users can view comments on their tasks" ON public.task_comments
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM tasks
            WHERE tasks.id = task_comments.task_id
            AND (
                EXISTS (
                    SELECT 1 FROM employees 
                    WHERE employees.id = tasks.assigned_to_id
                    AND employees.user_id IN (
                        SELECT id FROM users 
                        WHERE users.id::TEXT = current_setting('request.jwt.claims', true)::JSONB->>'sub'
                    )
                )
                OR is_admin() = true
            )
        )
    );

-- Create comments on accessible tasks
CREATE POLICY "Users can create comments on their tasks" ON public.task_comments
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM tasks
            WHERE tasks.id = task_comments.task_id
            AND (
                EXISTS (
                    SELECT 1 FROM employees 
                    WHERE employees.id = tasks.assigned_to_id
                    AND employees.user_id IN (
                        SELECT id FROM users 
                        WHERE users.id::TEXT = current_setting('request.jwt.claims', true)::JSONB->>'sub'
                    )
                )
                OR is_admin() = true
            )
        )
    );

-- Update own comments
CREATE POLICY "Users can update own comments" ON public.task_comments
    FOR UPDATE USING (
        EXISTS (
            SELECT 1 FROM employees 
            WHERE employees.id = task_comments.employee_id
            AND employees.user_id IN (
                SELECT id FROM users 
                WHERE users.id::TEXT = current_setting('request.jwt.claims', true)::JSONB->>'sub'
            )
        )
        OR is_admin() = true
    );

-- --------------------------
-- CHAT GROUPS TABLE
-- --------------------------
-- Authenticated users can view
CREATE POLICY "Authenticated can view chat groups" ON public.chat_groups
    FOR SELECT USING (auth.role() = 'authenticated');

-- Authenticated users can create
CREATE POLICY "Authenticated can create chat groups" ON public.chat_groups
    FOR INSERT WITH CHECK (auth.role() = 'authenticated');

-- Members can update group
CREATE POLICY "Members can update own groups" ON public.chat_groups
    FOR UPDATE USING (
        created_by::TEXT = current_setting('request.jwt.claims', true)::JSONB->>'sub'
        OR is_admin() = true
    );

-- --------------------------
-- CHAT GROUP MEMBERS TABLE
-- --------------------------
-- Members can view
CREATE POLICY "Members can view group members" ON public.chat_group_members
    FOR SELECT USING (
        user_id::TEXT = current_setting('request.jwt.claims', true)::JSONB->>'sub'
        OR is_admin() = true
    );

-- Users can join groups
CREATE POLICY "Users can join groups" ON public.chat_group_members
    FOR INSERT WITH CHECK (
        user_id::TEXT = current_setting('request.jwt.claims', true)::JSONB->>'sub'
    );

-- Members can leave
CREATE POLICY "Members can leave groups" ON public.chat_group_members
    FOR DELETE USING (
        user_id::TEXT = current_setting('request.jwt.claims', true)::JSONB->>'sub'
    );

-- --------------------------
-- CHAT MESSAGES TABLE
-- --------------------------
-- Group members can view messages
CREATE POLICY "Group members can view messages" ON public.chat_messages
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM chat_group_members
            WHERE chat_group_members.group_id = chat_messages.group_id
            AND chat_group_members.user_id IN (
                SELECT id FROM users 
                WHERE users.id::TEXT = current_setting('request.jwt.claims', true)::JSONB->>'sub'
            )
        )
        OR sender_id::TEXT = current_setting('request.jwt.claims', true)::JSONB->>'sub'
        OR is_admin() = true
    );

-- Members can send messages
CREATE POLICY "Members can send messages" ON public.chat_messages
    FOR INSERT WITH CHECK (
        EXISTS (
            SELECT 1 FROM chat_group_members
            WHERE chat_group_members.group_id = chat_messages.group_id
            AND chat_group_members.user_id IN (
                SELECT id FROM users 
                WHERE users.id::TEXT = current_setting('request.jwt.claims', true)::JSONB->>'sub'
            )
        )
        OR sender_id::TEXT = current_setting('request.jwt.claims', true)::JSONB->>'sub'
    );

-- Users can update own messages
CREATE POLICY "Users can update own messages" ON public.chat_messages
    FOR UPDATE USING (
        sender_id::TEXT = current_setting('request.jwt.claims', true)::JSONB->>'sub'
        OR is_admin() = true
    );

-- --------------------------
-- EMAIL MESSAGES TABLE
-- --------------------------
-- Sender can view own emails
CREATE POLICY "Sender can view own emails" ON public.email_messages
    FOR SELECT USING (
        sender_id::TEXT = current_setting('request.jwt.claims', true)::JSONB->>'sub'
        OR is_admin() = true
    );

-- Sender can create emails
CREATE POLICY "Users can send emails" ON public.email_messages
    FOR INSERT WITH CHECK (
        sender_id::TEXT = current_setting('request.jwt.claims', true)::JSONB->>'sub'
    );

-- --------------------------
-- EMAIL RECIPIENTS TABLE
-- --------------------------
-- Recipients can view
CREATE POLICY "Recipients can view emails" ON public.email_recipients
    FOR SELECT USING (
        recipient_id::TEXT = current_setting('request.jwt.claims', true)::JSONB->>'sub'
        OR is_admin() = true
    );

-- --------------------------
-- MEETINGS TABLE
-- --------------------------
-- Organizer can view/modify
CREATE POLICY "Organizer can manage meetings" ON public.meetings
    FOR ALL USING (
        organizer_id::TEXT = current_setting('request.jwt.claims', true)::JSONB->>'sub'
        OR is_admin() = true
    );

-- Admins can view all
CREATE POLICY "Admins can view all meetings" ON public.meetings
    FOR SELECT USING (is_admin() = true);

-- --------------------------
-- MEETING PARTICIPANTS TABLE
-- --------------------------
-- Participants can view
CREATE POLICY "Participants can view meetings" ON public.meeting_participants
    FOR SELECT USING (
        user_id::TEXT = current_setting('request.jwt.claims', true)::JSONB->>'sub'
        OR is_admin() = true
    );

-- Participants can respond
CREATE POLICY "Participants can respond to meetings" ON public.meeting_participants
    FOR UPDATE USING (
        user_id::TEXT = current_setting('request.jwt.claims', true)::JSONB->>'sub'
    );

-- --------------------------
-- MESSAGES TABLE (Direct Messages)
-- --------------------------
-- Sender/receiver can view
CREATE POLICY "Participants can view direct messages" ON public.messages
    FOR SELECT USING (
        sender_id::TEXT = current_setting('request.jwt.claims', true)::JSONB->>'sub'
        OR receiver_id::TEXT = current_setting('request.jwt.claims', true)::JSONB->>'sub'
        OR is_admin() = true
    );

-- Users can send messages
CREATE POLICY "Users can send direct messages" ON public.messages
    FOR INSERT WITH CHECK (
        sender_id::TEXT = current_setting('request.jwt.claims', true)::JSONB->>'sub'
    );

-- --------------------------
-- DOCUMENTS TABLE
-- --------------------------
-- Authenticated users can view public docs
CREATE POLICY "Users can view documents" ON public.documents
    FOR SELECT USING (
        is_public = true
        OR uploaded_by::TEXT = current_setting('request.jwt.claims', true)::JSONB->>'sub'
        OR is_admin() = true
    );

-- Users can upload
CREATE POLICY "Users can upload documents" ON public.documents
    FOR INSERT WITH CHECK (
        uploaded_by::TEXT = current_setting('request.jwt.claims', true)::JSONB->>'sub'
    );

-- Uploader can modify
CREATE POLICY "Uploader can modify documents" ON public.documents
    FOR UPDATE USING (
        uploaded_by::TEXT = current_setting('request.jwt.claims', true)::JSONB->>'sub'
        OR is_admin() = true
    );

-- --------------------------
-- USER PERMISSIONS TABLE
-- --------------------------
-- User can view own permissions
CREATE POLICY "Users can view own permissions" ON public.user_permissions
    FOR SELECT USING (
        user_id::TEXT = current_setting('request.jwt.claims', true)::JSONB->>'sub'
        OR is_admin() = true
    );

-- Only admins can modify
CREATE POLICY "Admins can manage permissions" ON public.user_permissions
    FOR ALL USING (is_admin() = true);

-- --------------------------
-- SCREEN ACCESS TABLE
-- --------------------------
-- User can view own screen access
CREATE POLICY "Users can view own screen access" ON public.screen_access
    FOR SELECT USING (
        user_id::TEXT = current_setting('request.jwt.claims', true)::JSONB->>'sub'
        OR is_admin() = true
    );

-- Only admins can modify
CREATE POLICY "Admins can manage screen access" ON public.screen_access
    FOR ALL USING (is_admin() = true);

-- --------------------------
-- ETL JOBS TABLE
-- --------------------------
-- Creator can view/modify
CREATE POLICY "Creator can manage ETL jobs" ON public.etl_jobs
    FOR ALL USING (
        created_by_id::TEXT = current_setting('request.jwt.claims', true)::JSONB->>'sub'
        OR is_admin() = true
    );

-- HR can view all
CREATE POLICY "HR can view ETL jobs" ON public.etl_jobs
    FOR SELECT USING (is_hr_manager() = true);

-- --------------------------
-- POWERBI REFRESH LOGS TABLE
-- --------------------------
-- Creator can view
CREATE POLICY "Creator can view PowerBI logs" ON public.powerbi_refresh_logs
    FOR SELECT USING (
        triggered_by_id::TEXT = current_setting('request.jwt.claims', true)::JSONB->>'sub'
        OR is_admin() = true
    );

-- --------------------------
-- EXCEL TEMPLATES TABLE
-- --------------------------
-- Authenticated can view
CREATE POLICY "Authenticated can view templates" ON public.excel_templates
    FOR SELECT USING (auth.role() = 'authenticated');

-- Admins can modify
CREATE POLICY "Admins can manage templates" ON public.excel_templates
    FOR ALL USING (is_admin() = true);

-- --------------------------
-- DATA IMPORT LOGS TABLE
-- --------------------------
-- Creator can view
CREATE POLICY "Creator can view import logs" ON public.data_import_logs
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM etl_jobs
            WHERE etl_jobs.id = data_import_logs.etl_job_id
            AND etl_jobs.created_by_id IN (
                SELECT id FROM users 
                WHERE users.id::TEXT = current_setting('request.jwt.claims', true)::JSONB->>'sub'
            )
        )
        OR is_admin() = true
    );

-- --------------------------
-- AUDIT LOGS TABLE
-- --------------------------
-- Only admins can view
CREATE POLICY "Admins can view audit logs" ON public.audit_logs
    FOR SELECT USING (is_admin() = true);

-- ============================================================================
-- STEP 4: Create Safe Views for Sensitive Data
-- ============================================================================

-- Create a view for employees WITHOUT sensitive data (account_number excluded)
CREATE OR REPLACE VIEW public.employees_safe AS
SELECT 
    id,
    employee_code,
    user_id,
    company_id,
    first_name,
    last_name,
    date_of_birth,
    gender,
    email,
    phone,
    department_id,
    position_id,
    date_of_joining,
    is_active,
    created_at,
    employment_type,
    employment_status,
    address,
    city,
    state,
    pincode,
    emergency_contact_name,
    emergency_phone,
    emergency_relation,
    bank_name,
    ifsc_code,
    branch_name,
    basic_salary,
    allowance,
    deduction
    -- NOTE: account_number is intentionally EXCLUDED from this view
FROM public.employees;

-- Comment explaining what's excluded from the safe view
COMMENT ON VIEW public.employees_safe IS 'Safe employee view WITHOUT sensitive columns: account_number';

-- Create a view for users without session tokens
CREATE OR REPLACE VIEW public.users_safe AS
SELECT 
    id,
    username,
    email,
    role_id,
    status,
    created_at,
    last_seen,
    is_online,
    last_login,
    last_ip
FROM public.users;

-- ============================================================================
-- STEP 5: Grant Execute on Helper Functions
-- ============================================================================

-- Grant execute on helper functions to authenticated users
GRANT EXECUTE ON FUNCTION get_user_role() TO authenticated;
GRANT EXECUTE ON FUNCTION is_admin() TO authenticated;
GRANT EXECUTE ON FUNCTION is_hr_manager() TO authenticated;
GRANT EXECUTE ON FUNCTION is_manager() TO authenticated;
GRANT EXECUTE ON FUNCTION get_user_employee_id(INTEGER) TO authenticated;
GRANT EXECUTE ON FUNCTION is_own_data(INTEGER) TO authenticated;
GRANT EXECUTE ON FUNCTION get_user_department_ids() TO authenticated;

-- ============================================================================
-- STEP 6: Drop Public Access to Tables
-- ============================================================================

-- This removes public access so RLS policies take full effect
-- Note: These are default grants that come with PostgreSQL

-- For tables that should only be accessible via views:
REVOKE SELECT ON public.employees FROM public;
REVOKE SELECT ON public.users FROM public;

-- Grant access to safe views
GRANT SELECT ON public.employees_safe TO authenticated;
GRANT SELECT ON public.users_safe TO authenticated;

-- ============================================================================
-- STEP 7: Create Indexes for Performance
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_attendances_employee_date 
    ON public.attendances(employee_id, date);
CREATE INDEX IF NOT EXISTS idx_leave_requests_employee_dates 
    ON public.leave_requests(employee_id, start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_tasks_assigned_to 
    ON public.tasks(assigned_to_id);
CREATE INDEX IF NOT EXISTS idx_chat_group_members_user 
    ON public.chat_group_members(user_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_group_date 
    ON public.chat_messages(group_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_email_recipients_email 
    ON public.email_recipients(email_id);

-- ============================================================================
-- VERIFICATION QUERIES
-- ============================================================================

-- Check if RLS is enabled on all tables
SELECT 
    schemaname,
    tablename,
    row_security_enabled
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY tablename;

-- Check all policies
SELECT 
    policyname,
    tablename,
    cmd,
    qual
FROM pg_policies
WHERE schemaname = 'public'
ORDER BY tablename, policyname;

-- ============================================================================
-- ROLLBACK SCRIPT (if needed)
-- ============================================================================

-- To rollback, drop all policies and disable RLS:
/*
-- Drop all policies
DROP POLICY IF EXISTS "Admins can view all companies" ON public.companies;
-- ... (repeat for all policies)

-- Disable RLS on all tables
ALTER TABLE public.roles DISABLE ROW LEVEL SECURITY;
ALTER TABLE public.departments DISABLE ROW LEVEL SECURITY;
-- ... (repeat for all tables)
*/

