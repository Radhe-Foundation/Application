#!/usr/bin/env python3
"""
Add RLS policies for Supabase Storage
"""
import psycopg2
import os
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')

print("Connecting to database...")
conn = psycopg2.connect(DATABASE_URL)
conn.autocommit = True
cursor = conn.cursor()

# Add RLS policies for storage
sql = """
-- Allow authenticated users to upload
DROP POLICY IF EXISTS "Allow authenticated uploads" ON storage.objects;
CREATE POLICY "Allow authenticated uploads" ON storage.objects
FOR INSERT WITH CHECK (bucket_id = 'RadheFoundation-files' AND auth.role() = 'authenticated');

-- Allow public read access
DROP POLICY IF EXISTS "Allow public read" ON storage.objects;
CREATE POLICY "Allow public read" ON storage.objects
FOR SELECT USING (bucket_id = 'RadheFoundation-files');
"""

print("Adding RLS policies...")
try:
    cursor.execute(sql)
    print("Policies created successfully!")
except Exception as e:
    print(f"Error: {e}")

cursor.close()
conn.close()
print("Done!")
