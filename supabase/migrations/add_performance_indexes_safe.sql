-- Performance Indexes for Vernika HR Application
-- This script safely creates indexes only for existing tables
-- Run this in Supabase SQL Editor

-- Helper function to create index if table exists
DO $$
DECLARE
    tbl TEXT;
    idx_name TEXT;
    col_name TEXT;
BEGIN
    -- Users table
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'users') THEN
        CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
        CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
        CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
        CREATE INDEX IF NOT EXISTS idx_users_is_online ON users(is_online);
        RAISE NOTICE 'Users indexes created';
    END IF;

    -- Employees table
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'employees') THEN
        CREATE INDEX IF NOT EXISTS idx_employees_user_id ON employees(user_id);
        CREATE INDEX IF NOT EXISTS idx_employees_department_id ON employees(department_id);
        CREATE INDEX IF NOT EXISTS idx_employees_position_id ON employees(position_id);
        CREATE INDEX IF NOT EXISTS idx_employees_is_active ON employees(is_active);
        CREATE INDEX IF NOT EXISTS idx_employees_employee_code ON employees(employee_code);
        RAISE NOTICE 'Employees indexes created';
    END IF;

    -- Attendance table (note: might be 'attendance' or 'attendances')
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'attendance') THEN
        CREATE INDEX IF NOT EXISTS idx_attendance_employee_id ON attendance(employee_id);
        CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date);
        CREATE INDEX IF NOT EXISTS idx_attendance_status ON attendance(status);
        CREATE INDEX IF NOT EXISTS idx_attendance_employee_date ON attendance(employee_id, date);
        RAISE NOTICE 'Attendance indexes created';
    END IF;

    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'attendances') THEN
        CREATE INDEX IF NOT EXISTS idx_attendances_employee_id ON attendances(employee_id);
        CREATE INDEX IF NOT EXISTS idx_attendances_date ON attendances(date);
        CREATE INDEX IF NOT EXISTS idx_attendances_status ON attendances(status);
        CREATE INDEX IF NOT EXISTS idx_attendances_employee_date ON attendances(employee_id, date);
        RAISE NOTICE 'Attendances indexes created';
    END IF;

    -- Leave requests
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'leave_requests') THEN
        CREATE INDEX IF NOT EXISTS idx_leave_requests_employee_id ON leave_requests(employee_id);
        CREATE INDEX IF NOT EXISTS idx_leave_requests_status ON leave_requests(status);
        CREATE INDEX IF NOT EXISTS idx_leave_requests_start_date ON leave_requests(start_date);
        CREATE INDEX IF NOT EXISTS idx_leave_requests_end_date ON leave_requests(end_date);
        CREATE INDEX IF NOT EXISTS idx_leave_requests_status_dates ON leave_requests(status, start_date, end_date);
        RAISE NOTICE 'Leave requests indexes created';
    END IF;

    -- Leave balances
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'leave_balances') THEN
        CREATE INDEX IF NOT EXISTS idx_leave_balances_employee_year ON leave_balances(employee_id, year);
        RAISE NOTICE 'Leave balances indexes created';
    END IF;

    -- Tasks
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'tasks') THEN
        CREATE INDEX IF NOT EXISTS idx_tasks_assigned_to_id ON tasks(assigned_to_id);
        CREATE INDEX IF NOT EXISTS idx_tasks_created_by_id ON tasks(created_by_id);
        CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
        CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date);
        CREATE INDEX IF NOT EXISTS idx_tasks_user_status ON tasks(assigned_to_id, status);
        RAISE NOTICE 'Tasks indexes created';
    END IF;

    -- Chat messages
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'chat_messages') THEN
        CREATE INDEX IF NOT EXISTS idx_chat_messages_sender_id ON chat_messages(sender_id);
        CREATE INDEX IF NOT EXISTS idx_chat_messages_receiver_id ON chat_messages(receiver_id);
        CREATE INDEX IF NOT EXISTS idx_chat_messages_group_id ON chat_messages(group_id);
        CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at);
        CREATE INDEX IF NOT EXISTS idx_chat_messages_conversation ON chat_messages(sender_id, receiver_id, created_at);
        CREATE INDEX IF NOT EXISTS idx_chat_messages_group ON chat_messages(group_id, created_at);
        RAISE NOTICE 'Chat messages indexes created';
    END IF;

    -- Chat group members
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'chat_group_members') THEN
        CREATE INDEX IF NOT EXISTS idx_chat_group_members_group_id ON chat_group_members(group_id);
        CREATE INDEX IF NOT EXISTS idx_chat_group_members_user_id ON chat_group_members(user_id);
        RAISE NOTICE 'Chat group members indexes created';
    END IF;

    -- Email messages
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'email_messages') THEN
        CREATE INDEX IF NOT EXISTS idx_email_messages_sender_id ON email_messages(sender_id);
        CREATE INDEX IF NOT EXISTS idx_email_messages_created_at ON email_messages(created_at);
        RAISE NOTICE 'Email messages indexes created';
    END IF;

    -- Email recipients
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'email_recipients') THEN
        CREATE INDEX IF NOT EXISTS idx_email_recipients_recipient_id ON email_recipients(recipient_id);
        CREATE INDEX IF NOT EXISTS idx_email_recipients_email_id ON email_recipients(email_id);
        RAISE NOTICE 'Email recipients indexes created';
    END IF;

    -- Meetings
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'meetings') THEN
        CREATE INDEX IF NOT EXISTS idx_meetings_organizer_id ON meetings(organizer_id);
        CREATE INDEX IF NOT EXISTS idx_meetings_start_time ON meetings(start_time);
        RAISE NOTICE 'Meetings indexes created';
    END IF;

    -- Meeting participants
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'meeting_participants') THEN
        CREATE INDEX IF NOT EXISTS idx_meeting_participants_user_id ON meeting_participants(user_id);
        CREATE INDEX IF NOT EXISTS idx_meeting_participants_meeting_id ON meeting_participants(meeting_id);
        RAISE NOTICE 'Meeting participants indexes created';
    END IF;

    -- Documents
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'documents') THEN
        CREATE INDEX IF NOT EXISTS idx_documents_uploaded_by ON documents(uploaded_by);
        CREATE INDEX IF NOT EXISTS idx_documents_category ON documents(category);
        RAISE NOTICE 'Documents indexes created';
    END IF;

    -- Audit logs
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'audit_logs') THEN
        CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
        CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);
        CREATE INDEX IF NOT EXISTS idx_audit_logs_user_time ON audit_logs(user_id, created_at);
        RAISE NOTICE 'Audit logs indexes created';
    END IF;

    -- App notifications
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'app_notifications') THEN
        CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON app_notifications(user_id);
        CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON app_notifications(is_read);
        CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON app_notifications(user_id, is_read);
        RAISE NOTICE 'App notifications indexes created';
    END IF;

    -- Timesheets
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'timesheets') THEN
        CREATE INDEX IF NOT EXISTS idx_timesheets_employee_id ON timesheets(employee_id);
        CREATE INDEX IF NOT EXISTS idx_timesheets_week_start ON timesheets(week_start);
        CREATE INDEX IF NOT EXISTS idx_timesheets_employee_week ON timesheets(employee_id, week_start);
        RAISE NOTICE 'Timesheets indexes created';
    END IF;

    -- Time entries
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'time_entries') THEN
        CREATE INDEX IF NOT EXISTS idx_time_entries_timesheet_id ON time_entries(timesheet_id);
        CREATE INDEX IF NOT EXISTS idx_time_entries_project_id ON time_entries(project_id);
        RAISE NOTICE 'Time entries indexes created';
    END IF;

    -- Projects
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'projects') THEN
        CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);
        RAISE NOTICE 'Projects indexes created';
    END IF;

    -- Products
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'products') THEN
        CREATE INDEX IF NOT EXISTS idx_products_category_id ON products(category_id);
        CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku);
        RAISE NOTICE 'Products indexes created';
    END IF;

    -- Inventory transactions
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'inventory_transactions') THEN
        CREATE INDEX IF NOT EXISTS idx_inventory_transactions_product_id ON inventory_transactions(product_id);
        RAISE NOTICE 'Inventory transactions indexes created';
    END IF;

    -- Billing requests
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'billing_requests') THEN
        CREATE INDEX IF NOT EXISTS idx_billing_requests_employee_id ON billing_requests(employee_id);
        CREATE INDEX IF NOT EXISTS idx_billing_requests_status ON billing_requests(status);
        CREATE INDEX IF NOT EXISTS idx_billing_requests_request_number ON billing_requests(request_number);
        RAISE NOTICE 'Billing requests indexes created';
    END IF;

    -- Messages (direct messages)
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'messages') THEN
        CREATE INDEX IF NOT EXISTS idx_messages_sender_id ON messages(sender_id);
        CREATE INDEX IF NOT EXISTS idx_messages_receiver_id ON messages(receiver_id);
        CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);
        RAISE NOTICE 'Messages indexes created';
    END IF;

    -- Transaction attachments
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'transaction_attachments') THEN
        CREATE INDEX IF NOT EXISTS idx_transaction_attachments_transaction_id ON transaction_attachments(transaction_id);
        RAISE NOTICE 'Transaction attachments indexes created';
    END IF;

    -- Call logs
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'call_logs') THEN
        CREATE INDEX IF NOT EXISTS idx_call_logs_caller_id ON call_logs(caller_id);
        CREATE INDEX IF NOT EXISTS idx_call_logs_receiver_id ON call_logs(receiver_id);
        RAISE NOTICE 'Call logs indexes created';
    END IF;

END $$;

-- Show completion message
SELECT 'Performance indexes creation completed! Check notices above for details.' as status;

