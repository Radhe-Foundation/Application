-- Migration: Add profile_photo column to employees table
-- Run this script to add profile photo support

ALTER TABLE employees ADD COLUMN profile_photo VARCHAR(500);

-- Verify the column was added
SELECT column_name, data_type, character_maximum_length 
FROM information_schema.columns 
WHERE table_name = 'employees' AND column_name = 'profile_photo';

