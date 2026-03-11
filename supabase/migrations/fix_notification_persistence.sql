-- Fix Notification Persistence - handles existing functions
-- Run this if add_notification_persistence.sql failed

-- Drop existing functions if they exist (with correct signature)
DROP FUNCTION IF EXISTS save_notification(INTEGER, VARCHAR, TEXT, VARCHAR, VARCHAR, VARCHAR, INTEGER);
DROP FUNCTION IF EXISTS mark_notification_read(INTEGER, INTEGER);
DROP FUNCTION IF EXISTS mark_all_notifications_read(INTEGER);
DROP FUNCTION IF EXISTS get_unread_notification_count(INTEGER);
DROP FUNCTION IF EXISTS get_user_notifications(INTEGER, INTEGER, INTEGER, BOOLEAN);
DROP FUNCTION IF EXISTS cleanup_old_notifications(INTEGER, INTEGER);

-- Drop existing tables if needed (optional - only if you want fresh start)
-- DROP TABLE IF EXISTS notifications CASCADE;
-- DROP TABLE IF EXISTS notification_settings CASCADE;

-- Create notifications table if not exists
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    type VARCHAR(50) DEFAULT 'info',
    priority VARCHAR(20) DEFAULT 'medium',
    is_read BOOLEAN DEFAULT FALSE,
    related_entity_type VARCHAR(100),
    related_entity_id INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP WITH TIME ZONE
);

-- Add indexes
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user_unread ON notifications(user_id, is_read) WHERE is_read = FALSE;
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at DESC);

-- Create notification settings table
CREATE TABLE IF NOT EXISTS notification_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    sound_enabled BOOLEAN DEFAULT TRUE,
    badge_enabled BOOLEAN DEFAULT TRUE,
    toast_duration INTEGER DEFAULT 3,
    show_unread_count BOOLEAN DEFAULT TRUE,
    banner_enabled BOOLEAN DEFAULT TRUE,
    banner_duration INTEGER DEFAULT 5,
    email_notifications BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_notification_settings_user_id ON notification_settings(user_id);

-- Create function to save notification
CREATE OR REPLACE FUNCTION save_notification(
    p_user_id INTEGER,
    p_title VARCHAR,
    p_message TEXT,
    p_type VARCHAR DEFAULT 'info',
    p_priority VARCHAR DEFAULT 'medium',
    p_related_entity_type VARCHAR DEFAULT NULL,
    p_related_entity_id INTEGER DEFAULT NULL
)
RETURNS INTEGER AS $$
DECLARE
    v_notification_id INTEGER;
BEGIN
    INSERT INTO notifications (
        user_id, title, message, type, priority, 
        related_entity_type, related_entity_id
    ) VALUES (
        p_user_id, p_title, p_message, p_type, p_priority,
        p_related_entity_type, p_related_entity_id
    )
    RETURNING id INTO v_notification_id;
    
    RETURN v_notification_id;
END;
$$ LANGUAGE plpgsql;

-- Create function to mark notification as read
CREATE OR REPLACE FUNCTION mark_notification_read(
    p_notification_id INTEGER,
    p_user_id INTEGER
)
RETURNS BOOLEAN AS $$
BEGIN
    UPDATE notifications 
    SET is_read = TRUE, read_at = CURRENT_TIMESTAMP
    WHERE id = p_notification_id AND user_id = p_user_id;
    
    RETURN FOUND;
END;
$$ LANGUAGE plpgsql;

-- Create function to mark all notifications as read
CREATE OR REPLACE FUNCTION mark_all_notifications_read(p_user_id INTEGER)
RETURNS INTEGER AS $$
DECLARE
    v_count INTEGER;
BEGIN
    UPDATE notifications 
    SET is_read = TRUE, read_at = CURRENT_TIMESTAMP
    WHERE user_id = p_user_id AND is_read = FALSE;
    
    GET DIAGNOSTICS v_count = ROW_COUNT;
    RETURN v_count;
END;
$$ LANGUAGE plpgsql;

-- Create function to get unread count
CREATE OR REPLACE FUNCTION get_unread_notification_count(p_user_id INTEGER)
RETURNS INTEGER AS $$
DECLARE
    v_count INTEGER;
BEGIN
    SELECT COUNT(*) INTO v_count
    FROM notifications
    WHERE user_id = p_user_id AND is_read = FALSE;
    
    RETURN v_count;
END;
$$ LANGUAGE plpgsql;

-- Create function to get user notifications
CREATE OR REPLACE FUNCTION get_user_notifications(
    p_user_id INTEGER,
    p_limit INTEGER DEFAULT 50,
    p_offset INTEGER DEFAULT 0,
    p_include_read BOOLEAN DEFAULT TRUE
)
RETURNS TABLE (
    id INTEGER,
    title VARCHAR,
    message TEXT,
    type VARCHAR,
    priority VARCHAR,
    is_read BOOLEAN,
    related_entity_type VARCHAR,
    related_entity_id INTEGER,
    created_at TIMESTAMP WITH TIME ZONE,
    read_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        n.id, n.title, n.message, n.type, n.priority,
        n.is_read, n.related_entity_type, n.related_entity_id,
        n.created_at, n.read_at
    FROM notifications n
    WHERE n.user_id = p_user_id
        AND (p_include_read OR n.is_read = FALSE)
    ORDER BY n.created_at DESC
    LIMIT p_limit
    OFFSET p_offset;
END;
$$ LANGUAGE plpgsql;

-- Create function to cleanup old notifications
CREATE OR REPLACE FUNCTION cleanup_old_notifications(
    p_user_id INTEGER DEFAULT NULL,
    p_days_to_keep INTEGER DEFAULT 30
)
RETURNS INTEGER AS $$
DECLARE
    v_count INTEGER;
BEGIN
    DELETE FROM notifications
    WHERE created_at < CURRENT_TIMESTAMP - (p_days_to_keep || ' days')::INTERVAL
        AND (p_user_id IS NULL OR user_id = p_user_id)
        AND is_read = TRUE;
    
    GET DIAGNOSTICS v_count = ROW_COUNT;
    RETURN v_count;
END;
$$ LANGUAGE plpgsql;

-- Grant execute permissions
GRANT EXECUTE ON FUNCTION save_notification TO service_role;
GRANT EXECUTE ON FUNCTION mark_notification_read TO service_role;
GRANT EXECUTE ON FUNCTION mark_all_notifications_read TO service_role;
GRANT EXECUTE ON FUNCTION get_unread_notification_count TO service_role;
GRANT EXECUTE ON FUNCTION get_user_notifications TO service_role;
GRANT EXECUTE ON FUNCTION cleanup_old_notifications TO service_role;

SELECT 'Notification persistence functions created successfully!' as result;

