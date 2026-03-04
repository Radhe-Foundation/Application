-- Add attachment fields to email_messages table
-- Run this migration to enable email attachments

ALTER TABLE email_messages 
ADD COLUMN IF NOT EXISTS has_attachment BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS attachment_path VARCHAR(500),
ADD COLUMN IF NOT EXISTS attachment_name VARCHAR(255);

COMMENT ON COLUMN email_messages.has_attachment IS 'Whether the email has an attachment';
COMMENT ON COLUMN email_messages.attachment_path IS 'Supabase Storage URL for the attachment';
COMMENT ON COLUMN email_messages.attachment_name IS 'Original filename of the attachment';
