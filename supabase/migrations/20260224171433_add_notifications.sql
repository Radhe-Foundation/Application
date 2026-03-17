-- RadheFoundation HRA - Notifications Database Migration
-- Run this SQL in your Supabase SQL Editor to enable notifications

-- ==================== NOTIFICATION TABLES ====================

-- Create notification types enum
DO $$ BEGIN
    CREATE TYPE notification_type AS ENUM (
        'leave_request', 'leave_approved', 'leave_rejected',
        'task_assigned', 'task_updated', 'chat_message',
        'email_received', 'meeting_invite', 'announcement', 'system'
    );
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create notification priority enum
DO $$ BEGIN
    CREATE TYPE notification_priority AS ENUM ('low', 'medium', 'high', 'urgent');
EXCEPTION
    WHEN duplicate_object THEN null;
END $$;

-- Create notifications table
CREATE TABLE IF NOT EXISTS app_notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    sender_id INTEGER REFERENCES users(id),
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    notification_type notification_type NOT NULL,
    priority notification_priority DEFAULT 'medium',
    related_entity_type VARCHAR(50),
    related_entity_id INTEGER,
    is_read BOOLEAN DEFAULT FALSE,
    read_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON app_notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_is_read ON app_notifications(is_read);
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON app_notifications(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_notifications_type ON app_notifications(notification_type);
CREATE INDEX IF NOT EXISTS idx_notifications_priority ON app_notifications(priority);

-- Enable Row Level Security (RLS)
ALTER TABLE app_notifications ENABLE ROW LEVEL SECURITY;

-- RLS Policy: Allow all access (simplified for RadheFoundation since we handle auth in app)
-- For production, you'd want to implement proper user-based policies
CREATE POLICY "Allow all access to notifications" ON app_notifications
    FOR ALL USING (true) WITH CHECK (true);

-- Add foreign key for sender_id (with different approach to avoid issues)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'app_notifications_sender_id_fkey'
    ) THEN
        ALTER TABLE app_notifications 
        ADD CONSTRAINT app_notifications_sender_id_fkey 
        FOREIGN KEY (sender_id) REFERENCES users(id) ON DELETE SET NULL;
    END IF;
END $$;

-- Insert sample notification for testing (optional)
-- INSERT INTO app_notifications (user_id, title, message, notification_type, priority)
-- SELECT id, 'Welcome to RadheFoundation!', 'Your account is now active. Start exploring the features.', 'system', 'medium'
-- FROM users WHERE username = 'admin' LIMIT 1;

-- Function to get unread notification count for a user
CREATE OR REPLACE FUNCTION get_unread_notification_count(p_user_id INTEGER)
RETURNS INTEGER AS $$
DECLARE
    v_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_count
    FROM app_notifications
    WHERE user_id = p_user_id AND is_read = FALSE;
    RETURN v_count;
END;
$$ LANGUAGE plpgsql;

-- Function to mark all notifications as read for a user
CREATE OR REPLACE FUNCTION mark_all_notifications_read(p_user_id INTEGER)
RETURNS VOID AS $$
BEGIN
    UPDATE app_notifications
    SET is_read = TRUE, read_at = CURRENT_TIMESTAMP
    WHERE user_id = p_user_id AND is_read = FALSE;
END;
$$ LANGUAGE plpgsql;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION get_unread_notification_count TO PUBLIC;
GRANT EXECUTE ON FUNCTION mark_all_notifications_read TO PUBLIC;

-- ==================== CHAT FILE SHARING ENHANCEMENTS ====================

-- Add attachment columns to chat_messages if they don't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'chat_messages' AND column_name = 'has_attachment'
    ) THEN
        ALTER TABLE chat_messages ADD COLUMN has_attachment BOOLEAN DEFAULT FALSE;
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'chat_messages' AND column_name = 'attachment_path'
    ) THEN
        ALTER TABLE chat_messages ADD COLUMN attachment_path VARCHAR(500);
    END IF;
END $$;

-- ==================== EMAIL ATTACHMENTS ====================

-- Add attachment columns to email_messages if they don't exist
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'email_messages' AND column_name = 'has_attachment'
    ) THEN
        ALTER TABLE email_messages ADD COLUMN has_attachment BOOLEAN DEFAULT FALSE;
    END IF;
    
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'email_messages' AND column_name = 'attachment_path'
    ) THEN
        ALTER TABLE email_messages ADD COLUMN attachment_path VARCHAR(500);
    END IF;
END $$;

-- Print success message
DO $$ 
BEGIN
    RAISE NOTICE 'Notifications migration completed successfully!';
END $$;

