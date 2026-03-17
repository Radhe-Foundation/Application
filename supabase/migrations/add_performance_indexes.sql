-- Performance Indexes for RadheFoundation HR Application
-- Run this in Supabase SQL Editor to improve query performance
-- This will significantly reduce the 831ms response time

-- ============================================
-- User and Authentication Indexes
-- ============================================
CREATE INDEX IF NOT EXISTS idx_users_username ON users(username);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_users_status ON users(status);
CREATE INDEX IF NOT EXISTS idx_users_is_online ON users(is_online);

-- ============================================
-- Employee Indexes
-- ============================================
CREATE INDEX IF NOT EXISTS idx_employees_user_id ON employees(user_id);
CREATE INDEX IF NOT EXISTS idx_employees_department_id ON employees(department_id);
CREATE INDEX IF NOT EXISTS idx_employees_position_id ON employees(position_id);
CREATE INDEX IF NOT EXISTS idx_employees_is_active ON employees(is_active);
CREATE INDEX IF NOT EXISTS idx_employees_employee_code ON employees(employee_code);

-- ============================================
-- Attendance Indexes
-- ============================================
CREATE INDEX IF NOT EXISTS idx_attendance_employee_id ON attendance(employee_id);
CREATE INDEX IF NOT EXISTS idx_attendance_date ON attendance(date);
CREATE INDEX IF NOT EXISTS idx_attendance_status ON attendance(status);
CREATE INDEX IF NOT EXISTS idx_attendance_employee_date ON attendance(employee_id, date);

-- ============================================
-- Leave Request Indexes
-- ============================================
CREATE INDEX IF NOT EXISTS idx_leave_requests_employee_id ON leave_requests(employee_id);
CREATE INDEX IF NOT EXISTS idx_leave_requests_status ON leave_requests(status);
CREATE INDEX IF NOT EXISTS idx_leave_requests_start_date ON leave_requests(start_date);
CREATE INDEX IF NOT EXISTS idx_leave_requests_end_date ON leave_requests(end_date);
CREATE INDEX IF NOT EXISTS idx_leave_requests_status_dates ON leave_requests(status, start_date, end_date);

-- ============================================
-- Leave Balance Indexes
-- ============================================
CREATE INDEX IF NOT EXISTS idx_leave_balances_employee_year ON leave_balances(employee_id, year);

-- ============================================
-- Task Indexes
-- ============================================
CREATE INDEX IF NOT EXISTS idx_tasks_assigned_to_id ON tasks(assigned_to_id);
CREATE INDEX IF NOT EXISTS idx_tasks_created_by_id ON tasks(created_by_id);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_due_date ON tasks(due_date);
CREATE INDEX IF NOT EXISTS idx_tasks_user_status ON tasks(assigned_to_id, status);

-- ============================================
-- Chat Message Indexes
-- ============================================
CREATE INDEX IF NOT EXISTS idx_chat_messages_sender_id ON chat_messages(sender_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_receiver_id ON chat_messages(receiver_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_group_id ON chat_messages(group_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON chat_messages(created_at);
CREATE INDEX IF NOT EXISTS idx_chat_messages_conversation ON chat_messages(sender_id, receiver_id, created_at);
CREATE INDEX IF NOT EXISTS idx_chat_messages_group ON chat_messages(group_id, created_at);

-- ============================================
-- Chat Group Member Indexes
-- ============================================
CREATE INDEX IF NOT EXISTS idx_chat_group_members_group_id ON chat_group_members(group_id);
CREATE INDEX IF NOT EXISTS idx_chat_group_members_user_id ON chat_group_members(user_id);

-- ============================================
-- Email Indexes
-- ============================================
CREATE INDEX IF NOT EXISTS idx_email_messages_sender_id ON email_messages(sender_id);
CREATE INDEX IF NOT EXISTS idx_email_messages_created_at ON email_messages(created_at);
CREATE INDEX IF NOT EXISTS idx_email_recipients_recipient_id ON email_recipients(recipient_id);
CREATE INDEX IF NOT EXISTS idx_email_recipients_email_id ON email_recipients(email_id);

-- ============================================
-- Meeting Indexes
-- ============================================
CREATE INDEX IF NOT EXISTS idx_meetings_organizer_id ON meetings(organizer_id);
CREATE INDEX IF NOT EXISTS idx_meetings_start_time ON meetings(start_time);
CREATE INDEX IF NOT EXISTS idx_meeting_participants_user_id ON meeting_participants(user_id);
CREATE INDEX IF NOT EXISTS idx_meeting_participants_meeting_id ON meeting_participants(meeting_id);

-- ============================================
-- Document Indexes
-- ============================================
CREATE INDEX IF NOT EXISTS idx_documents_uploaded_by ON documents(uploaded_by);
CREATE INDEX IF NOT EXISTS idx_documents_category ON documents(category);
CREATE INDEX IF NOT EXISTS idx_documents_group_id ON documents(group_id);

-- ============================================
-- Audit Log Indexes
-- ============================================
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX IF NOT EXISTS idx_audit_logs_user_time ON audit_logs(user_id, created_at);

-- ============================================
-- Notification Indexes
-- ============================================
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON app_notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON app_notifications(is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_user_read ON app_notifications(user_id, is_read);

-- ============================================
-- Timesheet Indexes
-- ============================================
CREATE INDEX IF NOT EXISTS idx_timesheets_employee_id ON timesheets(employee_id);
CREATE INDEX IF NOT EXISTS idx_timesheets_week_start ON timesheets(week_start);
CREATE INDEX IF NOT EXISTS idx_timesheets_employee_week ON timesheets(employee_id, week_start);
CREATE INDEX IF NOT EXISTS idx_time_entries_timesheet_id ON time_entries(timesheet_id);
CREATE INDEX IF NOT EXISTS idx_time_entries_project_id ON time_entries(project_id);

-- ============================================
-- Project Indexes
-- ============================================
CREATE INDEX IF NOT EXISTS idx_projects_status ON projects(status);

-- ============================================
-- Inventory Indexes
-- ============================================
CREATE INDEX IF NOT EXISTS idx_products_category_id ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_products_sku ON products(sku);
CREATE INDEX IF NOT EXISTS idx_inventory_transactions_product_id ON inventory_transactions(product_id);

-- ============================================
-- Billing Indexes
-- ============================================
CREATE INDEX IF NOT EXISTS idx_billing_requests_employee_id ON billing_requests(employee_id);
CREATE INDEX IF NOT EXISTS idx_billing_requests_status ON billing_requests(status);
CREATE INDEX IF NOT EXISTS idx_billing_requests_request_number ON billing_requests(request_number);

-- ============================================
-- Message (Direct Messages) Indexes
-- ============================================
CREATE INDEX IF NOT EXISTS idx_messages_sender_id ON messages(sender_id);
CREATE INDEX IF NOT EXISTS idx_messages_receiver_id ON messages(receiver_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);

-- ============================================
-- Transaction Attachment Indexes
-- ============================================
CREATE INDEX IF NOT EXISTS idx_transaction_attachments_transaction_id ON transaction_attachments(transaction_id);

-- Show confirmation
SELECT 'Performance indexes created successfully!' as status;

