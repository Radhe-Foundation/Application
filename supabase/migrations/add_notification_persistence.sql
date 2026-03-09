-- Add Notification Persistence to Database
-- This enables notifications to be saved and retrieved across sessions

-- Create notifications table
CREATE TABLE IF NOT EXISTS notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    type VARCHAR(50) DEFAULT 'info', -- info, success, warning, error, etc.
    priority VARCHAR(20) DEFAULT 'medium', -- low, medium, high, urgent
    is_read BOOLEAN DEFAULT FALSE,
    related_entity_type VARCHAR(100),
    related_entity_id INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    read_at TIMESTAMP WITH TIME ZONE
);

-- Add index for faster queries
CREATE INDEX IF NOT EXISTS idx_notifications_user_id ON notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_user_unread ON notifications(user_id, is_read) WHERE is_read = FALSE;
CREATE INDEX IF NOT EXISTS idx_notifications_created_at ON notifications(created_at DESC);

-- Create notification settings table
CREATE TABLE IF NOT EXISTS notification_settings (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    sound_enabled BOOLEAN DEFAULT TRUE,
    badge_enabled BOOLEAN DEFAULT TRUE,
    toast_duration INTEGER DEFAULT 3, -- seconds
    show_unread_count BOOLEAN DEFAULT TRUE,
    banner_enabled BOOLEAN DEFAULT TRUE,
    banner_duration INTEGER DEFAULT 5, -- seconds
    email_notifications BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Add index
CREATE INDEX IF NOT EXISTS idx_notification_settings_user_id ON notification_settings(user_id);

-- Add function to update notification settings timestamp
CREATE OR REPLACE FUNCTION update_notification_settings_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to update timestamp
CREATE TRIGGER trigger_update_notification_settings
    BEFORE UPDATE ON notification_settings
    FOR EACH ROW
    EXECUTE FUNCTION update_notification_settings_timestamp();

-- Create function to save notification to database
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

-- Create function to mark all notifications as read for user
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

-- Create function to get unread notification count
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

-- Create function to delete old notifications
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

-- Insert default notification settings for existing users (will be created on first login)
-- This is a placeholder - actual settings will be created when user logs in

COMMENT ON TABLE notifications IS 'Stores user notifications for persistence across sessions';
COMMENT ON TABLE notification_settings IS 'User notification preferences and settings';

