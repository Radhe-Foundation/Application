-- Migration: Add recipient targeting to announcements
-- Date: 2024

-- Add columns for recipient targeting to announcements table
ALTER TABLE announcements ADD COLUMN IF NOT EXISTS target_audience VARCHAR(50) DEFAULT 'all';
ALTER TABLE announcements ADD COLUMN IF NOT EXISTS target_department_id INTEGER REFERENCES departments(id);
ALTER TABLE announcements ADD COLUMN IF NOT EXISTS target_employee_ids TEXT;

-- Create index for faster queries
CREATE INDEX IF NOT EXISTS idx_announcements_target_audience ON announcements(target_audience);
CREATE INDEX IF NOT EXISTS idx_announcements_target_department ON announcements(target_department_id);

